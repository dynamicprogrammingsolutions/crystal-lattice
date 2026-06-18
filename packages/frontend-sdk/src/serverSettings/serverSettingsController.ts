import type { AgentBackend } from '../backend/backend';
import type { UiSchemaElement } from '../types/uiSchema';
import { SimpleSubscribable } from '../util/subscribable';
import { coerceValueForElement } from '../utils/uiSchema';

export type ServerSettingsStatusTone = 'idle' | 'busy' | 'success' | 'error';

export interface ServerSettingsControllerState {
  elements: UiSchemaElement[];
  settings: Record<string, any>;
  baseConfig: Record<string, any>;
  loading: boolean;
  refreshing: boolean;
  savingKeys: string[];
  error: string | null;
  statusMessage: string | null;
  statusTone: ServerSettingsStatusTone;
  lastSavedAt: number | null;
  lastLoadedAt: number | null;
}

interface CachedServerSettingsSnapshot {
  elements: UiSchemaElement[];
  settings: Record<string, any>;
  baseConfig: Record<string, any>;
  lastSavedAt: number | null;
  lastLoadedAt: number | null;
}

type BaseState = Omit<ServerSettingsControllerState, 'statusMessage' | 'statusTone'>;

const EMPTY_BASE_STATE: BaseState = {
  elements: [],
  settings: {},
  baseConfig: {},
  loading: false,
  refreshing: false,
  savingKeys: [],
  error: null,
  lastSavedAt: null,
  lastLoadedAt: null,
};

const CACHE_BY_BACKEND: WeakMap<object, Map<string, CachedServerSettingsSnapshot>> = new WeakMap();
const SAVED_STATUS_TIMEOUT_MS = 3000;

function asBackendKey(backend: AgentBackend | null): object | null {
  if (backend && (typeof backend === 'object' || typeof backend === 'function')) {
    return backend as object;
  }
  return null;
}

function getCacheMap(backend: AgentBackend | null): Map<string, CachedServerSettingsSnapshot> | null {
  const backendKey = asBackendKey(backend);
  if (!backendKey) {
    return null;
  }

  let cache = CACHE_BY_BACKEND.get(backendKey);
  if (!cache) {
    cache = new Map<string, CachedServerSettingsSnapshot>();
    CACHE_BY_BACKEND.set(backendKey, cache);
  }
  return cache;
}

function hasOwn(value: unknown, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(value, key);
}

function formatErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message || 'Request failed.';
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'Request failed.';
}

function toError(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  }
  return new Error(formatErrorMessage(error));
}

function filterServerConfigUiSchemaElements(elements: UiSchemaElement[]): UiSchemaElement[] {
  return (Array.isArray(elements) ? elements : []).filter((element) => {
    if (!element || typeof element !== 'object') {
      return false;
    }

    const key = (element as any).key;
    if (typeof key !== 'string' || !key) {
      return false;
    }

    if ((element as any).scope !== 'server') {
      return false;
    }

    const uiType = (element as any).ui_type;
    if (uiType === 'config') {
      return true;
    }

    return uiType === undefined || uiType === null || uiType === '';
  }) as UiSchemaElement[];
}

function findElementByKey(elements: UiSchemaElement[], key: string): UiSchemaElement | undefined {
  return (elements || []).find((el) => el && typeof el === 'object' && (el as any).key === key);
}

function ensureServerSettingsBackend(backend: AgentBackend): Required<Pick<
  AgentBackend,
  'getServerSettings' | 'patchServerSettings' | 'deleteServerSetting' | 'listServerSettingsUiSchema'
>> {
  if (
    typeof backend.getServerSettings !== 'function' ||
    typeof backend.patchServerSettings !== 'function' ||
    typeof backend.deleteServerSetting !== 'function' ||
    typeof backend.listServerSettingsUiSchema !== 'function'
  ) {
    throw new Error('Server settings are not supported by this backend.');
  }
  return backend as Required<Pick<
    AgentBackend,
    'getServerSettings' | 'patchServerSettings' | 'deleteServerSetting' | 'listServerSettingsUiSchema'
  >>;
}

function addSavingKey(keys: string[], key: string): string[] {
  if (keys.includes(key)) {
    return keys;
  }
  return [...keys, key];
}

function removeSavingKey(keys: string[], key: string): string[] {
  if (!keys.includes(key)) {
    return keys;
  }
  return keys.filter((entry) => entry !== key);
}

