import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

import {
  loadConnections,
  saveConnections,
  type ConnectionRecord,
  type KeyValueStore,
} from '@crystal-lattice/frontend-sdk';

import { DesktopShell } from './layout/DesktopShell';
import { ConnectionsPanelPlaceholder, type DesktopConnectionStub } from './panels/ConnectionsPanelPlaceholder';
import { SessionsPanelPlaceholder } from './panels/SessionsPanelPlaceholder';
import { ChatPanePlaceholder } from './chat/ChatPanePlaceholder';
import { SessionTabs, type DesktopSessionTab } from './tabs/SessionTabs';

function buildTabId(connectionId: string, sessionId: string): string {
  return `${connectionId}:${sessionId}`;
}

function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    const v = c === 'x' ? r : (r % 4) + 8;
    return v.toString(16);
  });
}

const connectionsStore: KeyValueStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};

function removeTabAndSelectNext(
  tabs: DesktopSessionTab[],
  removedTabId: string,
  activeTabId: string | null,
): { tabs: DesktopSessionTab[]; nextActiveTabId: string | null } {
  const index = tabs.findIndex((tab) => tab.tabId === removedTabId);
  if (index === -1) {
    return { tabs, nextActiveTabId: activeTabId };
  }

  const nextTabs = tabs.filter((tab) => tab.tabId !== removedTabId);
  if (activeTabId !== removedTabId) {
    return { tabs: nextTabs, nextActiveTabId: activeTabId };
  }

  if (nextTabs.length === 0) {
    return { tabs: nextTabs, nextActiveTabId: null };
  }

  const neighborIndex = Math.min(index, nextTabs.length - 1);
  return { tabs: nextTabs, nextActiveTabId: nextTabs[neighborIndex].tabId };
}

