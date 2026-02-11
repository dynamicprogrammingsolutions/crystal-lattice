export const STORAGE_KEY_OPEN_TABS = 'clc_open_tabs_v1';

export type PersistedOpenTab = {
  connectionId: string;
  sessionId: string;
  title: string;
  subtitle?: string | null;
};

export type PersistedOpenTabsStateV1 = {
  version: 1;
  activeTabId: string | null;
  tabs: PersistedOpenTab[];
};

function parsePersistedOpenTab(value: unknown): PersistedOpenTab | null {
  if (!value || typeof value !== 'object') {
    return null;
  }

  const record = value as any;
  if (typeof record.connectionId !== 'string' || !record.connectionId) {
    return null;
  }
  if (typeof record.sessionId !== 'string' || !record.sessionId) {
    return null;
  }

  const title = typeof record.title === 'string' && record.title ? record.title : record.sessionId;
  const subtitle =
    record.subtitle === null || typeof record.subtitle === 'string' ? (record.subtitle as any) : null;

  return {
    connectionId: record.connectionId,
    sessionId: record.sessionId,
    title,
    subtitle,
  };
}

export function parsePersistedOpenTabsState(raw: string | null): PersistedOpenTabsStateV1 | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') {
      return null;
    }

    if ((parsed as any).version !== 1) {
      return null;
    }

    const tabsRaw = (parsed as any).tabs;
    if (!Array.isArray(tabsRaw)) {
      return null;
    }

    const tabs: PersistedOpenTab[] = [];
    for (const entry of tabsRaw) {
      const tab = parsePersistedOpenTab(entry);
      if (tab) {
        tabs.push(tab);
      }
    }

    const activeRaw = (parsed as any).activeTabId;
    const activeTabId = typeof activeRaw === 'string' ? activeRaw : null;

    return {
      version: 1,
      activeTabId,
      tabs,
    };
  } catch {
    return null;
  }
}

export function serializePersistedOpenTabsState(state: {
  activeTabId: string | null;
  tabs: PersistedOpenTab[];
}): string {
  const payload: PersistedOpenTabsStateV1 = {
    version: 1,
    activeTabId: state.activeTabId,
    tabs: state.tabs,
  };

  return JSON.stringify(payload);
}
