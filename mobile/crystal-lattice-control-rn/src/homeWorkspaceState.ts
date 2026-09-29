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
  /** Opt-in for human time tracking (default off). */
  timeTrackingEnabled: boolean;
  /** Frontend-owned telemetry plugin id the spans upload to. */
  timeTrackingPluginId: string;
}

export const DEFAULT_TIME_TRACKING_PLUGIN_ID = 'duration_tracking_app';

function normalizeTimeTrackingPluginId(value: unknown): string {
  return typeof value === 'string' && value.trim()
    ? value.trim()
    : DEFAULT_TIME_TRACKING_PLUGIN_ID;
}

export const DEFAULT_MOBILE_GLOBAL_PREFERENCES: MobileGlobalPreferences = {
  recentSessionsWindow: DEFAULT_RECENT_SESSIONS_WINDOW,
  timeTrackingEnabled: false,
  timeTrackingPluginId: DEFAULT_TIME_TRACKING_PLUGIN_ID,
};

export function normalizeMobileGlobalPreferences(
  value: unknown,
): MobileGlobalPreferences {
  const candidate =
    value && typeof value === 'object'
      ? (value as Partial<MobileGlobalPreferences>)
      : null;
  return {
    recentSessionsWindow: normalizeRecentSessionsWindow(candidate?.recentSessionsWindow),
    timeTrackingEnabled: candidate?.timeTrackingEnabled === true,
    timeTrackingPluginId: normalizeTimeTrackingPluginId(
      candidate?.timeTrackingPluginId,
    ),
  };
}
