import {
  DEFAULT_RECENT_SESSIONS_WINDOW,
  normalizeRecentSessionsWindow,
  type RecentSessionsWindow,
} from '@crystal-lattice/frontend-rn-components';

export const HOME_WATCHLIST_STORAGE_KEY = 'clc_home_watchlist_v1';
export const SESSION_NOTES_STORAGE_KEY = 'clc_session_notes_v1';
export const MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY =
  'clc_mobile_global_preferences_v1';

export type {
  HomeSessionCollections,
  HomeSessionItem,
  HomeSessionsCache,
  HomeSessionsCacheEntry,
  RecentSessionsWindow,
  WatchedSessionIdentity,
} from '@crystal-lattice/frontend-rn-components';
export {
  MAX_SESSION_NOTE_LENGTH,
  deriveHomeSessionCollections,
  moveWatchedSession,
  normalizeSessionNotes,
  normalizeWatchlist,
  watchedSessionKey,
} from '@crystal-lattice/frontend-rn-components';

export interface MobileGlobalPreferences {
  recentSessionsWindow: RecentSessionsWindow;
}

export const DEFAULT_MOBILE_GLOBAL_PREFERENCES: MobileGlobalPreferences = {
  recentSessionsWindow: DEFAULT_RECENT_SESSIONS_WINDOW,
};

export function normalizeMobileGlobalPreferences(
  value: unknown,
): MobileGlobalPreferences {
  const candidate =
    value && typeof value === 'object'
      ? (value as Partial<MobileGlobalPreferences>).recentSessionsWindow
      : null;
  return {
    recentSessionsWindow: normalizeRecentSessionsWindow(candidate),
  };
}
