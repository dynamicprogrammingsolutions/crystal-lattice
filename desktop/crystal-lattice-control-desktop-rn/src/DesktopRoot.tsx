import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MarkdownDisplayPreferencesProvider,
  ThemeProvider,
  applyDisplayTypographyPreset,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownHeaderSize,
  useTheme,
  type MarkdownBaseFontSize,
  type MarkdownDisplayPreferences,
  type MarkdownHeaderSize,
} from '@crystal-lattice/frontend-rn-components';

import type { ConnectionRecord, SessionSummary } from '@crystal-lattice/frontend-sdk';

import { DesktopShell } from './layout/DesktopShell';
import { ConnectionsPanel } from './panels/ConnectionsPanel';
import { SessionsPanel } from './panels/SessionsPanel';
import { ChatPanePlaceholder } from './chat/ChatPanePlaceholder';
import {ChatPaneTabStack, ChatPaneTabStackPlaceholder} from './tabs/ChatPaneTabStack';
import { SessionTabs, type DesktopSessionTab } from './tabs/SessionTabs';
import { usePersistedConnections } from './connections/usePersistedConnections';
import { useOpenConnections } from './connections/useOpenConnections';
import { asyncStorageKeyValueStore } from './storage/asyncStorageKeyValueStore';
import { desktopWindowEvents, DesktopWindowManager } from './windows/desktopWindowManager';
import { clearActiveSessionSettingsWindow } from './windows/sessionSettingsCoordinator';
import { cancelAttachmentMetadataWindowFromSystem } from './windows/attachmentMetadataCoordinator';
import { clearActiveSessionPluginsWindow } from './windows/sessionPluginsCoordinator';
import { clearActiveSessionSnapshotsWindow } from './windows/sessionSnapshotsCoordinator';
import { useMessagesCache } from './cache/useMessagesCache';
import { useSessionsCache } from './cache/useSessionsCache';
import { desktopEventBus } from './events/desktopEventBus';
import {
  DEFAULT_TAB_STRIP_STYLE,
  parseTabStripStyle,
  type TabStripStyle,
} from './tabs/tabStripStyle';
import {
  parsePersistedOpenTabsState,
  serializePersistedOpenTabsState,
  STORAGE_KEY_OPEN_TABS,
} from './tabs/openTabsStorage';
import { DesktopGlobalDisplayLayer } from './ui/DesktopGlobalDisplayLayer';
import { setActiveServerSettingsWindow } from './windows/serverSettingsCoordinator';

const EMPTY_CACHED_SESSIONS: SessionSummary[] = [];

const DEFAULT_CONNECTION_ROW_CLICK_BEHAVIOR = 'focusAndOpen' as const;

function buildTabId(connectionId: string, sessionId: string): string {
  return `${connectionId}:${sessionId}`;
}

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

function tabArrayEqualByReference(
  a: ReadonlyArray<DesktopSessionTab>,
  b: ReadonlyArray<DesktopSessionTab>,
): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

export interface DesktopRootProps {
  initialTabStripStyle?: TabStripStyle;
  initialSessionsFollowActiveTabEnabled?: boolean;
  initialMarkdownBaseFontSize?: MarkdownBaseFontSize;
  initialMarkdownHeaderSize?: MarkdownHeaderSize;
}

