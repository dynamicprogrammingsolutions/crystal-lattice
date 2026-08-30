import type { ConnectionRecord, SessionSummary } from '@crystal-lattice/frontend-sdk';

export const HOME_WATCHLIST_STORAGE_KEY = 'clc_home_watchlist_v1';
export const SESSION_NOTES_STORAGE_KEY = 'clc_session_notes_v1';
export const MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY = 'clc_mobile_global_preferences_v1';
export const MAX_SESSION_NOTE_LENGTH = 2000;

export type RecentSessionsWindow = '24h' | '3d' | '1w';

export interface WatchedSessionIdentity {
  connectionId: string;
  sessionId: string;
}

export interface MobileGlobalPreferences {
  recentSessionsWindow: RecentSessionsWindow;
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

export const DEFAULT_MOBILE_GLOBAL_PREFERENCES: MobileGlobalPreferences = {
  recentSessionsWindow: '3d',
};

const RECENT_WINDOW_MS: Record<RecentSessionsWindow, number> = {
  '24h': 24 * 60 * 60 * 1000,
  '3d': 3 * 24 * 60 * 60 * 1000,
  '1w': 7 * 24 * 60 * 60 * 1000,
};

export function watchedSessionKey(
  connectionId: string,
  sessionId: string,
): string {
  return `${encodeURIComponent(connectionId)}::${encodeURIComponent(sessionId)}`;
}

export function normalizeWatchlist(value: unknown): WatchedSessionIdentity[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  const normalized: WatchedSessionIdentity[] = [];
  for (const item of value) {
    if (!item || typeof item !== 'object') continue;
    const connectionId = (item as any).connectionId;
    const sessionId = (item as any).sessionId;
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

export function normalizeMobileGlobalPreferences(
  value: unknown,
): MobileGlobalPreferences {
  const candidate =
    value && typeof value === 'object'
      ? (value as Partial<MobileGlobalPreferences>).recentSessionsWindow
      : null;
  return {
    recentSessionsWindow:
      candidate === '24h' || candidate === '3d' || candidate === '1w'
        ? candidate
        : DEFAULT_MOBILE_GLOBAL_PREFERENCES.recentSessionsWindow,
  };
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
    options.connections.map((connection) => [connection.id, connection]),
  );
  const watchedKeys = new Set(
    options.watchlist.map(({ connectionId, sessionId }) =>
      watchedSessionKey(connectionId, sessionId),
    ),
  );
  const resolveItem = (
    connectionId: string,
    sessionId: string,
  ): HomeSessionItem | null => {
    const connection = connectionsById.get(connectionId);
    const summary = options.sessionsCache[connectionId]?.sessions.find(
      (candidate) => candidate.session_id === sessionId,
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
    (options.nowMs ?? Date.now()) - RECENT_WINDOW_MS[options.recentSessionsWindow];
  const recent: HomeSessionItem[] = [];
  for (const connection of options.connections) {
    for (const summary of options.sessionsCache[connection.id]?.sessions ?? []) {
      const key = watchedSessionKey(connection.id, summary.session_id);
      if (watchedKeys.has(key) || summary.modified * 1000 < cutoffMs) continue;
      recent.push({
        key,
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