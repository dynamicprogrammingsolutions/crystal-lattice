import type { AgentBackend } from '../backend/backend';
import type {
  ActionUiElement,
  ApplicationActionDefinition,
  ApplicationUiElement,
  SessionListFieldElement,
} from '../types/plugins';
import { SimpleSubscribable } from '../util/subscribable';

export interface PluginsResult {
  actionsById: Record<string, ApplicationActionDefinition>;
  sessionActions: ActionUiElement[];
  messageActions: ActionUiElement[];
  sessionListActions: ActionUiElement[];
  sessionListFields: SessionListFieldElement[];
  sessionListPinnedToggles: ActionUiElement[];
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
};

const CACHE: Map<string, CacheEntry | null | undefined> = new Map();

function buildResultFromEntry(entry: CacheEntry | null | undefined): PluginsResult {
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
  const sessionListActions = elements.filter(
    (el) => el && (el as any).ui_type === 'session_list_action',
  ) as ActionUiElement[];
  const sessionListFields = elements.filter(
    (el) => el && (el as any).ui_type === 'session_list_field',
  ) as SessionListFieldElement[];
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

    this.setSnapshot({ ...this.getSnapshot(), loading: true, error: null });

    try {
      const [actions, elements] = await Promise.all([
        this.backend.listApplicationActions(),
        this.backend.listApplicationUiSchema(),
      ]);

      const entry: CacheEntry = {
        actions: Array.isArray(actions) ? actions : [],
        elements: Array.isArray(elements) ? elements : [],
      };
      CACHE.set(this.cacheKey, entry);
      const next = buildResultFromEntry(entry);
      this.setSnapshot({ ...next, loading: false, error: null });
    } catch (err: any) {
      CACHE.set(this.cacheKey, null);
      this.setSnapshot({ ...EMPTY_RESULT, loading: false, error: err?.message || 'Failed to load' });
    }
  }
}