export function DesktopRoot({
  initialTabStripStyle,
  initialSessionsFollowActiveTabEnabled,
  initialMarkdownBaseFontSize,
  initialMarkdownHeaderSize,
}: DesktopRootProps): React.JSX.Element {
  const baseTheme = useTheme();

  const [tabStripStyle, setTabStripStyle] = useState<TabStripStyle>(
    parseTabStripStyle(initialTabStripStyle) ?? DEFAULT_TAB_STRIP_STYLE,
  );

  const [sessionsFollowActiveTabEnabled, setSessionsFollowActiveTabEnabled] = useState<boolean>(
    initialSessionsFollowActiveTabEnabled !== undefined
      ? !!initialSessionsFollowActiveTabEnabled
      : true,
  );
  const [markdownDisplayPreferences, setMarkdownDisplayPreferences] =
    useState<MarkdownDisplayPreferences>({
      baseFontSize: normalizeMarkdownBaseFontSize(
        initialMarkdownBaseFontSize ??
          DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize,
      ),
      headerSize: normalizeMarkdownHeaderSize(
        initialMarkdownHeaderSize ??
          DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.headerSize,
      ),
    });
  const theme = useMemo(
    () => applyDisplayTypographyPreset(
      baseTheme,
      markdownDisplayPreferences.baseFontSize,
    ),
    [baseTheme, markdownDisplayPreferences.baseFontSize],
  );
  const styles = useMemo(() => createStyles(theme), [theme]);

  const {
    hydrated: connectionsHydrated,
    sortedConnectionRecords,
    upsertConnection,
    deleteConnection,
    touchConnection,
    clearConnections,
  } = usePersistedConnections(asyncStorageKeyValueStore);

  const {
    openConnectionsById,
    openConnection,
    closeConnection,
    closeAllConnections,
    getBackend,
  } = useOpenConnections();

  // Cache hooks are introduced in task 060 so tabs can remain viewable offline.
  // UI consumption is implemented in tasks 070/080.
  const {
    sessionsCache,
    updateSessionsCache,
    deleteConnectionSessionsCache,
    clearSessionsCache,
  } = useSessionsCache(asyncStorageKeyValueStore);

  const {
    messagesCache,
    hydrated: messagesCacheHydrated,
    updateMessagesCache,
    deleteConnectionMessagesCache,
    clearMessagesCache,
  } = useMessagesCache(asyncStorageKeyValueStore);

  const [focusedConnectionId, setFocusedConnectionId] = useState<string | null>(null);
  const [tabs, setTabs] = useState<DesktopSessionTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);

  const activeTabIdRef = useRef<string | null>(null);
  useEffect(() => {
    activeTabIdRef.current = activeTabId;
  }, [activeTabId]);

  const [tabsHydrated, setTabsHydrated] = useState(false);
  const hydratedTabRangesRef = useRef<
    Array<{ connectionId: string; sessionId: string; rangeStartText?: string | null; rangeEndText?: string | null }>
  >([]);
  const didSeedTabRangesRef = useRef(false);

  const [didAutoOpenMostRecent, setDidAutoOpenMostRecent] = useState(false);

  const lastValidatedOpenedAtByConnectionRef = useRef<Record<string, number>>({});
  const validatingConnectionIdsRef = useRef<Set<string>>(new Set());

  const lastSavedOpenTabsStateRef = useRef<{
    activeTabId: string | null;
    tabs: DesktopSessionTab[];
  } | null>(null);

  const openTab = useCallback(
    ({
      connectionId,
      sessionId,
      title,
      subtitle,
    }: {
      connectionId: string;
      sessionId: string;
      title?: string;
      subtitle?: string | null;
    }) => {
      const tabId = buildTabId(connectionId, sessionId);
      setTabs((prev) => {
        const existingIndex = prev.findIndex((tab) => tab.tabId === tabId);
        if (existingIndex >= 0) {
          const existing = prev[existingIndex];
          const nextTitle = typeof title === 'string' && title ? title : existing.title;
          const nextSubtitle = subtitle !== undefined ? subtitle : existing.subtitle;
          if (existing.title === nextTitle && existing.subtitle === nextSubtitle) {
            return prev;
          }
          const next = [...prev];
          next[existingIndex] = { ...existing, title: nextTitle, subtitle: nextSubtitle };
          return next;
        }
        return [
          ...prev,
          {
            tabId,
            connectionId,
            sessionId,
            title: title ?? sessionId,
            subtitle: subtitle ?? null,
          },
        ];
      });
      setActiveTabId(tabId);
    },
    [],
  );

  const updateOpenTabsPresentation = useCallback(
    (params: {
      connectionId: string;
      presentations: Record<string, { title: string; subtitle: string | null }>;
    }) => {
      setTabs((prev) => {
        if (prev.length === 0) {
          return prev;
        }

        let changed = false;
        const next = prev.map((tab) => {
          if (tab.connectionId !== params.connectionId) {
            return tab;
          }

          const presentation = params.presentations[tab.sessionId];
          if (!presentation) {
            return tab;
          }

          const nextTitle = presentation.title || tab.title;
          const nextSubtitle = presentation.subtitle;
          if (tab.title === nextTitle && tab.subtitle === nextSubtitle) {
            return tab;
          }
          changed = true;
          return { ...tab, title: nextTitle, subtitle: nextSubtitle };
        });

        return changed ? next : prev;
      });
    },
    [],
  );

  const closeTab = useCallback(
    (tabId: string) => {
      setTabs((prev) => {
        const result = removeTabAndSelectNext(prev, tabId, activeTabIdRef.current);
        setActiveTabId(result.nextActiveTabId);
        return result.tabs;
      });
    },
    [],
  );

  const focusTab = useCallback((tabId: string) => {
    setActiveTabId(tabId);
  }, []);

  const activeTab = useMemo(
    () => (activeTabId ? tabs.find((tab) => tab.tabId === activeTabId) ?? null : null),
    [activeTabId, tabs],
  );

  useEffect(() => {
    let cancelled = false;

    const hydrateTabs = async () => {
      try {
        const raw = await asyncStorageKeyValueStore.get(STORAGE_KEY_OPEN_TABS);
        const parsed = parsePersistedOpenTabsState(raw);
        if (!parsed || cancelled) {
          return;
        }

        hydratedTabRangesRef.current = parsed.tabs.map((tab) => ({
          connectionId: tab.connectionId,
          sessionId: tab.sessionId,
          rangeStartText: tab.rangeStartText,
          rangeEndText: tab.rangeEndText,
        }));

        setTabs((prevTabs) => {
          if (prevTabs.length > 0) {
            return prevTabs;
          }

          const restoredTabs: DesktopSessionTab[] = parsed.tabs.map((tab) => {
            const tabId = buildTabId(tab.connectionId, tab.sessionId);
            return {
              tabId,
              connectionId: tab.connectionId,
              sessionId: tab.sessionId,
              title: tab.title,
              subtitle: tab.subtitle ?? null,
            };
          });

          const restoredActive =
            parsed.activeTabId && restoredTabs.some((tab) => tab.tabId === parsed.activeTabId)
              ? parsed.activeTabId
              : restoredTabs[0]?.tabId ?? null;

          setActiveTabId(restoredActive);

          const focusedConnection = restoredActive
            ? restoredTabs.find((tab) => tab.tabId === restoredActive)?.connectionId
            : restoredTabs[0]?.connectionId;
          if (focusedConnection) {
            setFocusedConnectionId(focusedConnection);
          }

          lastSavedOpenTabsStateRef.current = {
            activeTabId: restoredActive,
            tabs: restoredTabs,
          };

          return restoredTabs;
        });
      } finally {
        if (!cancelled) {
          setTabsHydrated(true);
        }
      }
    };

    hydrateTabs();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!tabsHydrated) {
      return;
    }
    if (!messagesCacheHydrated) {
      return;
    }
    if (didSeedTabRangesRef.current) {
      return;
    }

    const ranges = hydratedTabRangesRef.current;
    if (ranges.length === 0) {
      didSeedTabRangesRef.current = true;
      return;
    }

    didSeedTabRangesRef.current = true;
    for (const range of ranges) {
      const startText = range.rangeStartText;
      const endText = range.rangeEndText;
      if (startText == null && endText == null) {
        continue;
      }

      const existing = messagesCache[range.connectionId]?.[range.sessionId];
      const existingHasRange =
        (typeof existing?.rangeStartText === 'string' || existing?.rangeStartText === null) &&
        (typeof existing?.rangeEndText === 'string' || existing?.rangeEndText === null);
      if (existing && existingHasRange) {
        continue;
      }

      updateMessagesCache({
        connectionId: range.connectionId,
        sessionId: range.sessionId,
        messages: existing?.messages ?? [],
        cursorEventId: existing?.cursorEventId ?? null,
        activeRequestId: existing?.activeRequestId ?? null,
        rangeStartText: startText ?? null,
        rangeEndText: endText ?? null,
      });
    }
  }, [messagesCache, messagesCacheHydrated, tabsHydrated, updateMessagesCache]);

  useEffect(() => {
    if (!tabsHydrated) {
      return;
    }

    const lastSaved = lastSavedOpenTabsStateRef.current;
    if (
      lastSaved &&
      lastSaved.activeTabId === activeTabId &&
      tabArrayEqualByReference(lastSaved.tabs, tabs)
    ) {
      return;
    }

    lastSavedOpenTabsStateRef.current = {
      activeTabId,
      tabs,
    };

    const save = async () => {
      try {
        await asyncStorageKeyValueStore.set(
          STORAGE_KEY_OPEN_TABS,
          serializePersistedOpenTabsState({
            activeTabId,
            tabs: tabs.map((tab) => ({
              connectionId: tab.connectionId,
              sessionId: tab.sessionId,
              title: tab.title,
              subtitle: tab.subtitle ?? null,
            })),
          }),
        );
      } catch {
      }
    };

    save();
  }, [activeTabId, tabs, tabsHydrated]);

  useEffect(() => {
    if (!connectionsHydrated) return;

    if (
      focusedConnectionId &&
      sortedConnectionRecords.some((record) => record.id === focusedConnectionId)
    ) {
      return;
    }

    const nextFocusedId = sortedConnectionRecords[0]?.id ?? null;
    setFocusedConnectionId(nextFocusedId);
  }, [connectionsHydrated, focusedConnectionId, sortedConnectionRecords]);

  const openConnectionAndTouch = useCallback(
    async (record: ConnectionRecord) => {
      touchConnection(record.id);
      const backend = await openConnection(record);
      if (!backend) {
        return;
      }

      try {
        const sessions = await backend.listSessions();
        updateSessionsCache(record.id, sessions);
      } catch {
        // Ignore; cache remains stale.
      }
    },
    [openConnection, touchConnection, updateSessionsCache],
  );

  useEffect(() => {
    if (!connectionsHydrated) return;
    if (!tabsHydrated) return;

    if (tabs.length > 0) {
      // If tabs were restored, don't auto-open any connections.
      setDidAutoOpenMostRecent(true);
      return;
    }
    if (didAutoOpenMostRecent) return;
    const mostRecent = sortedConnectionRecords[0];
    if (!mostRecent) {
      return;
    }

    setDidAutoOpenMostRecent(true);
    setFocusedConnectionId(mostRecent.id);
    openConnectionAndTouch(mostRecent);
  }, [
    connectionsHydrated,
    didAutoOpenMostRecent,
    openConnectionAndTouch,
    sortedConnectionRecords,
    tabs,
    tabsHydrated,
  ]);

  useEffect(() => {
    if (!connectionsHydrated) return;
    if (!tabsHydrated) return;

    const validConnectionIds = new Set(sortedConnectionRecords.map((record) => record.id));
    setTabs((prevTabs) => {
      if (prevTabs.length === 0) {
        return prevTabs;
      }

      const nextTabs = prevTabs.filter((tab) => validConnectionIds.has(tab.connectionId));
      if (nextTabs.length === prevTabs.length) {
        return prevTabs;
      }

      setActiveTabId((prevActive) => {
        if (prevActive && nextTabs.some((tab) => tab.tabId === prevActive)) {
          return prevActive;
        }
        return nextTabs[0]?.tabId ?? null;
      });

      return nextTabs;
    });
  }, [connectionsHydrated, sortedConnectionRecords, tabsHydrated]);

  useEffect(() => {
    if (!tabsHydrated) {
      return;
    }

    const openConnectionIds = Object.keys(openConnectionsById);
    if (openConnectionIds.length === 0) {
      return;
    }

    for (const connectionId of openConnectionIds) {
      const openState = openConnectionsById[connectionId];
      if (!openState || openState.status !== 'open' || !openState.backend) {
        continue;
      }

      const openedAt = typeof openState.lastOpenedAt === 'number' ? openState.lastOpenedAt : 0;
      if (!openedAt) {
        continue;
      }

      if (lastValidatedOpenedAtByConnectionRef.current[connectionId] === openedAt) {
        continue;
      }

      if (validatingConnectionIdsRef.current.has(connectionId)) {
        continue;
      }

      lastValidatedOpenedAtByConnectionRef.current[connectionId] = openedAt;
      validatingConnectionIdsRef.current.add(connectionId);

      const backend = openState.backend;
      const tabsForConnection = tabs.filter((tab) => tab.connectionId === connectionId);
      if (tabsForConnection.length === 0) {
        validatingConnectionIdsRef.current.delete(connectionId);
        continue;
      }

      (async () => {
        try {
          for (const tab of tabsForConnection) {
            try {
              await backend.getSessionAgent(tab.sessionId);
            } catch (err: any) {
              const message = typeof err?.message === 'string' ? err.message : '';
              if (/\bHTTP 404\b/.test(message)) {
                closeTab(tab.tabId);
              }
            }
          }
        } finally {
          validatingConnectionIdsRef.current.delete(connectionId);
        }
      })();
    }
  }, [closeTab, openConnectionsById, tabs, tabsHydrated]);

  useEffect(() => {
    if (!desktopWindowEvents) return;

    const savedSub = desktopWindowEvents.addListener('connectionEditorSaved', (payload: any) => {
      const record = payload?.record;
      if (!record || typeof record !== 'object' || typeof record.id !== 'string') {
        return;
      }
      upsertConnection(record);
      setFocusedConnectionId(record.id);
      openConnectionAndTouch(record);
    });

    const styleSub = desktopWindowEvents.addListener('tabStripStyleChanged', (payload: any) => {
      const style = parseTabStripStyle(payload?.style);
      if (!style) {
        return;
      }
      setTabStripStyle(style);
    });

    const followSub = desktopWindowEvents.addListener(
      'sessionsFollowActiveTabChanged',
      (payload: any) => {
        if (payload && typeof payload.enabled === 'boolean') {
          setSessionsFollowActiveTabEnabled(payload.enabled);
        }
      },
    );

    const markdownBaseFontSizeSub = desktopWindowEvents.addListener(
      'markdownBaseFontSizeChanged',
      (payload: any) => {
        setMarkdownDisplayPreferences((current) => ({
          ...current,
          baseFontSize: normalizeMarkdownBaseFontSize(payload?.baseFontSize),
        }));
      },
    );

    const markdownHeaderSizeSub = desktopWindowEvents.addListener(
      'markdownHeaderSizeChanged',
      (payload: any) => {
        setMarkdownDisplayPreferences((current) => ({
          ...current,
          headerSize: normalizeMarkdownHeaderSize(payload?.headerSize),
        }));
      },
    );

    const clearStoredSessionCachesSub = desktopWindowEvents.addListener(
      'clearStoredSessionCachesRequested',
      () => {
        clearSessionsCache();
        clearMessagesCache();
        setTabs([]);
        setActiveTabId(null);
      },
    );

    const agentPickerSub = desktopWindowEvents.addListener(
      'agentPickerSelected',
      (payload: any) => {
        const pickedConnectionId = payload?.connectionId;
        const agentId = payload?.agentId;
        const mode = payload?.mode;
        const pickedSessionId = payload?.sessionId;
        if (typeof pickedConnectionId !== 'string' || !pickedConnectionId) {
          return;
        }
        if (typeof agentId !== 'string' || !agentId) {
          return;
        }

        const backend = getBackend(pickedConnectionId);
        if (!backend) {
          return;
        }

        if (mode === 'switchSessionAgent') {
          if (typeof pickedSessionId !== 'string' || !pickedSessionId) {
            return;
          }

          backend
            .switchSessionAgent(pickedSessionId, agentId)
            .then(() => {
              desktopEventBus.publish('sessionAgentSwitched', {
                connectionId: pickedConnectionId,
                sessionId: pickedSessionId,
                agentId,
              });
            })
            .catch(() => {});
          return;
        }

        backend
          .createSession({ agentId })
          .then((resp) => {
            const sessionId = resp?.session?.session_id;
            if (typeof sessionId !== 'string' || !sessionId) {
              return;
            }
            openTab({ connectionId: pickedConnectionId, sessionId, title: `Session ${sessionId.slice(0, 8)}` });
            desktopEventBus.publish('sessionsReloadRequested', {
              connectionId: pickedConnectionId,
              reason: 'sessionCreated',
            });

            backend
              .listSessions()
              .then((sessions) => {
                if (Array.isArray(sessions)) {
                  updateSessionsCache(pickedConnectionId, sessions);
                }
              })
              .catch(() => {});
          })
          .catch(() => {});
      },
    );

    const sessionSettingsCancelledSub = desktopWindowEvents.addListener(
      'reactWindowCancelled',
      (payload) => {
        const windowKey = payload?.windowKey;
        if (windowKey === 'sessionSettings') {
          clearActiveSessionSettingsWindow();
        }
        if (windowKey === 'sessionPlugins') {
          clearActiveSessionPluginsWindow();
        }
        if (windowKey === 'sessionSnapshots') {
          clearActiveSessionSnapshotsWindow();
        }
        if (windowKey === 'attachmentMetadata') {
          cancelAttachmentMetadataWindowFromSystem();
        }
        if (windowKey === 'serverSettings') {
          setActiveServerSettingsWindow(null);
        }
      },
    );

    return () => {
      savedSub.remove();
      styleSub.remove();
      followSub.remove();
      markdownBaseFontSizeSub.remove();
      markdownHeaderSizeSub.remove();
      clearStoredSessionCachesSub.remove();
      agentPickerSub.remove();
      sessionSettingsCancelledSub.remove();
    };
  }, [
    clearMessagesCache,
    clearSessionsCache,
    getBackend,
    openConnectionAndTouch,
    openTab,
    updateSessionsCache,
    upsertConnection,
  ]);

  const connectionNameById = useMemo(() => {
    const map: Record<string, string> = {};
    sortedConnectionRecords.forEach((record) => {
      map[record.id] = record.name;
    });
    return map;
  }, [sortedConnectionRecords]);

  const openNewConnectionEditor = useCallback(() => {
    DesktopWindowManager?.openConnectionEditor({ mode: 'new' });
  }, []);

  const openEditConnectionEditor = useCallback((record: ConnectionRecord) => {
    DesktopWindowManager?.openConnectionEditor({ mode: 'edit', initialRecord: record });
  }, []);

  const handleClearConnections = useCallback(() => {
    clearConnections();
    closeAllConnections();
    clearSessionsCache();
    clearMessagesCache();
    setFocusedConnectionId(null);
    setTabs([]);
    setActiveTabId(null);
  }, [clearConnections, clearMessagesCache, clearSessionsCache, closeAllConnections]);

  const handleDeleteConnection = useCallback(
    (id: string) => {
      closeConnection(id);
      deleteConnection(id);
      deleteConnectionSessionsCache(id);
      deleteConnectionMessagesCache(id);
      setTabs((prev) => {
        const remaining = prev.filter((tab) => tab.connectionId !== id);

        setActiveTabId((currentActive) => {
          if (!currentActive) {
            return remaining[0]?.tabId ?? null;
          }
          if (!currentActive.startsWith(`${id}:`)) {
            return currentActive;
          }
          return remaining[0]?.tabId ?? null;
        });

        return remaining;
      });
      setFocusedConnectionId((prev) => (prev === id ? null : prev));
    },
    [
      closeConnection,
      deleteConnection,
      deleteConnectionMessagesCache,
      deleteConnectionSessionsCache,
    ],
  );

  return (
    <MarkdownDisplayPreferencesProvider
      value={markdownDisplayPreferences}
      onChange={setMarkdownDisplayPreferences}
    >
    <ThemeProvider theme={theme}>
    <View style={styles.root}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={openConnectionsById}
        connectionNameById={connectionNameById}
      >
      <DesktopShell
        left={(
          <View style={styles.leftColumn}>
            <ConnectionsPanel
              connectionRecords={sortedConnectionRecords}
              focusedConnectionId={focusedConnectionId}
              openConnectionsById={openConnectionsById}
              rowClickBehavior={DEFAULT_CONNECTION_ROW_CLICK_BEHAVIOR}
              onFocusConnection={(id) => setFocusedConnectionId(id)}
              onOpenConnection={(record) => {
                setFocusedConnectionId(record.id);
                openConnectionAndTouch(record);
              }}
              onCloseConnection={(id) => closeConnection(id)}
              onDeleteConnection={handleDeleteConnection}
              onClearConnections={handleClearConnections}
              onOpenNewConnectionEditor={openNewConnectionEditor}
              onOpenEditConnectionEditor={openEditConnectionEditor}
            />

            <SessionsPanel
              focusedConnectionId={focusedConnectionId}
              focusedConnectionName={
                focusedConnectionId ? connectionNameById[focusedConnectionId] : null
              }
              connectionBaseUrl={
                focusedConnectionId
                  ? openConnectionsById[focusedConnectionId]?.baseUrl ?? null
                  : null
              }
              connectionId={focusedConnectionId}
              backend={focusedConnectionId ? getBackend(focusedConnectionId) : null}
              isOnline={
                focusedConnectionId
                  ? openConnectionsById[focusedConnectionId]?.status === 'open'
                  : false
              }
              cachedSessions={
                focusedConnectionId
                  ? sessionsCache[focusedConnectionId]?.sessions ?? EMPTY_CACHED_SESSIONS
                  : EMPTY_CACHED_SESSIONS
              }
              cachedLastLoadedAt={
                focusedConnectionId ? sessionsCache[focusedConnectionId]?.lastLoadedAt ?? null : null
              }
              activeTabId={activeTabId}
              activeTabConnectionId={activeTab?.connectionId ?? null}
              activeTabSessionId={activeTab?.sessionId ?? null}
              followActiveTabEnabled={sessionsFollowActiveTabEnabled}
              onUpdateCache={updateSessionsCache}
              onOpenSessionTab={openTab}
              onUpdateOpenTabsPresentation={updateOpenTabsPresentation}
            />
          </View>
        )}
        main={(
          <View style={styles.mainColumn}>
            <SessionTabs
              tabs={tabs}
              activeTabId={activeTabId}
              styleVariant={tabStripStyle}
              connectionNameById={connectionNameById}
              onSelectTab={focusTab}
              onCloseTab={closeTab}
            />

            <View
              style={[
                styles.mainContent,
                tabStripStyle === 'codeTabs' || tabStripStyle === 'underlineTabs'
                  ? styles.mainContentCodeLike
                  : styles.mainContentCardLike,
              ]}
            >
              {tabs.length === 0 ? (
                <ChatPanePlaceholder
                  visible
                  title="No sessions open"
                  subtitle="Select a session from the left to open it in a tab."
                  styleVariant={tabStripStyle}
                />
              ) : (
	                <ChatPaneTabStack
	                  tabs={tabs}
	                  activeTabId={activeTabId}
	                  styleVariant={tabStripStyle}
	                  connectionNameById={connectionNameById}
	                  getBackend={getBackend}
	                  sessionsCache={sessionsCache}
	                  messagesCache={messagesCache}
                    messagesCacheHydrated={messagesCacheHydrated}
	                  onUpdateCache={updateMessagesCache}
	                  onOpenSessionTab={openTab}
	                />
              )}
            </View>
          </View>
        )}
      />
      </DesktopGlobalDisplayLayer>
    </View>
    </ThemeProvider>
    </MarkdownDisplayPreferencesProvider>
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
    mainContentCardLike: {
      backgroundColor: theme.backgroundAlt,
    },
    mainContentCodeLike: {
      padding: 0,
      backgroundColor: theme.surface,
    },
  });
}
