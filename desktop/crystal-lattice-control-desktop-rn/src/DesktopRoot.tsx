import React, {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from 'react';
import { AppState, StyleSheet, View } from 'react-native';

import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MarkdownDisplayPreferencesProvider,
  ThemeProvider,
  applyDisplayTypographyPreset,
  deriveHomeSessionCollections,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownHeaderSize,
  normalizeRecentSessionsWindow,
  useTheme,
  type MarkdownBaseFontSize,
  type MarkdownDisplayPreferences,
  type MarkdownHeaderSize,
  type HomeSessionItem,
  type RecentSessionsWindow,
} from '@crystal-lattice/frontend-rn-components';

import type {
  ConnectionRecord,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { useSessionRequestStatuses } from '@crystal-lattice/frontend-sdk-react';

import { DesktopShell } from './layout/DesktopShell';
import {
  DesktopActivityRail,
  type DesktopLowerPanel,
} from './layout/DesktopActivityRail';
import { ConnectionsPanel } from './panels/ConnectionsPanel';
import { HistoryPanel } from './panels/HistoryPanel';
import { SessionsPanel } from './panels/SessionsPanel';
import { ChatPanePlaceholder } from './chat/ChatPanePlaceholder';
import { ChatPaneTabStack } from './tabs/ChatPaneTabStack';
import { SessionTabs } from './tabs/SessionTabs';
import { usePersistedConnections } from './connections/usePersistedConnections';
import { useOpenConnections } from './connections/useOpenConnections';
import { asyncStorageKeyValueStore } from './storage/asyncStorageKeyValueStore';
import {
  desktopWindowEvents,
  DesktopWindowManager,
} from './windows/desktopWindowManager';
import { dismissActiveActionDisplayWindowFromSystem } from './windows/actionDisplayWindowCoordinator';
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
import {
  INITIAL_DESKTOP_WORKSPACE_STATE,
  desktopWorkspaceReducer,
  getActiveDesktopSessionTab,
  getDesktopWorkspaceTabs,
} from './tabs/desktopWorkspaceState';
import { DesktopGlobalDisplayLayer } from './ui/DesktopGlobalDisplayLayer';
import { setActiveServerSettingsWindow } from './windows/serverSettingsCoordinator';
import {
  DesktopHomeWorkspaceProvider,
  useDesktopHomeWorkspace,
} from './home/DesktopHomeWorkspaceContext';
import { DesktopHomeView } from './home/DesktopHomeView';
import {
  normalizeSessionOpenMode,
  type SessionOpenMode,
} from './settings/desktopGlobalSettings';
import { DesktopConnectionSessionStatusReader } from './status/DesktopConnectionSessionStatusReader';
import {
  deriveDesktopStatusSessionIds,
  type VisibleSessionsStatusScope,
} from './status/desktopStatusScope';
import {
  clearSessionNoteWindowFromSystem,
  openSessionNoteWindow,
} from './windows/sessionNoteCoordinator';

const EMPTY_CACHED_SESSIONS: SessionSummary[] = [];

const DEFAULT_CONNECTION_ROW_CLICK_BEHAVIOR = 'focusAndOpen' as const;

function buildTabId(connectionId: string, sessionId: string): string {
  return `${connectionId}:${sessionId}`;
}

function stringArraysEqual(
  left: readonly string[],
  right: readonly string[],
): boolean {
  return (
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  );
}

export interface DesktopRootProps {
  initialTabStripStyle?: TabStripStyle;
  initialSessionsFollowActiveTabEnabled?: boolean;
  initialMarkdownBaseFontSize?: MarkdownBaseFontSize;
  initialMarkdownHeaderSize?: MarkdownHeaderSize;
  initialRecentSessionsWindow?: RecentSessionsWindow;
  initialSessionDoubleClickAction?: SessionOpenMode;
}

export function DesktopRoot(props: DesktopRootProps): React.JSX.Element {
  return (
    <DesktopHomeWorkspaceProvider store={asyncStorageKeyValueStore}>
      <DesktopRootInner {...props} />
    </DesktopHomeWorkspaceProvider>
  );
}

function DesktopRootInner({
  initialTabStripStyle,
  initialSessionsFollowActiveTabEnabled,
  initialMarkdownBaseFontSize,
  initialMarkdownHeaderSize,
  initialRecentSessionsWindow,
  initialSessionDoubleClickAction,
}: DesktopRootProps): React.JSX.Element {
  const baseTheme = useTheme();

  const [tabStripStyle, setTabStripStyle] = useState<TabStripStyle>(
    parseTabStripStyle(initialTabStripStyle) ?? DEFAULT_TAB_STRIP_STYLE,
  );

  const [sessionsFollowActiveTabEnabled, setSessionsFollowActiveTabEnabled] =
    useState<boolean>(
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
    () =>
      applyDisplayTypographyPreset(
        baseTheme,
        markdownDisplayPreferences.baseFontSize,
      ),
    [baseTheme, markdownDisplayPreferences.baseFontSize],
  );
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [recentSessionsWindow, setRecentSessionsWindow] =
    useState<RecentSessionsWindow>(
      normalizeRecentSessionsWindow(initialRecentSessionsWindow),
    );
  const [sessionDoubleClickAction, setSessionDoubleClickAction] =
    useState<SessionOpenMode>(
      normalizeSessionOpenMode(initialSessionDoubleClickAction),
    );
  const [foreground, setForeground] = useState(
    AppState.currentState === 'active',
  );
  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => {
      setForeground(state === 'active');
    });
    return () => subscription.remove();
  }, []);
  const {
    watchlist,
    notes,
    addToWatchlist,
    removeFromWatchlist,
    moveWatchlistItem,
    removeConnectionFromWatchlist,
    setSessionNote,
    removeSessionNote,
  } = useDesktopHomeWorkspace();

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

  const [focusedConnectionId, setFocusedConnectionId] = useState<string | null>(
    null,
  );
  const [workspace, dispatchWorkspace] = useReducer(
    desktopWorkspaceReducer,
    INITIAL_DESKTOP_WORKSPACE_STATE,
  );
  const tabs = useMemo(() => getDesktopWorkspaceTabs(workspace), [workspace]);
  const activeTab = useMemo(
    () => getActiveDesktopSessionTab(workspace),
    [workspace],
  );
  const activeTabId =
    workspace.activeWorkspace.kind === 'session'
      ? workspace.activeWorkspace.tabId
      : null;
  const [tabsHydrated, setTabsHydrated] = useState(false);
  const [sessionReopenIntentVersion, setSessionReopenIntentVersion] =
    useState(0);
  const lastSessionReopenAttemptRef = useRef<string | null>(null);
  const [didAutoOpenMostRecent, setDidAutoOpenMostRecent] = useState(false);
  const [connectionsVisible, setConnectionsVisible] = useState(true);
  const [lowerPanel, setLowerPanel] = useState<DesktopLowerPanel>('sessions');
  const [visibleSessionsStatusScope, setVisibleSessionsStatusScope] =
    useState<VisibleSessionsStatusScope>({
      connectionId: null,
      sessionIds: [],
    });

  const lastValidatedOpenedAtByConnectionRef = useRef<Record<string, number>>(
    {},
  );
  const validatingConnectionIdsRef = useRef<Set<string>>(new Set());

  const openTab = useCallback(
    ({
      connectionId,
      sessionId,
      title,
      subtitle,
      mode = 'open',
    }: {
      connectionId: string;
      sessionId: string;
      title?: string;
      subtitle?: string | null;
      mode?: SessionOpenMode;
    }) => {
      const tabId = buildTabId(connectionId, sessionId);
      dispatchWorkspace({
        type: mode === 'preview' ? 'openPreview' : 'openPermanent',
        tab: {
          tabId,
          connectionId,
          sessionId,
          title: title ?? sessionId,
          subtitle: subtitle ?? null,
        },
      });
      setSessionReopenIntentVersion(current => current + 1);
    },
    [],
  );

  const updateOpenTabsPresentation = useCallback(
    (params: {
      connectionId: string;
      presentations: Record<string, { title: string; subtitle: string | null }>;
    }) => {
      dispatchWorkspace({
        type: 'updatePresentations',
        connectionId: params.connectionId,
        presentations: params.presentations,
      });
    },
    [],
  );

  const closeTab = useCallback((tabId: string) => {
    dispatchWorkspace({ type: 'closeTab', tabId });
  }, []);

  const focusTab = useCallback((tabId: string) => {
    dispatchWorkspace({ type: 'selectTab', tabId });
    setSessionReopenIntentVersion(current => current + 1);
  }, []);
  const promotePreview = useCallback((tabId?: string) => {
    dispatchWorkspace({ type: 'promotePreview', tabId });
  }, []);

  useEffect(() => {
    let cancelled = false;

    const hydrateTabs = async () => {
      try {
        const raw = await asyncStorageKeyValueStore.get(STORAGE_KEY_OPEN_TABS);
        const parsed = parsePersistedOpenTabsState(raw);
        if (!parsed || cancelled) {
          return;
        }
        dispatchWorkspace({ type: 'hydrate', state: parsed });
        const restoredActive = getActiveDesktopSessionTab(parsed);
        if (restoredActive) {
          setFocusedConnectionId(restoredActive.connectionId);
        }
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
    if (!tabsHydrated) return;
    void asyncStorageKeyValueStore
      .set(STORAGE_KEY_OPEN_TABS, serializePersistedOpenTabsState(workspace))
      .catch(() => {});
  }, [tabsHydrated, workspace]);

  useEffect(() => {
    if (!connectionsHydrated) return;

    if (
      focusedConnectionId &&
      sortedConnectionRecords.some(record => record.id === focusedConnectionId)
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
    if (!connectionsHydrated || !tabsHydrated || !activeTab) return;
    const attemptKey = `${activeTab.tabId}:${sessionReopenIntentVersion}`;
    if (lastSessionReopenAttemptRef.current === attemptKey) return;
    lastSessionReopenAttemptRef.current = attemptKey;
    const record = sortedConnectionRecords.find(
      candidate => candidate.id === activeTab.connectionId,
    );
    if (!record) return;
    setFocusedConnectionId(record.id);
    const openState = openConnectionsById[record.id];
    if (openState?.status === 'open' || openState?.status === 'connecting') {
      return;
    }
    void openConnectionAndTouch(record);
  }, [
    activeTab,
    connectionsHydrated,
    openConnectionAndTouch,
    openConnectionsById,
    sessionReopenIntentVersion,
    sortedConnectionRecords,
    tabsHydrated,
  ]);

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

    const validConnectionIds = new Set(
      sortedConnectionRecords.map(record => record.id),
    );
    const removedConnectionIds = new Set(
      tabs
        .filter(tab => !validConnectionIds.has(tab.connectionId))
        .map(tab => tab.connectionId),
    );
    for (const connectionId of removedConnectionIds) {
      dispatchWorkspace({ type: 'removeConnection', connectionId });
    }
  }, [connectionsHydrated, sortedConnectionRecords, tabs, tabsHydrated]);

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

      const openedAt =
        typeof openState.lastOpenedAt === 'number' ? openState.lastOpenedAt : 0;
      if (!openedAt) {
        continue;
      }

      if (
        lastValidatedOpenedAtByConnectionRef.current[connectionId] === openedAt
      ) {
        continue;
      }

      if (validatingConnectionIdsRef.current.has(connectionId)) {
        continue;
      }

      lastValidatedOpenedAtByConnectionRef.current[connectionId] = openedAt;
      validatingConnectionIdsRef.current.add(connectionId);

      const backend = openState.backend;
      const tabsForConnection = tabs.filter(
        tab => tab.connectionId === connectionId,
      );
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
              const message =
                typeof err?.message === 'string' ? err.message : '';
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

    const savedSub = desktopWindowEvents.addListener(
      'connectionEditorSaved',
      (payload: any) => {
        const record = payload?.record;
        if (
          !record ||
          typeof record !== 'object' ||
          typeof record.id !== 'string'
        ) {
          return;
        }
        upsertConnection(record);
        setFocusedConnectionId(record.id);
        openConnectionAndTouch(record);
      },
    );

    const styleSub = desktopWindowEvents.addListener(
      'tabStripStyleChanged',
      (payload: any) => {
        const style = parseTabStripStyle(payload?.style);
        if (!style) {
          return;
        }
        setTabStripStyle(style);
      },
    );

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
        setMarkdownDisplayPreferences(current => ({
          ...current,
          baseFontSize: normalizeMarkdownBaseFontSize(payload?.baseFontSize),
        }));
      },
    );

    const markdownHeaderSizeSub = desktopWindowEvents.addListener(
      'markdownHeaderSizeChanged',
      (payload: any) => {
        setMarkdownDisplayPreferences(current => ({
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
        dispatchWorkspace({ type: 'clear' });
      },
    );

    const recentSessionsWindowSub = desktopWindowEvents.addListener(
      'recentSessionsWindowChanged',
      (payload: any) => {
        setRecentSessionsWindow(
          normalizeRecentSessionsWindow(payload?.recentSessionsWindow),
        );
      },
    );

    const sessionDoubleClickActionSub = desktopWindowEvents.addListener(
      'sessionDoubleClickActionChanged',
      (payload: any) => {
        setSessionDoubleClickAction(
          normalizeSessionOpenMode(payload?.sessionDoubleClickAction),
        );
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
          .then(resp => {
            const sessionId = resp?.session?.session_id;
            if (typeof sessionId !== 'string' || !sessionId) {
              return;
            }
            openTab({
              connectionId: pickedConnectionId,
              sessionId,
              title: `Session ${sessionId.slice(0, 8)}`,
            });
            desktopEventBus.publish('sessionsReloadRequested', {
              connectionId: pickedConnectionId,
              reason: 'sessionCreated',
            });

            backend
              .listSessions()
              .then(sessions => {
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
      payload => {
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
        if (windowKey === 'actionDisplay') {
          dismissActiveActionDisplayWindowFromSystem();
        }
        if (windowKey === 'sessionNote') {
          clearSessionNoteWindowFromSystem();
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
      recentSessionsWindowSub.remove();
      sessionDoubleClickActionSub.remove();
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
    sortedConnectionRecords.forEach(record => {
      map[record.id] = record.name;
    });
    return map;
  }, [sortedConnectionRecords]);

  const homeCollections = useMemo(
    () =>
      deriveHomeSessionCollections({
        connections: sortedConnectionRecords,
        sessionsCache,
        watchlist,
        notes,
        recentSessionsWindow,
      }),
    [
      notes,
      recentSessionsWindow,
      sessionsCache,
      sortedConnectionRecords,
      watchlist,
    ],
  );

  const statusSessionIdsByConnection = useMemo(
    () =>
      deriveDesktopStatusSessionIds({
        tabs,
        homeActive: workspace.activeWorkspace.kind === 'home',
        homeCollections,
        lowerPanel,
        focusedConnectionId,
        visibleSessions: visibleSessionsStatusScope,
      }),
    [
      focusedConnectionId,
      homeCollections,
      lowerPanel,
      tabs,
      visibleSessionsStatusScope,
      workspace.activeWorkspace.kind,
    ],
  );

  const handleVisibleSessionIdsChange = useCallback(
    (next: { connectionId: string | null; sessionIds: readonly string[] }) => {
      setVisibleSessionsStatusScope(current =>
        current.connectionId === next.connectionId &&
        stringArraysEqual(current.sessionIds, next.sessionIds)
          ? current
          : {
              connectionId: next.connectionId,
              sessionIds: [...next.sessionIds],
            },
      );
    },
    [],
  );

  const statusReader = useMemo(
    () => new DesktopConnectionSessionStatusReader(getBackend),
    [getBackend],
  );
  const requestStatuses = useSessionRequestStatuses({
    active: connectionsHydrated && foreground,
    connections: sortedConnectionRecords,
    sessionIdsByConnection: statusSessionIdsByConnection,
    reader: statusReader,
  });

  const openCollectionSession = useCallback(
    (item: HomeSessionItem, mode: SessionOpenMode) => {
      const presentation = item.summary.presentation;
      setFocusedConnectionId(item.connectionId);
      openTab({
        connectionId: item.connectionId,
        sessionId: item.sessionId,
        title:
          presentation?.title ||
          item.summary.preview ||
          item.summary.session_id,
        subtitle: presentation?.subtitle ?? item.connection.name,
        mode,
      });
    },
    [openTab],
  );

  const editCollectionNote = useCallback(
    (item: HomeSessionItem) => {
      openSessionNoteWindow({
        id: `session-note:${item.sessionId}`,
        sessionId: item.sessionId,
        title:
          item.summary.presentation?.title ||
          item.summary.preview ||
          item.sessionId,
        initialNote: notes[item.sessionId] ?? '',
        onSave: note => setSessionNote(item.sessionId, note),
        onRemove: () => removeSessionNote(item.sessionId),
      });
    },
    [notes, removeSessionNote, setSessionNote],
  );

  const openNewConnectionEditor = useCallback(() => {
    DesktopWindowManager?.openConnectionEditor({ mode: 'new' });
  }, []);

  const openEditConnectionEditor = useCallback((record: ConnectionRecord) => {
    DesktopWindowManager?.openConnectionEditor({
      mode: 'edit',
      initialRecord: record,
    });
  }, []);

  const handleClearConnections = useCallback(() => {
    for (const record of sortedConnectionRecords) {
      removeConnectionFromWatchlist(record.id);
    }
    clearConnections();
    closeAllConnections();
    clearSessionsCache();
    clearMessagesCache();
    setFocusedConnectionId(null);
    dispatchWorkspace({ type: 'clear' });
  }, [
    clearConnections,
    clearMessagesCache,
    clearSessionsCache,
    closeAllConnections,
    removeConnectionFromWatchlist,
    sortedConnectionRecords,
  ]);

  const handleDeleteConnection = useCallback(
    (id: string) => {
      closeConnection(id);
      deleteConnection(id);
      deleteConnectionSessionsCache(id);
      deleteConnectionMessagesCache(id);
      dispatchWorkspace({ type: 'removeConnection', connectionId: id });
      removeConnectionFromWatchlist(id);
      setFocusedConnectionId(prev => (prev === id ? null : prev));
    },
    [
      closeConnection,
      deleteConnection,
      deleteConnectionMessagesCache,
      deleteConnectionSessionsCache,
      removeConnectionFromWatchlist,
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
              activityRail={
                <DesktopActivityRail
                  connectionsVisible={connectionsVisible}
                  lowerPanel={lowerPanel}
                  onToggleConnections={() =>
                    setConnectionsVisible(current => !current)
                  }
                  onSelectLowerPanel={setLowerPanel}
                />
              }
              panel={
                <View style={styles.leftColumn}>
                  {connectionsVisible ? (
                    <ConnectionsPanel
                      connectionRecords={sortedConnectionRecords}
                      focusedConnectionId={focusedConnectionId}
                      openConnectionsById={openConnectionsById}
                      rowClickBehavior={DEFAULT_CONNECTION_ROW_CLICK_BEHAVIOR}
                      onFocusConnection={id => setFocusedConnectionId(id)}
                      onOpenConnection={record => {
                        setFocusedConnectionId(record.id);
                        openConnectionAndTouch(record);
                      }}
                      onCloseConnection={id => closeConnection(id)}
                      onDeleteConnection={handleDeleteConnection}
                      onClearConnections={handleClearConnections}
                      onOpenNewConnectionEditor={openNewConnectionEditor}
                      onOpenEditConnectionEditor={openEditConnectionEditor}
                    />
                  ) : null}

                  {lowerPanel === 'sessions' ? (
                    <SessionsPanel
                      focusedConnectionId={focusedConnectionId}
                      focusedConnectionName={
                        focusedConnectionId
                          ? connectionNameById[focusedConnectionId]
                          : null
                      }
                      connectionBaseUrl={
                        focusedConnectionId
                          ? openConnectionsById[focusedConnectionId]?.baseUrl ??
                            null
                          : null
                      }
                      connectionId={focusedConnectionId}
                      backend={
                        focusedConnectionId
                          ? getBackend(focusedConnectionId)
                          : null
                      }
                      isOnline={
                        focusedConnectionId
                          ? openConnectionsById[focusedConnectionId]?.status ===
                            'open'
                          : false
                      }
                      cachedSessions={
                        focusedConnectionId
                          ? sessionsCache[focusedConnectionId]?.sessions ??
                            EMPTY_CACHED_SESSIONS
                          : EMPTY_CACHED_SESSIONS
                      }
                      cachedLastLoadedAt={
                        focusedConnectionId
                          ? sessionsCache[focusedConnectionId]?.lastLoadedAt ??
                            null
                          : null
                      }
                      activeTabId={activeTabId}
                      activeTabConnectionId={activeTab?.connectionId ?? null}
                      activeTabSessionId={activeTab?.sessionId ?? null}
                      followActiveTabEnabled={sessionsFollowActiveTabEnabled}
                      onUpdateCache={updateSessionsCache}
                      onOpenSessionTab={openTab}
                      onUpdateOpenTabsPresentation={updateOpenTabsPresentation}
                      sessionDoubleClickAction={sessionDoubleClickAction}
                      requestStatuses={
                        focusedConnectionId
                          ? requestStatuses[focusedConnectionId] ?? {}
                          : {}
                      }
                      onVisibleSessionIdsChange={handleVisibleSessionIdsChange}
                      sessionNotes={notes}
                      onEditSessionNote={({ sessionId, title }) =>
                        openSessionNoteWindow({
                          id: `session-note:${sessionId}`,
                          sessionId,
                          title,
                          initialNote: notes[sessionId] ?? '',
                          onSave: note => setSessionNote(sessionId, note),
                          onRemove: () => removeSessionNote(sessionId),
                        })
                      }
                    />
                  ) : (
                    <HistoryPanel
                      collections={homeCollections}
                      statuses={requestStatuses}
                      doubleClickAction={sessionDoubleClickAction}
                      onOpenSession={openCollectionSession}
                      onToggleWatch={(item, watched) =>
                        watched
                          ? removeFromWatchlist(
                              item.connectionId,
                              item.sessionId,
                            )
                          : addToWatchlist(item.connectionId, item.sessionId)
                      }
                      onEditNote={editCollectionNote}
                    />
                  )}
                </View>
              }
              main={
                <View style={styles.mainColumn}>
                  <SessionTabs
                    permanentTabs={workspace.permanentTabs}
                    previewTab={workspace.previewTab}
                    homeActive={workspace.activeWorkspace.kind === 'home'}
                    activeTabId={activeTabId}
                    styleVariant={tabStripStyle}
                    connectionNameById={connectionNameById}
                    requestStatuses={requestStatuses}
                    onSelectHome={() =>
                      dispatchWorkspace({ type: 'selectHome' })
                    }
                    onSelectTab={focusTab}
                    onCloseTab={closeTab}
                    onPromotePreview={promotePreview}
                    onReorderPermanent={(fromIndex, toIndex) =>
                      dispatchWorkspace({
                        type: 'reorderPermanent',
                        fromIndex,
                        toIndex,
                      })
                    }
                  />

                  <View
                    style={[
                      styles.mainContent,
                      tabStripStyle === 'codeTabs' ||
                      tabStripStyle === 'underlineTabs'
                        ? styles.mainContentCodeLike
                        : styles.mainContentCardLike,
                    ]}
                  >
                    <View style={styles.workspaceHost}>
                      {tabs.length > 0 ? (
                        <View style={styles.workspaceLayer}>
                          <ChatPaneTabStack
                            tabs={tabs}
                            activeTabId={activeTabId}
                            workspaceVisible={
                              workspace.activeWorkspace.kind === 'session' &&
                              activeTab !== null
                            }
                            styleVariant={tabStripStyle}
                            connectionNameById={connectionNameById}
                            getBackend={getBackend}
                            sessionsCache={sessionsCache}
                            messagesCache={messagesCache}
                            messagesCacheHydrated={messagesCacheHydrated}
                            requestStatuses={requestStatuses}
                            onUpdateCache={updateMessagesCache}
                            onOpenSessionTab={openTab}
                            onPromotePreview={promotePreview}
                          />
                        </View>
                      ) : null}

                      {workspace.activeWorkspace.kind === 'home' ? (
                        <View style={styles.workspaceLayer}>
                          <DesktopHomeView
                            collections={homeCollections}
                            statuses={requestStatuses}
                            doubleClickAction={sessionDoubleClickAction}
                            onOpenSession={openCollectionSession}
                            onToggleWatch={(item, watched) =>
                              watched
                                ? removeFromWatchlist(
                                    item.connectionId,
                                    item.sessionId,
                                  )
                                : addToWatchlist(
                                    item.connectionId,
                                    item.sessionId,
                                  )
                            }
                            onEditNote={editCollectionNote}
                            onMoveWatchlistItem={moveWatchlistItem}
                          />
                        </View>
                      ) : !activeTab ? (
                        <View style={styles.workspaceLayer}>
                          <ChatPanePlaceholder
                            visible
                            title="No sessions open"
                            subtitle="Select a session from the left to open it in a tab."
                            styleVariant={tabStripStyle}
                          />
                        </View>
                      ) : null}
                    </View>
                  </View>
                </View>
              }
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
    workspaceHost: {
      flex: 1,
    },
    workspaceLayer: {
      ...StyleSheet.absoluteFillObject,
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
