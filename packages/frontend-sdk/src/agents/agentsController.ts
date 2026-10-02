import type { AgentBackend } from '../backend/backend';
import type { AgentDescriptor } from '../types/agents';
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

export function invalidateAgentsCache(cacheKey: string): void {
  CACHE.delete(cacheKey);
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