export class ServerSettingsController extends SimpleSubscribable<ServerSettingsControllerState> {
  private backend: AgentBackend | null;
  private cacheKey: string;
  private requestSeq = 0;
  private loadPromise: Promise<void> | null = null;
  private savedStatusUntil: number | null = null;
  private savedStatusTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(options: { backend: AgentBackend | null; cacheKey: string }) {
    super({ ...EMPTY_BASE_STATE, statusMessage: null, statusTone: 'idle' });
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;

    const cached = this.readCache();
    if (cached) {
      this.commit({
        ...EMPTY_BASE_STATE,
        elements: cached.elements,
        settings: cached.settings,
        baseConfig: cached.baseConfig,
        lastSavedAt: cached.lastSavedAt,
        lastLoadedAt: cached.lastLoadedAt,
      });
    }
  }

  dispose(): void {
    this.clearSavedStatusTimer();
  }

  invalidate(): void {
    const cache = getCacheMap(this.backend);
    cache?.delete(this.buildCacheKey());
    this.requestSeq += 1;
    this.loadPromise = null;
  }

  async load(): Promise<void> {
    if (!this.backend) {
      this.savedStatusUntil = null;
      this.clearSavedStatusTimer();
      this.commit(EMPTY_BASE_STATE);
      return;
    }

    if (this.loadPromise) {
      return this.loadPromise;
    }

    const seq = ++this.requestSeq;
    const current = this.getBaseState();
    const hasSnapshot = current.lastLoadedAt != null;
    this.commit({
      ...current,
      loading: !hasSnapshot,
      refreshing: hasSnapshot,
      error: null,
    });

    const promise = (async () => {
      try {
        const serverSettingsBackend = ensureServerSettingsBackend(this.backend!);
        const [applicationUiSchema, settings] = await Promise.all([
          serverSettingsBackend.listServerSettingsUiSchema(),
          serverSettingsBackend.getServerSettings(),
        ]);

        if (this.requestSeq !== seq) {
          return;
        }

        const next: BaseState = {
          ...this.getBaseState(),
          elements: filterServerConfigUiSchemaElements(
            Array.isArray(applicationUiSchema) ? applicationUiSchema : [],
          ),
          settings: settings && typeof settings === 'object' ? settings : {},
          baseConfig: {},
          loading: false,
          refreshing: false,
          error: null,
          lastLoadedAt: Date.now(),
        };

        this.writeCache(next);
        this.commit(next);
      } catch (error) {
        if (this.requestSeq !== seq) {
          return;
        }

        this.savedStatusUntil = null;
        this.clearSavedStatusTimer();
        this.commit({
          ...this.getBaseState(),
          loading: false,
          refreshing: false,
          error: formatErrorMessage(error),
        });
      } finally {
        if (this.requestSeq === seq) {
          this.loadPromise = null;
        }
      }
    })();

    this.loadPromise = promise;
    return promise;
  }

  async patchSetting(key: string, value: any): Promise<void> {
    if (!this.backend) {
      throw new Error('No active backend.');
    }

    this.requestSeq += 1;
    this.loadPromise = null;
    this.savedStatusUntil = null;
    this.clearSavedStatusTimer();

    const current = this.getBaseState();
    const hadPrevious = hasOwn(current.settings, key);
    const previousValue = hadPrevious ? current.settings[key] : undefined;
    const element = findElementByKey(current.elements, key);
    const coercedValue = element ? coerceValueForElement(element, value) : value;

    const optimistic: BaseState = {
      ...current,
      settings: {
        ...current.settings,
        [key]: coercedValue,
      },
      savingKeys: addSavingKey(current.savingKeys, key),
      error: null,
    };

    this.writeCache(optimistic);
    this.commit(optimistic);

    try {
      await ensureServerSettingsBackend(this.backend).patchServerSettings({ [key]: coercedValue });
      this.markMutationSaved(key);
      this.load().catch(() => {});
    } catch (error) {
      const revertedSettings = { ...this.getBaseState().settings };
      if (hadPrevious) {
        revertedSettings[key] = previousValue;
      } else {
        delete revertedSettings[key];
      }

      this.savedStatusUntil = null;
      this.clearSavedStatusTimer();
      const failed: BaseState = {
        ...this.getBaseState(),
        settings: revertedSettings,
        savingKeys: removeSavingKey(this.getBaseState().savingKeys, key),
        error: formatErrorMessage(error),
      };
      this.writeCache(failed);
      this.commit(failed);
      throw toError(error);
    }
  }

