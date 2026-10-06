import type { AgentBackend } from '../backend/backend';
import type { AgentDescriptor } from '../types/agents';
import type { AgentPluginEntry } from '../types/agentPlugins';
import { normalizeAgentPluginEntries } from '../types/agentPlugins';
import { SimpleSubscribable } from '../util/subscribable';

export interface AgentsControllerState {
  loading: boolean;
  error: string | null;
  agents: string[];
  descriptors: AgentDescriptor[];
}

const EMPTY_STATE: AgentsControllerState = {
  loading: false,
  error: null,
  agents: [],
  descriptors: [],
};

type AgentsCacheEntry = {
  agents: string[];
  descriptors: AgentDescriptor[];
};

const CACHE: Map<string, AgentsCacheEntry | null | undefined> = new Map();
const PLUGINS_CACHE: Map<string, Map<string, AgentPluginEntry[]>> = new Map();
const PLUGINS_IN_FLIGHT: Map<string, Promise<AgentPluginEntry[]>> = new Map();

export function invalidateAgentsCache(cacheKey: string): void {
  CACHE.delete(cacheKey);
  PLUGINS_CACHE.delete(cacheKey);
  for (const key of PLUGINS_IN_FLIGHT.keys()) {
    if (key.startsWith(`${cacheKey}\u0000`)) {
      PLUGINS_IN_FLIGHT.delete(key);
    }
  }
}

export class AgentsController extends SimpleSubscribable<AgentsControllerState> {
  private backend: AgentBackend | null;
  private cacheKey: string;

  constructor(options: { backend: AgentBackend | null; cacheKey: string }) {
    super(EMPTY_STATE);
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;

    const cached = CACHE.get(this.cacheKey);
    if (cached !== undefined) {
      this.setSnapshot({
        loading: false,
        error: null,
        agents: cached?.agents ?? [],
        descriptors: cached?.descriptors ?? [],
      });
    }
  }

  invalidate(): void {
    invalidateAgentsCache(this.cacheKey);
    this.setSnapshot(EMPTY_STATE);
  }

  async load(): Promise<string[]> {
    if (!this.backend) {
      this.setSnapshot({ ...EMPTY_STATE, error: 'No active connection' });
      throw new Error('No active connection');
    }

    const existing = CACHE.get(this.cacheKey);
    if (existing !== undefined) {
      const agents = existing?.agents ?? [];
      this.setSnapshot({
        loading: false,
        error: null,
        agents,
        descriptors: existing?.descriptors ?? [],
      });
      return agents;
    }

    const snapshot = this.getSnapshot();
    if (snapshot.loading) {
      return snapshot.agents;
    }

    this.setSnapshot({ ...snapshot, loading: true, error: null });
    try {
      const rawDescriptors = this.backend.listAgentDescriptors
        ? await this.backend.listAgentDescriptors()
        : [];
      const descriptors = normalizeAgentDescriptors(rawDescriptors);
      const rawAgents =
        descriptors.length > 0
          ? descriptors.map((descriptor) => descriptor.id)
          : await this.backend.listAgents();
      const agents = Array.isArray(rawAgents)
        ? rawAgents.filter(
            (agent): agent is string =>
              typeof agent === 'string' && agent.trim().length > 0,
          )
        : [];
      const effectiveDescriptors =
        descriptors.length > 0
          ? descriptors
          : agents.map((id, index) => ({
              id,
              title: id,
              description: '',
              order: index,
            }));
      const entry = { agents, descriptors: effectiveDescriptors };
      CACHE.set(this.cacheKey, entry);
      this.setSnapshot({
        loading: false,
        error: null,
        agents,
        descriptors: effectiveDescriptors,
      });
      return agents;
    } catch (err: any) {
      CACHE.set(this.cacheKey, null);
      this.setSnapshot({
        loading: false,
        error: err?.message || 'Failed to load agents',
        agents: [],
        descriptors: [],
      });
      throw err;
    }
  }

  async ensureLoaded(): Promise<string[]> {
    const snapshot = this.getSnapshot();
    if (snapshot.agents.length > 0) {
      return snapshot.agents;
    }
    return this.load();
  }

  async ensureDescriptorsLoaded(): Promise<AgentDescriptor[]> {
    const snapshot = this.getSnapshot();
    if (snapshot.descriptors.length > 0) {
      return snapshot.descriptors;
    }
    await this.load();
    return this.getSnapshot().descriptors;
  }

  async ensurePluginsLoaded(agentId: string): Promise<AgentPluginEntry[]> {
    const normalizedAgentId =
      typeof agentId === 'string' ? agentId.trim() : '';
    if (!normalizedAgentId) {
      throw new Error('Agent id is required');
    }
    if (!this.backend) {
      throw new Error('No active connection');
    }
    if (!this.backend.listAgentPlugins) {
      throw new Error(
        'Agent plugin preview is not supported by this connection',
      );
    }

    const cached = PLUGINS_CACHE.get(this.cacheKey)?.get(normalizedAgentId);
    if (cached) {
      return cached;
    }

    const requestKey = `${this.cacheKey}\u0000${normalizedAgentId}`;
    const inFlight = PLUGINS_IN_FLIGHT.get(requestKey);
    if (inFlight) {
      return inFlight;
    }

    const request = this.backend
      .listAgentPlugins(normalizedAgentId)
      .then(raw => {
        const plugins = normalizeAgentPluginEntries(raw);
        let byAgent = PLUGINS_CACHE.get(this.cacheKey);
        if (!byAgent) {
          byAgent = new Map();
          PLUGINS_CACHE.set(this.cacheKey, byAgent);
        }
        byAgent.set(normalizedAgentId, plugins);
        return plugins;
      })
      .finally(() => {
        PLUGINS_IN_FLIGHT.delete(requestKey);
      });
    PLUGINS_IN_FLIGHT.set(requestKey, request);
    return request;
  }
}

export function normalizeAgentDescriptors(
  values: readonly AgentDescriptor[] | null | undefined,
): AgentDescriptor[] {
  if (!Array.isArray(values)) return [];
  return values
    .flatMap((value, index) => {
      if (!value || typeof value !== 'object') return [];
      const id = typeof value.id === 'string' ? value.id.trim() : '';
      if (!id) return [];
      const title =
        typeof value.title === 'string' && value.title.trim()
          ? value.title.trim()
          : id;
      const description =
        typeof value.description === 'string' ? value.description.trim() : '';
      const order =
        typeof value.order === 'number' && Number.isFinite(value.order)
          ? value.order
          : index;
      return [{ id, title, description, order, index }];
    })
    .sort(
      (left, right) =>
        left.order - right.order ||
        left.index - right.index ||
        left.id.localeCompare(right.id),
    )
    .map(({ index: _index, ...descriptor }) => descriptor);
}

export function pickDefaultAgentId(agents: string[]): string | null {
  if (!Array.isArray(agents) || agents.length === 0) return null;
  const first = agents[0];
  return typeof first === 'string' && first.trim() ? first.trim() : null;
}
