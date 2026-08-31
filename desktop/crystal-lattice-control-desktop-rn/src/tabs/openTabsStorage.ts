import {
  INITIAL_DESKTOP_WORKSPACE_STATE,
  type DesktopActiveWorkspace,
  type DesktopSessionTab,
  type DesktopWorkspaceState,
} from './desktopWorkspaceState';

export const STORAGE_KEY_OPEN_TABS = 'clc_open_tabs_v1';

type PersistedOpenTab = {
  connectionId: string;
  sessionId: string;
  title: string;
  subtitle?: string | null;
};

type PersistedOpenTabsStateV1 = {
  version: 1;
  activeTabId: string | null;
  tabs: PersistedOpenTab[];
};

type PersistedOpenTabsStateV2 = {
  version: 2;
  activeWorkspace: DesktopActiveWorkspace;
  permanentTabs: PersistedOpenTab[];
  previewTab: PersistedOpenTab | null;
};

function buildTabId(connectionId: string, sessionId: string): string {
  return `${connectionId}:${sessionId}`;
}

function parsePersistedOpenTab(value: unknown): DesktopSessionTab | null {
  if (!value || typeof value !== 'object') return null;
  const record = value as Record<string, unknown>;
  const connectionId = record.connectionId;
  const sessionId = record.sessionId;
  if (
    typeof connectionId !== 'string' ||
    !connectionId ||
    typeof sessionId !== 'string' ||
    !sessionId
  ) {
    return null;
  }
  return {
    tabId: buildTabId(connectionId, sessionId),
    connectionId,
    sessionId,
    title:
      typeof record.title === 'string' && record.title
        ? record.title
        : sessionId,
    subtitle:
      record.subtitle === null || typeof record.subtitle === 'string'
        ? record.subtitle
        : null,
  };
}

function normalizeUniqueTabs(values: unknown): DesktopSessionTab[] {
  if (!Array.isArray(values)) return [];
  const seen = new Set<string>();
  const tabs: DesktopSessionTab[] = [];
  for (const value of values) {
    const tab = parsePersistedOpenTab(value);
    if (!tab || seen.has(tab.tabId)) continue;
    seen.add(tab.tabId);
    tabs.push(tab);
  }
  return tabs;
}

function normalizeActiveWorkspace(
  value: unknown,
  permanentTabs: readonly DesktopSessionTab[],
  previewTab: DesktopSessionTab | null,
): DesktopActiveWorkspace {
  if (
    value &&
    typeof value === 'object' &&
    (value as Record<string, unknown>).kind === 'session'
  ) {
    const tabId = (value as Record<string, unknown>).tabId;
    if (
      typeof tabId === 'string' &&
      (previewTab?.tabId === tabId ||
        permanentTabs.some(tab => tab.tabId === tabId))
    ) {
      return { kind: 'session', tabId };
    }
  }
  return { kind: 'home' };
}

export function parsePersistedOpenTabsState(
  raw: string | null,
): DesktopWorkspaceState | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as
      | PersistedOpenTabsStateV1
      | PersistedOpenTabsStateV2;
    if (!parsed || typeof parsed !== 'object') return null;
    if (parsed.version === 1) {
      const permanentTabs = normalizeUniqueTabs(parsed.tabs);
      const activeWorkspace =
        typeof parsed.activeTabId === 'string' &&
        permanentTabs.some(tab => tab.tabId === parsed.activeTabId)
          ? { kind: 'session' as const, tabId: parsed.activeTabId }
          : permanentTabs.length > 0
          ? {
              kind: 'session' as const,
              tabId: permanentTabs[0].tabId,
            }
          : { kind: 'home' as const };
      return { permanentTabs, previewTab: null, activeWorkspace };
    }
    if (parsed.version !== 2) return null;
    const permanentTabs = normalizeUniqueTabs(parsed.permanentTabs);
    const permanentIds = new Set(permanentTabs.map(tab => tab.tabId));
    const parsedPreview = parsePersistedOpenTab(parsed.previewTab);
    const previewTab =
      parsedPreview && !permanentIds.has(parsedPreview.tabId)
        ? parsedPreview
        : null;
    return {
      permanentTabs,
      previewTab,
      activeWorkspace: normalizeActiveWorkspace(
        parsed.activeWorkspace,
        permanentTabs,
        previewTab,
      ),
    };
  } catch {
    return null;
  }
}

function persistedTab(tab: DesktopSessionTab): PersistedOpenTab {
  return {
    connectionId: tab.connectionId,
    sessionId: tab.sessionId,
    title: tab.title,
    subtitle: tab.subtitle ?? null,
  };
}

export function serializePersistedOpenTabsState(
  state: DesktopWorkspaceState,
): string {
  const payload: PersistedOpenTabsStateV2 = {
    version: 2,
    activeWorkspace: state.activeWorkspace,
    permanentTabs: state.permanentTabs.map(persistedTab),
    previewTab: state.previewTab ? persistedTab(state.previewTab) : null,
  };
  return JSON.stringify(payload);
}

export function emptyPersistedWorkspaceState(): DesktopWorkspaceState {
  return INITIAL_DESKTOP_WORKSPACE_STATE;
}
