import type { AgentBackend } from '../backend/backend';
import { subscribeServerSettingsInvalidated } from '../serverSettings/serverSettingsInvalidation';
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
  private unsubscribeServerSettings: (() => void) | null = null;

  constructor(options: { backend: AgentBackend; initialSessions?: SessionSummary[]; limit?: number }) {
    super({
      sessions: options.initialSessions ?? [],
      loading: false,
      error: null,
      lastLoadedAt: null,
    });
    this.backend = options.backend;
    this.limit = options.limit;
    this.unsubscribeServerSettings = subscribeServerSettingsInvalidated(
      this.backend,
      () => {
        this.load({ force: true }).catch(() => {
          // Errors are stored in controller state.
        });
      },
    );
  }

  close(): void {
    this.unsubscribeServerSettings?.();
    this.unsubscribeServerSettings = null;
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

  async loadIfStale(options: { staleMs: number; nowMs?: number }): Promise<SessionSummary[] | null> {
    const snapshot = this.getSnapshot();
    if (snapshot.loading) {
      return null;
    }

    const nowMs = options.nowMs ?? Date.now();
    const hasTimestamp = snapshot.lastLoadedAt != null;
    const isStale = hasTimestamp && nowMs - snapshot.lastLoadedAt! > options.staleMs;
    if (!hasTimestamp || isStale) {
      return this.load({ force: true });
    }
    return null;
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
