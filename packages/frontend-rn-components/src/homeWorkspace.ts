import type {
  ConnectionRecord,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

export const MAX_SESSION_NOTE_LENGTH = 2000;

export type RecentSessionsWindow = '24h' | '3d' | '1w';

export interface WatchedSessionIdentity {
  connectionId: string;
  sessionId: string;
}

export interface HomeSessionItem extends WatchedSessionIdentity {
  key: string;
  connection: ConnectionRecord;
  summary: SessionSummary;
  note: string | null;
}

export interface HomeSessionCollections {
  watchlist: HomeSessionItem[];
  recent: HomeSessionItem[];
}

export interface HomeSessionsCacheEntry {
  sessions: SessionSummary[];
}

export type HomeSessionsCache = Record<string, HomeSessionsCacheEntry>;

export const DEFAULT_RECENT_SESSIONS_WINDOW: RecentSessionsWindow = '3d';

const RECENT_WINDOW_MS: Record<RecentSessionsWindow, number> = {
  '24h': 24 * 60 * 60 * 1000,
  '3d': 3 * 24 * 60 * 60 * 1000,
  '1w': 7 * 24 * 60 * 60 * 1000,
};

export function watchedSessionKey(
  connectionId: string,
  sessionId: string,
): string {
  return `${encodeURIComponent(connectionId)}::${encodeURIComponent(
    sessionId,
  )}`;
}

export function normalizeWatchlist(value: unknown): WatchedSessionIdentity[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  const normalized: WatchedSessionIdentity[] = [];
  for (const item of value) {
    if (!item || typeof item !== 'object') continue;
    const connectionId = (item as Record<string, unknown>).connectionId;
    const sessionId = (item as Record<string, unknown>).sessionId;
    if (
      typeof connectionId !== 'string' ||
      !connectionId ||
      typeof sessionId !== 'string' ||
      !sessionId
    ) {
      continue;
    }
    const key = watchedSessionKey(connectionId, sessionId);
    if (seen.has(key)) continue;
    seen.add(key);
    normalized.push({ connectionId, sessionId });
  }
  return normalized;
}

export function normalizeSessionNotes(value: unknown): Record<string, string> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const notes: Record<string, string> = {};
  for (const [sessionId, rawNote] of Object.entries(value)) {
    if (!sessionId || typeof rawNote !== 'string' || !rawNote.trim()) continue;
    notes[sessionId] = rawNote.slice(0, MAX_SESSION_NOTE_LENGTH);
  }
  return notes;
}

export function normalizeRecentSessionsWindow(
  value: unknown,
): RecentSessionsWindow {
  return value === '24h' || value === '3d' || value === '1w'
    ? value
    : DEFAULT_RECENT_SESSIONS_WINDOW;
}

export function moveWatchedSession(
  watchlist: readonly WatchedSessionIdentity[],
  fromIndex: number,
  toIndex: number,
): WatchedSessionIdentity[] {
  if (
    fromIndex < 0 ||
    fromIndex >= watchlist.length ||
    toIndex < 0 ||
    toIndex >= watchlist.length ||
    fromIndex === toIndex
  ) {
    return [...watchlist];
  }
  const next = [...watchlist];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
}

export function deriveHomeSessionCollections(options: {
  connections: readonly ConnectionRecord[];
  sessionsCache: HomeSessionsCache;
  watchlist: readonly WatchedSessionIdentity[];
  notes: Readonly<Record<string, string>>;
  recentSessionsWindow: RecentSessionsWindow;
  nowMs?: number;
}): HomeSessionCollections {
  const connectionsById = new Map(
    options.connections.map(connection => [connection.id, connection]),
  );
  const resolveItem = (
    connectionId: string,
    sessionId: string,
  ): HomeSessionItem | null => {
    const connection = connectionsById.get(connectionId);
    const summary = options.sessionsCache[connectionId]?.sessions.find(
      candidate => candidate.session_id === sessionId,
    );
    if (!connection || !summary) return null;
    return {
      key: watchedSessionKey(connectionId, sessionId),
      connectionId,
      sessionId,
      connection,
      summary,
      note: options.notes[sessionId] ?? null,
    };
  };

  const watchlist = options.watchlist
    .map(({ connectionId, sessionId }) => resolveItem(connectionId, sessionId))
    .filter((item): item is HomeSessionItem => item !== null);

  const cutoffMs =
    (options.nowMs ?? Date.now()) -
    RECENT_WINDOW_MS[options.recentSessionsWindow];
  const recent: HomeSessionItem[] = [];
  for (const connection of options.connections) {
    for (const summary of options.sessionsCache[connection.id]?.sessions ??
      []) {
      if (summary.modified * 1000 < cutoffMs) continue;
      recent.push({
        key: watchedSessionKey(connection.id, summary.session_id),
        connectionId: connection.id,
        sessionId: summary.session_id,
        connection,
        summary,
        note: options.notes[summary.session_id] ?? null,
      });
    }
  }
  recent.sort((left, right) => right.summary.modified - left.summary.modified);

  return { watchlist, recent };
}
