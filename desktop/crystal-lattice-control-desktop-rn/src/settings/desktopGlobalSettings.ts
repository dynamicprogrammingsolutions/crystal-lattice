import {
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
}

export const DEFAULT_DESKTOP_GLOBAL_SETTINGS: DesktopGlobalSettings = {
  baseFontSize: DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize,
  headerSize: DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.headerSize,
  recentSessionsWindow: DEFAULT_RECENT_SESSIONS_WINDOW,
  sessionDoubleClickAction: 'preview',
  sessionsFollowActiveTabEnabled: false,
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
      record.sessionsFollowActiveTabEnabled === true,
  };
}
