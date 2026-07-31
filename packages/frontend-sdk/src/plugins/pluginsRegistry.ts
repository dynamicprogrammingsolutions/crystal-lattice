import type { AgentBackend } from '../backend/backend';
import type {
  ActionUiElement,
  ApplicationActionDefinition,
  ApplicationActionUiElement,
  ApplicationUiElement,
  SessionListFieldElement,
} from '../types/plugins';
import type { ApplicationActionDiagnostic } from './applicationActions';
import {
  buildApplicationActionsByKey,
  normalizeApplicationActionElements,
} from './applicationActions';
import { subscribeApplicationActionsInvalidated } from './applicationActionsInvalidation';
import type {
  SessionListActionElement,
  SessionListContractDiagnostic,
} from '../sessions/sessionListContracts';
import type { SessionListFilterSchema } from '../sessions/sessionListFilters';
import {
  normalizeSessionListActionElement,
  normalizeSessionListFieldElement,
} from '../sessions/sessionListContracts';
import {
  normalizeSessionListFilterSchema,
} from '../sessions/sessionListFilters';
import { subscribeServerSettingsInvalidated } from '../serverSettings/serverSettingsInvalidation';
import { SimpleSubscribable } from '../util/subscribable';

export interface PluginsResult {
  actionsById: Record<string, ApplicationActionDefinition>;
  actionsByKey?: Record<string, ApplicationActionDefinition>;
  applicationActions?: ApplicationActionUiElement[];
  applicationActionDiagnostics?: ApplicationActionDiagnostic[];
  sessionActions: ActionUiElement[];
  messageActions: ActionUiElement[];
  sessionListActions: SessionListActionElement[];
  sessionListFields: SessionListFieldElement[];
  sessionListFilterSchema: SessionListFilterSchema;
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

const EMPTY_SESSION_LIST_FILTER_SCHEMA = normalizeSessionListFilterSchema([]);

const EMPTY_RESULT: PluginsResult = {
  actionsById: {},
  actionsByKey: {},
  applicationActions: [],
  applicationActionDiagnostics: [],
  sessionActions: [],
  messageActions: [],
  sessionListActions: [],
  sessionListFields: [],
  sessionListFilterSchema: EMPTY_SESSION_LIST_FILTER_SCHEMA,
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
  const actionsByKey = buildApplicationActionsByKey(entry.actions || []);

  const elements = Array.isArray(entry.elements) ? entry.elements : [];
  const normalizedApplicationActions = normalizeApplicationActionElements({
    elements,
    actionsByKey,
  });
  const sessionActions = elements.filter((el) => el && (el as any).ui_type === 'session_action') as ActionUiElement[];
  const messageActions = elements.filter((el) => el && (el as any).ui_type === 'message_action') as ActionUiElement[];
  const sessionListActions: SessionListActionElement[] = [];
  const sessionListFields: SessionListFieldElement[] = [];
  const rawSessionListFilters: ApplicationUiElement[] = [];
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
      return;
    }
    if (element && (element as any).ui_type === 'session_list_filter') {
      rawSessionListFilters.push(element);
    }
  });
  const sessionListFilterSchema = normalizeSessionListFilterSchema(
    rawSessionListFilters,
  );
  sessionListDiagnostics.push(...sessionListFilterSchema.diagnostics);
  sessionListActions.sort(
    (left, right) => (left.order ?? 0) - (right.order ?? 0),
  );

  return {
    actionsById,
    actionsByKey,
    applicationActions: normalizedApplicationActions.actions,
    applicationActionDiagnostics: normalizedApplicationActions.diagnostics,
    sessionActions,
    messageActions,
    sessionListActions,
    sessionListFields,
    sessionListFilterSchema,
    sessionListDiagnostics,
  };
}

function buildResultFromState(state: PluginsRegistryState): PluginsResult {
  return {
    actionsById: state.actionsById || {},
    actionsByKey: state.actionsByKey || {},
    applicationActions: state.applicationActions || [],
    applicationActionDiagnostics: state.applicationActionDiagnostics || [],
    sessionActions: state.sessionActions || [],
    messageActions: state.messageActions || [],
    sessionListActions: state.sessionListActions || [],
    sessionListFields: state.sessionListFields || [],
    sessionListFilterSchema:
      state.sessionListFilterSchema || EMPTY_SESSION_LIST_FILTER_SCHEMA,
    sessionListDiagnostics: state.sessionListDiagnostics || [],
  };
}

export class PluginsRegistry extends SimpleSubscribable<PluginsRegistryState> {
  private backend: AgentBackend | null;
  private cacheKey: string;
  private unsubscribeServerSettings: (() => void) | null = null;
  private unsubscribeApplicationActions: (() => void) | null = null;

  constructor(options: { backend: AgentBackend | null; cacheKey: string }) {
    super({ ...EMPTY_RESULT, loading: false, error: null });
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;

    const cachedEntry = CACHE.get(this.cacheKey);
    if (cachedEntry !== undefined) {
      const next = buildResultFromEntry(cachedEntry);
      this.setSnapshot({ ...next, loading: false, error: null });
    }

    if (this.backend) {
      this.unsubscribeServerSettings = subscribeServerSettingsInvalidated(
        this.backend,
        () => {
          this.invalidate();
          this.refresh().catch(() => {
            // Errors are stored in registry state.
          });
        },
      );
      this.unsubscribeApplicationActions = subscribeApplicationActionsInvalidated(
        this.backend,
        () => {
          this.invalidate();
          this.refresh().catch(() => {
            // Errors are stored in registry state.
          });
        },
      );
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

  close(): void {
    this.unsubscribeServerSettings?.();
    this.unsubscribeServerSettings = null;
    this.unsubscribeApplicationActions?.();
    this.unsubscribeApplicationActions = null;
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
