import type { AgentBackend } from '../backend/backend';
import type {
  ActionUiElement,
  ApplicationActionDefinition,
  ApplicationUiElement,
  SessionListFieldElement,
} from '../types/plugins';
import type {
  SessionListActionElement,
  SessionListContractDiagnostic,
} from '../sessions/sessionListContracts';
import {
  normalizeSessionListActionElement,
  normalizeSessionListFieldElement,
} from '../sessions/sessionListContracts';
import { SimpleSubscribable } from '../util/subscribable';

export interface PluginsResult {
  actionsById: Record<string, ApplicationActionDefinition>;
  sessionActions: ActionUiElement[];
  messageActions: ActionUiElement[];
  sessionListActions: SessionListActionElement[];
  sessionListFields: SessionListFieldElement[];
  sessionListPinnedToggles: ActionUiElement[];
  sessionListDiagnostics: SessionListContractDiagnostic[];
}

export interface PluginsRegistryState extends PluginsResult {
  loading: boolean;
  error: string | null;
}

interface CacheEntry {
  actions: ApplicationActionDefinition[];
  elements: ApplicationUiElement[];
}

const EMPTY_RESULT: PluginsResult = {
  actionsById: {},
  sessionActions: [],
  messageActions: [],
  sessionListActions: [],
  sessionListFields: [],
  sessionListPinnedToggles: [],
  sessionListDiagnostics: [],
};

const CACHE: Map<string, CacheEntry | undefined> = new Map();

function buildResultFromEntry(entry: CacheEntry | undefined): PluginsResult {
  if (!entry) {
    return EMPTY_RESULT;
  }

  const actionsById: Record<string, ApplicationActionDefinition> = {};
  (entry.actions || []).forEach((a) => {
    if (a && typeof a.id === 'string') {
      actionsById[a.id] = a;
    }
  });

  const elements = Array.isArray(entry.elements) ? entry.elements : [];
  const sessionActions = elements.filter((el) => el && (el as any).ui_type === 'session_action') as ActionUiElement[];
  const messageActions = elements.filter((el) => el && (el as any).ui_type === 'message_action') as ActionUiElement[];
  const sessionListActions: SessionListActionElement[] = [];
  const sessionListFields: SessionListFieldElement[] = [];
  const sessionListDiagnostics: SessionListContractDiagnostic[] = [];
  elements.forEach((element) => {
    if (element && (element as any).ui_type === 'session_list_action') {
      const normalized = normalizeSessionListActionElement(element);
      sessionListDiagnostics.push(...normalized.diagnostics);
      if (normalized.value) {
        sessionListActions.push(normalized.value);
      }
      return;
    }
    if (element && (element as any).ui_type === 'session_list_field') {
      const normalized = normalizeSessionListFieldElement(element);
      sessionListDiagnostics.push(...normalized.diagnostics);
      if (normalized.value) {
        sessionListFields.push(normalized.value);
      }
    }
  });
  const sessionListPinnedToggles = elements.filter(
    (el) => el && (el as any).ui_type === 'session_list_toggle_pinned',
  ) as ActionUiElement[];

  return {
    actionsById,
    sessionActions,
    messageActions,
    sessionListActions,
    sessionListFields,
    sessionListPinnedToggles,
    sessionListDiagnostics,
  };
}

function buildResultFromState(state: PluginsRegistryState): PluginsResult {
  return {
    actionsById: state.actionsById || {},
    sessionActions: state.sessionActions || [],
    messageActions: state.messageActions || [],
    sessionListActions: state.sessionListActions || [],
    sessionListFields: state.sessionListFields || [],
    sessionListPinnedToggles: state.sessionListPinnedToggles || [],
    sessionListDiagnostics: state.sessionListDiagnostics || [],
  };
}

export class PluginsRegistry extends SimpleSubscribable<PluginsRegistryState> {
  private backend: AgentBackend | null;
  private cacheKey: string;

  constructor(options: { backend: AgentBackend | null; cacheKey: string }) {
    super({ ...EMPTY_RESULT, loading: false, error: null });
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;

    const cachedEntry = CACHE.get(this.cacheKey);
    if (cachedEntry !== undefined) {
      const next = buildResultFromEntry(cachedEntry);
      this.setSnapshot({ ...next, loading: false, error: null });
    }
  }

  async load(): Promise<void> {
    if (!this.backend) {
      this.setSnapshot({ ...EMPTY_RESULT, loading: false, error: null });
      return;
    }

    const existing = CACHE.get(this.cacheKey);
    if (existing !== undefined) {
      const next = buildResultFromEntry(existing);
      this.setSnapshot({ ...next, loading: false, error: null });
      return;
    }

    await this.fetch({ preserveExisting: true });
  }

  async refresh(): Promise<void> {
    if (!this.backend) {
      this.setSnapshot({ ...EMPTY_RESULT, loading: false, error: null });
      return;
    }

    await this.fetch({ preserveExisting: true });
  }

  invalidate(): void {
    CACHE.delete(this.cacheKey);
  }

  private async fetch(options: { preserveExisting: boolean }): Promise<void> {
    const current = this.getSnapshot();
    const currentResult = buildResultFromState(current);

    this.setSnapshot({
      ...(options.preserveExisting ? currentResult : EMPTY_RESULT),
      loading: true,
      error: null,
    });

    try {
      const [actions, elements] = await Promise.all([
        this.backend!.listApplicationActions(),
        this.backend!.listApplicationUiSchema(),
      ]);

      const entry: CacheEntry = {
        actions: Array.isArray(actions) ? actions : [],
        elements: Array.isArray(elements) ? elements : [],
      };
      CACHE.set(this.cacheKey, entry);
      const next = buildResultFromEntry(entry);
      this.setSnapshot({ ...next, loading: false, error: null });
    } catch (err: any) {
      this.setSnapshot({
        ...currentResult,
        loading: false,
        error: err?.message || 'Failed to load',
      });
    }
  }
}
