import type { AgentBackend } from '../backend/backend';
import type { SessionSummary } from '../types/sessions';
import { SimpleSubscribable } from '../util/subscribable';

export interface SessionContextControllerState {
  summary: SessionSummary | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  lastLoadedAt: number | null;
}

interface CachedSessionContextSnapshot {
  summary: SessionSummary;
  lastLoadedAt: number | null;
}

const EMPTY_STATE: SessionContextControllerState = {
  summary: null,
  loading: false,
  refreshing: false,
  error: null,
  lastLoadedAt: null,
};

const CACHE_BY_BACKEND: WeakMap<object, Map<string, CachedSessionContextSnapshot>> = new WeakMap();

function asBackendKey(backend: AgentBackend | null): object | null {
  if (backend && (typeof backend === 'object' || typeof backend === 'function')) {
    return backend as object;
  }
  return null;
}

function getCacheMap(backend: AgentBackend | null): Map<string, CachedSessionContextSnapshot> | null {
  const backendKey = asBackendKey(backend);
  if (!backendKey) {
    return null;
  }

  let cache = CACHE_BY_BACKEND.get(backendKey);
  if (!cache) {
    cache = new Map<string, CachedSessionContextSnapshot>();
    CACHE_BY_BACKEND.set(backendKey, cache);
  }
  return cache;
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

function isSessionSummary(value: unknown): value is SessionSummary {
  return !!value && typeof value === 'object' && typeof (value as any).session_id === 'string';
}

export class SessionContextController extends SimpleSubscribable<SessionContextControllerState> {
  private backend: AgentBackend | null;
  private cacheKey: string;
  private sessionId: string;
  private requestSeq = 0;
  private loadPromise: Promise<SessionSummary | null> | null = null;

  constructor(options: {
    backend: AgentBackend | null;
    cacheKey: string;
    sessionId: string;
    initialSummary?: SessionSummary | null;
    initialLoadedAt?: number | null;
  }) {
    super(EMPTY_STATE);
    this.backend = options.backend;
    this.cacheKey = options.cacheKey;
    this.sessionId = options.sessionId;

    const cached = this.readCache();
    if (cached) {
      this.setSnapshot({
        ...EMPTY_STATE,
        summary: cached.summary,
        lastLoadedAt: cached.lastLoadedAt,
      });
    } else if (isSessionSummary(options.initialSummary)) {
      this.hydrateFromSummary({
        summary: options.initialSummary,
        lastLoadedAt: options.initialLoadedAt ?? null,
      });
    }
  }

  hydrateFromSummary(options: { summary: SessionSummary | null; lastLoadedAt?: number | null }): void {
    if (!isSessionSummary(options.summary)) {
      return;
    }
    const snapshot = this.getSnapshot();
    if (snapshot.loading || snapshot.refreshing) {
      return;
    }
    const next = {
      ...snapshot,
      summary: options.summary,
      error: null,
      lastLoadedAt: options.lastLoadedAt ?? snapshot.lastLoadedAt,
    };
    this.writeCache(next);
    this.setSnapshot(next);
  }

  invalidate(): void {
    const cache = getCacheMap(this.backend);
    cache?.delete(this.buildCacheKey());
    this.requestSeq += 1;
    this.loadPromise = null;
  }

  async load(): Promise<SessionSummary | null> {
    if (!this.backend) {
      this.setSnapshot(EMPTY_STATE);
      return null;
    }

    if (this.loadPromise) {
      return this.loadPromise;
    }

    const seq = ++this.requestSeq;
    const current = this.getSnapshot();
    const hasSummary = current.summary != null;
    this.setSnapshot({
      ...current,
      loading: !hasSummary,
      refreshing: hasSummary,
      error: null,
    });

    const promise = (async () => {
      try {
        const summary = await this.backend!.getSessionSummary(this.sessionId);
        if (this.requestSeq !== seq) {
          return this.getSnapshot().summary;
        }

        const next: SessionContextControllerState = {
          summary,
          loading: false,
          refreshing: false,
          error: null,
          lastLoadedAt: Date.now(),
        };
        this.writeCache(next);
        this.setSnapshot(next);
        return summary;
      } catch (error) {
        if (this.requestSeq !== seq) {
          return this.getSnapshot().summary;
        }

        this.setSnapshot({
          ...this.getSnapshot(),
          loading: false,
          refreshing: false,
          error: formatErrorMessage(error),
        });
        return this.getSnapshot().summary;
      } finally {
        if (this.requestSeq === seq) {
          this.loadPromise = null;
        }
      }
    })();

    this.loadPromise = promise;
    return promise;
  }

  async refresh(): Promise<SessionSummary | null> {
    return this.load();
  }

  async loadIfStale(options: { staleMs: number; nowMs?: number }): Promise<SessionSummary | null> {
    const snapshot = this.getSnapshot();
    if (snapshot.loading || snapshot.refreshing) {
      return null;
    }

    const nowMs = options.nowMs ?? Date.now();
    const hasTimestamp = snapshot.lastLoadedAt != null;
    const isStale = hasTimestamp && nowMs - snapshot.lastLoadedAt! > options.staleMs;
    if (!hasTimestamp || isStale) {
      return this.load();
    }
    return null;
  }

  private buildCacheKey(): string {
    return `${this.cacheKey}:${this.sessionId}`;
  }

  private readCache(): CachedSessionContextSnapshot | null {
    const cache = getCacheMap(this.backend);
    return cache?.get(this.buildCacheKey()) ?? null;
  }

  private writeCache(state: Pick<SessionContextControllerState, 'summary' | 'lastLoadedAt'>): void {
    if (!state.summary) {
      return;
    }
    const cache = getCacheMap(this.backend);
    cache?.set(this.buildCacheKey(), {
      summary: state.summary,
      lastLoadedAt: state.lastLoadedAt,
    });
  }
}