export function DesktopRoot(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [connectionRecords, setConnectionRecords] = useState<ConnectionRecord[]>([]);
  const [connectionsHydrated, setConnectionsHydrated] = useState(false);
  const [focusedConnectionId, setFocusedConnectionId] = useState<string | null>(null);
  const [openConnectionIds, setOpenConnectionIds] = useState<string[]>([]);
  const [tabs, setTabs] = useState<DesktopSessionTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);

  useEffect(() => {
    const hydrate = async () => {
      try {
        const records = await loadConnections(connectionsStore);
        setConnectionRecords(records);
      } finally {
        setConnectionsHydrated(true);
      }
    };

    hydrate();
  }, []);

  useEffect(() => {
    if (!connectionsHydrated) return;

    const save = async () => {
      try {
        await saveConnections(connectionsStore, connectionRecords);
      } catch {
      }
    };

    save();
  }, [connectionRecords, connectionsHydrated]);

  useEffect(() => {
    if (!connectionsHydrated) return;

    if (focusedConnectionId && connectionRecords.some((record) => record.id === focusedConnectionId)) {
      return;
    }

    const nextFocusedId = connectionRecords[0]?.id ?? null;
    setFocusedConnectionId(nextFocusedId);
    setOpenConnectionIds((prev) => {
      if (!nextFocusedId) return [];
      return prev.includes(nextFocusedId) ? prev : [nextFocusedId, ...prev];
    });
  }, [connectionRecords, connectionsHydrated, focusedConnectionId]);

  const connections: DesktopConnectionStub[] = useMemo(
    () => connectionRecords.map((record) => ({ id: record.id, name: record.name })),
    [connectionRecords],
  );

  const openTab = useCallback(
    ({ connectionId, sessionId, title }: { connectionId: string; sessionId: string; title?: string }) => {
      const tabId = buildTabId(connectionId, sessionId);
      setTabs((prev) => {
        if (prev.some((tab) => tab.tabId === tabId)) {
          return prev;
        }
        return [...prev, { tabId, connectionId, sessionId, title: title ?? sessionId }];
      });
      setActiveTabId(tabId);
      setOpenConnectionIds((prev) => (prev.includes(connectionId) ? prev : [...prev, connectionId]));
    },
    [],
  );

  const closeTab = useCallback((tabId: string) => {
    setTabs((prev) => {
      const result = removeTabAndSelectNext(prev, tabId, activeTabId);
      setActiveTabId(result.nextActiveTabId);
      return result.tabs;
    });
  }, [activeTabId]);

  const focusTab = useCallback((tabId: string) => {
    setActiveTabId(tabId);
  }, []);

  const activeTab = useMemo(() => {
    if (!activeTabId) return null;
    return tabs.find((tab) => tab.tabId === activeTabId) ?? null;
  }, [activeTabId, tabs]);

  const connectionNameById = useMemo(() => {
    const map: Record<string, string> = {};
    connections.forEach((c) => {
      map[c.id] = c.name;
    });
    return map;
  }, [connections]);

  const addDemoConnection = useCallback(() => {
    const now = Date.now();
    const nextPort = 8080 + connectionRecords.length;
    const record: ConnectionRecord = {
      id: generateId(),
      kind: 'manual',
      name: `Local (${nextPort})`,
      lastUsedAt: now,
      host: '127.0.0.1',
      port: nextPort,
    };

    setConnectionRecords((prev) => [record, ...prev]);
    setFocusedConnectionId(record.id);
    setOpenConnectionIds((prev) => (prev.includes(record.id) ? prev : [record.id, ...prev]));
  }, [connectionRecords.length]);

  const clearConnections = useCallback(() => {
    setConnectionRecords([]);
    setFocusedConnectionId(null);
    setOpenConnectionIds([]);
    setTabs([]);
    setActiveTabId(null);
  }, []);

  return (
    <View style={styles.root}>
      <DesktopShell
        left={(
          <View style={styles.leftColumn}>
            <ConnectionsPanelPlaceholder
              connections={connections}
              focusedConnectionId={focusedConnectionId}
              openConnectionIds={openConnectionIds}
              onFocusConnection={(id) => {
                setFocusedConnectionId(id);
                setOpenConnectionIds((prev) => (prev.includes(id) ? prev : [...prev, id]));
              }}
              onToggleOpenConnection={(id) => {
                setOpenConnectionIds((prev) =>
                  prev.includes(id) ? prev.filter((existing) => existing !== id) : [...prev, id],
                );
              }}
              onAddDemoConnection={addDemoConnection}
              onClearConnections={clearConnections}
            />

            <SessionsPanelPlaceholder
              focusedConnectionId={focusedConnectionId}
              focusedConnectionName={focusedConnectionId ? connectionNameById[focusedConnectionId] : null}
              isFocusedConnectionOpen={
                focusedConnectionId ? openConnectionIds.includes(focusedConnectionId) : false
              }
              onOpenSession={({ connectionId, sessionId, title }) => {
                openTab({ connectionId, sessionId, title });
              }}
            />
          </View>
        )}
        main={(
          <View style={styles.mainColumn}>
            <SessionTabs
              tabs={tabs}
              activeTabId={activeTabId}
              connectionNameById={connectionNameById}
              onSelectTab={focusTab}
              onCloseTab={closeTab}
            />

            <View style={styles.mainContent}>
              {tabs.length === 0 ? (
                <ChatPanePlaceholder
                  visible
                  title="No sessions open"
                  subtitle="Select a session from the left to open it in a tab."
                />
              ) : (
                tabs.map((tab) => (
                  <ChatPanePlaceholder
                    key={tab.tabId}
                    visible={tab.tabId === activeTabId}
                    title={tab.title}
                    subtitle={`${connectionNameById[tab.connectionId] ?? tab.connectionId} • ${tab.sessionId}`}
                  />
                ))
              )}
            </View>
          </View>
        )}
      />
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.background,
    },
    leftColumn: {
      flex: 1,
      gap: 12,
      padding: 12,
    },
    mainColumn: {
      flex: 1,
    },
    mainContent: {
      flex: 1,
      padding: 12,
    },
  });
}
