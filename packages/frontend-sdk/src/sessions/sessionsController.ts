import type { AgentBackend } from '../backend/backend';
import type { SessionSummary } from '../types/sessions';
import { SimpleSubscribable } from '../util/subscribable';

export interface SessionsControllerState {
  sessions: SessionSummary[];
  loading: boolean;
  error: string | null;
  lastLoadedAt: number | null;
}

export class SessionsController extends SimpleSubscribable<SessionsControllerState> {
  private backend: AgentBackend;
  private limit?: number;

  constructor(options: { backend: AgentBackend; initialSessions?: SessionSummary[]; limit?: number }) {
    super({
      sessions: options.initialSessions ?? [],
      loading: false,
      error: null,
      lastLoadedAt: null,
    });
    this.backend = options.backend;
    this.limit = options.limit;
  }

  hydrateFromCache(options: { sessions: SessionSummary[]; lastLoadedAt?: number | null }): void {
    const snapshot = this.getSnapshot();
    if (snapshot.loading) {
      return;
    }

    this.setSnapshot({
      ...snapshot,
      sessions: options.sessions,
      error: null,
      lastLoadedAt: options.lastLoadedAt ?? snapshot.lastLoadedAt,
    });
  }

  async load(options: { force?: boolean } = {}): Promise<SessionSummary[]> {
    const snapshot = this.getSnapshot();
    if (!options.force && snapshot.loading) {
      return snapshot.sessions;
    }

    this.setSnapshot({ ...snapshot, loading: true, error: null });
    try {
      const sessions = await this.backend.listSessions({ limit: this.limit });
      const next = Array.isArray(sessions) ? sessions : [];
      this.setSnapshot({
        sessions: next,
        loading: false,
        error: null,
        lastLoadedAt: Date.now(),
      });
      return next;
    } catch (err: any) {
      this.setSnapshot({
        ...this.getSnapshot(),
        loading: false,
        error: err?.message || 'Failed to load sessions',
      });
      throw err;
    }
  }

  async createSession(params?: { agentId?: string; systemMessage?: string }): Promise<{ sessionId: string }> {
    const resp = await this.backend.createSession({
      agentId: params?.agentId,
      systemMessage: params?.systemMessage,
    });
    const sessionId = resp?.session?.session_id;
    if (typeof sessionId !== 'string' || !sessionId) {
      throw new Error('Server did not return a session id');
    }
    return { sessionId };
  }
}
