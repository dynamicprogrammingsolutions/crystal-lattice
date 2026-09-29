import {
  DEFAULT_HUMAN_TIME_PLUGIN_ID,
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  DEFAULT_RECENT_SESSIONS_WINDOW,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownHeaderSize,
  normalizeRecentSessionsWindow,
  type MarkdownBaseFontSize,
  type MarkdownHeaderSize,
  type RecentSessionsWindow,
} from '@crystal-lattice/frontend-rn-components';

export type SessionOpenMode = 'preview' | 'open';

export interface DesktopGlobalSettings {
  baseFontSize: MarkdownBaseFontSize;
  headerSize: MarkdownHeaderSize;
  recentSessionsWindow: RecentSessionsWindow;
  sessionDoubleClickAction: SessionOpenMode;
  sessionsFollowActiveTabEnabled: boolean;
  switchConnectionWithActiveTabEnabled: boolean;
  timeTrackingEnabled: boolean;
  timeTrackingPluginId: string;
  timeTrackingInactivitySeconds: number;
}

export const DEFAULT_TIME_TRACKING_INACTIVITY_SECONDS = 30;

export const DEFAULT_DESKTOP_GLOBAL_SETTINGS: DesktopGlobalSettings = {
  baseFontSize: DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize,
  headerSize: DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.headerSize,
  recentSessionsWindow: DEFAULT_RECENT_SESSIONS_WINDOW,
  sessionDoubleClickAction: 'preview',
  sessionsFollowActiveTabEnabled: true,
  switchConnectionWithActiveTabEnabled: false,
  timeTrackingEnabled: false,
  timeTrackingPluginId: DEFAULT_HUMAN_TIME_PLUGIN_ID,
  timeTrackingInactivitySeconds: DEFAULT_TIME_TRACKING_INACTIVITY_SECONDS,
};

export function normalizeSessionOpenMode(value: unknown): SessionOpenMode {
  return value === 'open' ? 'open' : 'preview';
}

export function complementarySessionOpenMode(
  value: SessionOpenMode,
): SessionOpenMode {
  return value === 'preview' ? 'open' : 'preview';
}

export function sessionOpenModeLabel(value: SessionOpenMode): string {
  return value === 'preview' ? 'Preview' : 'Open';
}

export function normalizeDesktopGlobalSettings(
  value: unknown,
): DesktopGlobalSettings {
  const record =
    value && typeof value === 'object'
      ? (value as Partial<DesktopGlobalSettings>)
      : {};
  return {
    baseFontSize: normalizeMarkdownBaseFontSize(record.baseFontSize),
    headerSize: normalizeMarkdownHeaderSize(record.headerSize),
    recentSessionsWindow: normalizeRecentSessionsWindow(
      record.recentSessionsWindow,
    ),
    sessionDoubleClickAction: normalizeSessionOpenMode(
      record.sessionDoubleClickAction,
    ),
    sessionsFollowActiveTabEnabled:
      typeof record.sessionsFollowActiveTabEnabled === 'boolean'
        ? record.sessionsFollowActiveTabEnabled
        : DEFAULT_DESKTOP_GLOBAL_SETTINGS.sessionsFollowActiveTabEnabled,
    switchConnectionWithActiveTabEnabled:
      record.switchConnectionWithActiveTabEnabled === true,
    timeTrackingEnabled: record.timeTrackingEnabled === true,
    timeTrackingPluginId:
      typeof record.timeTrackingPluginId === 'string' &&
      record.timeTrackingPluginId.trim()
        ? record.timeTrackingPluginId.trim()
        : DEFAULT_HUMAN_TIME_PLUGIN_ID,
    timeTrackingInactivitySeconds:
      typeof record.timeTrackingInactivitySeconds === 'number' &&
      Number.isFinite(record.timeTrackingInactivitySeconds) &&
      record.timeTrackingInactivitySeconds > 0
        ? record.timeTrackingInactivitySeconds
        : DEFAULT_TIME_TRACKING_INACTIVITY_SECONDS,
  };
}
