import type { AgentBackend } from '../backend/backend';
import type { SdkEvent } from '../runtime/sdkEvent';
import type { SdkEventBus } from '../runtime/sdkEventBus';
import { BusAwareController } from '../runtime/busAwareController';
import { SESSION_MUTATION_EVENT_TYPES } from '../sessionMutations/sessionMutationEventTypes';
import { isEventForSession } from '../sessionMutations/sessionMutationRules';
import type { UiSchemaElement } from '../types/uiSchema';

export interface SessionUiSchemaControllerState {
  loading: boolean;
  error: string | null;
  elements: UiSchemaElement[];
}

const EMPTY_STATE: SessionUiSchemaControllerState = {
  loading: false,
  error: null,
  elements: [],
};

const CACHE: Map<string, UiSchemaElement[] | null | undefined> = new Map();

const UI_SCHEMA_INVALIDATION_EVENT_TYPES: Set<string> = new Set([
  SESSION_MUTATION_EVENT_TYPES.PLUGINS_CHANGED,
  SESSION_MUTATION_EVENT_TYPES.OVERRIDES_CHANGED,
  SESSION_MUTATION_EVENT_TYPES.AGENT_CHANGED,
]);

export class SessionUiSchemaController extends BusAwareController<SessionUiSchemaControllerState> {
  private backend: AgentBackend | null;
  private cacheKey: string;
  private sessionId: string;
  private enabled: boolean;
  private loadInFlight: boolean;
  private needsReload: boolean;

  constructor(options: {
    backend: AgentBackend | null;
    cacheKey: string;
    sessionId: string;
    bus?: SdkEventBus;
    scopeKey?: string;
    enabled?: boolean;
  }) {
    super({
      initialSnapshot: EMPTY_STATE,
      scopeKey: options.scopeKey ?? options.cacheKey,
      bus: options.bus ?? null,
    });
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;
    this.sessionId = options.sessionId;
    this.enabled = options.enabled ?? true;
    this.loadInFlight = false;
    this.needsReload = false;

    this.subscribeToBus((event) => {
      this.handleBusEvent(event);
    });

    const cached = CACHE.get(this.buildCacheKey());
    if (cached !== undefined) {
      this.setSnapshot({ loading: false, error: null, elements: cached || [] });
    }
  }

  private handleBusEvent(event: SdkEvent): void {
    if (!UI_SCHEMA_INVALIDATION_EVENT_TYPES.has(event.type)) {
      return;
    }
    if (!isEventForSession(event, this.scopeKey, this.sessionId)) {
      return;
    }

    this.invalidate();
    if (!this.enabled) {
      return;
    }

    void this.load();
  }

  private buildCacheKey(): string {
    return `${this.cacheKey}::${this.sessionId}`;
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  invalidate(): void {
    CACHE.delete(this.buildCacheKey());
    if (this.loadInFlight) {
      this.needsReload = true;
    }
  }

  /** Update state and cache from a fresh fetch without calling the backend. */
  setElements(elements: UiSchemaElement[]): void {
    const list = Array.isArray(elements) ? elements : [];
    CACHE.set(this.buildCacheKey(), list);
    this.setSnapshot({ loading: false, error: null, elements: list });
  }

  async load(): Promise<void> {
    if (this.loadInFlight) {
      this.needsReload = true;
      return;
    }

    this.loadInFlight = true;
    let forceReload = false;
    try {
      do {
        this.needsReload = false;
        await this.loadOnce({ force: forceReload });
        forceReload = this.needsReload;
      } while (forceReload);
    } finally {
      this.loadInFlight = false;
    }
  }

  private async loadOnce(options: { force: boolean }): Promise<void> {
    if (!this.backend) {
      this.setSnapshot(EMPTY_STATE);
      return;
    }

    const existing = options.force ? undefined : CACHE.get(this.buildCacheKey());
    if (existing !== undefined) {
      this.setSnapshot({ loading: false, error: null, elements: existing || [] });
      return;
    }

    this.setSnapshot({ ...this.getSnapshot(), loading: true, error: null });
    try {
      const els = await this.backend.getSessionUiSchema(this.sessionId);
      const elements = Array.isArray(els) ? els : [];
      CACHE.set(this.buildCacheKey(), elements);
      this.setSnapshot({ loading: false, error: null, elements });
    } catch (err: any) {
      CACHE.set(this.buildCacheKey(), null);
      this.setSnapshot({ loading: false, error: err?.message || 'Failed to load', elements: [] });
    }
  }
}