  async deleteSetting(key: string): Promise<void> {
    if (!this.backend) {
      throw new Error('No active backend.');
    }

    this.requestSeq += 1;
    this.loadPromise = null;
    this.savedStatusUntil = null;
    this.clearSavedStatusTimer();

    const current = this.getBaseState();
    const hadPrevious = hasOwn(current.settings, key);
    const previousValue = hadPrevious ? current.settings[key] : undefined;

    const nextSettings = { ...current.settings };
    delete nextSettings[key];

    const optimistic: BaseState = {
      ...current,
      settings: nextSettings,
      savingKeys: addSavingKey(current.savingKeys, key),
      error: null,
    };

    this.writeCache(optimistic);
    this.commit(optimistic);

    try {
      await ensureServerSettingsBackend(this.backend).deleteServerSetting(key);
      this.markMutationSaved(key);
      this.load().catch(() => {});
    } catch (error) {
      const revertedSettings = { ...this.getBaseState().settings };
      if (hadPrevious) {
        revertedSettings[key] = previousValue;
      }

      this.savedStatusUntil = null;
      this.clearSavedStatusTimer();
      const failed: BaseState = {
        ...this.getBaseState(),
        settings: revertedSettings,
        savingKeys: removeSavingKey(this.getBaseState().savingKeys, key),
        error: formatErrorMessage(error),
      };
      this.writeCache(failed);
      this.commit(failed);
      throw toError(error);
    }
  }

  private markMutationSaved(key: string): void {
    const current = this.getBaseState();
    const next: BaseState = {
      ...current,
      savingKeys: removeSavingKey(current.savingKeys, key),
      error: null,
      lastSavedAt: Date.now(),
    };

    this.savedStatusUntil = Date.now() + SAVED_STATUS_TIMEOUT_MS;
    this.scheduleSavedStatusClear();
    this.writeCache(next);
    this.commit(next);
  }

  private scheduleSavedStatusClear(): void {
    this.clearSavedStatusTimer();
    if (!this.savedStatusUntil) {
      return;
    }

    const delay = this.savedStatusUntil - Date.now();
    if (delay <= 0) {
      this.savedStatusUntil = null;
      this.commit(this.getBaseState());
      return;
    }

    this.savedStatusTimer = setTimeout(() => {
      this.savedStatusTimer = null;
      this.savedStatusUntil = null;
      this.commit(this.getBaseState());
    }, delay);
  }

  private clearSavedStatusTimer(): void {
    if (!this.savedStatusTimer) {
      return;
    }
    clearTimeout(this.savedStatusTimer);
    this.savedStatusTimer = null;
  }

  private deriveStatus(base: BaseState): {
    statusMessage: string | null;
    statusTone: ServerSettingsStatusTone;
  } {
    if (base.error) {
      return { statusMessage: base.error, statusTone: 'error' };
    }
    if (base.loading) {
      return { statusMessage: 'Loading settings...', statusTone: 'busy' };
    }
    if (base.savingKeys.length > 0) {
      return { statusMessage: 'Saving...', statusTone: 'busy' };
    }
    if (this.savedStatusUntil && this.savedStatusUntil > Date.now()) {
      return { statusMessage: 'Saved.', statusTone: 'success' };
    }
    if (base.refreshing) {
      return { statusMessage: 'Refreshing settings...', statusTone: 'busy' };
    }
    return { statusMessage: null, statusTone: 'idle' };
  }

  private commit(base: BaseState): void {
    this.setSnapshot({
      ...base,
      ...this.deriveStatus(base),
    });
  }

  private getBaseState(): BaseState {
    const { statusMessage: _statusMessage, statusTone: _statusTone, ...rest } = this.getSnapshot();
    return rest;
  }

  private readCache(): CachedServerSettingsSnapshot | null {
    const cache = getCacheMap(this.backend);
    return cache?.get(this.buildCacheKey()) ?? null;
  }

  private writeCache(state: BaseState): void {
    const cache = getCacheMap(this.backend);
    if (!cache) {
      return;
    }

    cache.set(this.buildCacheKey(), {
      elements: state.elements,
      settings: state.settings,
      baseConfig: state.baseConfig,
      lastSavedAt: state.lastSavedAt,
      lastLoadedAt: state.lastLoadedAt,
    });
  }

  private buildCacheKey(): string {
    return `${this.cacheKey}::server`;
  }
}