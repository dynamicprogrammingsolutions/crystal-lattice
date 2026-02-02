import type { AgentBackend } from '../backend/backend';
import { SimpleSubscribable } from '../util/subscribable';

export interface AgentsControllerState {
  loading: boolean;
  error: string | null;
  agents: string[];
}

const EMPTY_STATE: AgentsControllerState = {
  loading: false,
  error: null,
  agents: [],
};

const CACHE: Map<string, string[] | null | undefined> = new Map();

export class AgentsController extends SimpleSubscribable<AgentsControllerState> {
  private backend: AgentBackend | null;
  private cacheKey: string;

  constructor(options: { backend: AgentBackend | null; cacheKey: string }) {
    super(EMPTY_STATE);
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;

    const cachedAgents = CACHE.get(this.cacheKey);
    if (cachedAgents !== undefined) {
      this.setSnapshot({ loading: false, error: null, agents: cachedAgents || [] });
    }
  }

  invalidate(): void {
    CACHE.delete(this.cacheKey);
    this.setSnapshot(EMPTY_STATE);
  }

  async load(): Promise<string[]> {
    if (!this.backend) {
      this.setSnapshot({ ...EMPTY_STATE, error: 'No active connection' });
      throw new Error('No active connection');
    }

    const existing = CACHE.get(this.cacheKey);
    if (existing !== undefined) {
      const agents = existing || [];
      this.setSnapshot({ loading: false, error: null, agents });
      return agents;
    }

    const snapshot = this.getSnapshot();
    if (snapshot.loading) {
      return snapshot.agents;
    }

    this.setSnapshot({ ...snapshot, loading: true, error: null });
    try {
      const agents = await this.backend.listAgents();
      const list = Array.isArray(agents) ? agents : [];
      CACHE.set(this.cacheKey, list);
      this.setSnapshot({ loading: false, error: null, agents: list });
      return list;
    } catch (err: any) {
      CACHE.set(this.cacheKey, null);
      this.setSnapshot({ loading: false, error: err?.message || 'Failed to load agents', agents: [] });
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
}

export function pickDefaultAgentId(agents: string[]): string | null {
  if (!Array.isArray(agents) || agents.length === 0) return null;
  const first = agents[0];
  return typeof first === 'string' && first.trim() ? first.trim() : null;
}
