import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  ActionsMenuBar,
  ApplicationActionDialog,
  useTheme,
  type ActionDefinition,
  type ActionKey,
} from '@crystal-lattice/frontend-rn-components';

import type {
  ActionUiElement,
  AgentBackend,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import {
  deriveSessionListPresentationFromGroups,
  groupSessionListFields,
  runApplicationAction,
} from '@crystal-lattice/frontend-sdk';

import {
  ApplicationPluginsProvider,
  useAgentsController,
  useApplicationPlugins,
  useHydrateControllerFromCache,
  usePersistentPinnedActions,
  usePluginActionDialog,
  useSessionsController,
} from '@crystal-lattice/frontend-sdk-react';

import { asyncStorageKeyValueStore } from '../storage/asyncStorageKeyValueStore';
import { desktopEventBus } from '../events/desktopEventBus';
import { PanelHeader } from '../ui/PanelHeader';
import { DesktopWindowManager } from '../windows/desktopWindowManager';
import { useMacOSApplicationActionDialog } from '../windows/useMacOSApplicationActionDialog';
import { truncateByChars } from '../utils/text';
import { useSessionsPanelTabAutoSelect } from './useSessionsPanelTabAutoSelect';

const PINNED_SESSION_LIST_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_session_list_actions_v1';
const SESSION_DOUBLE_CLICK_MS = 300;
const SESSIONS_STALE_MS = 30_000;
const DEFAULT_PINNED_SESSION_LIST_ACTION_KEYS: ActionKey[] = [];

export interface SessionsPanelProps {
  focusedConnectionId: string | null;
  focusedConnectionName: string | null;
  connectionId: string | null;
  backend: AgentBackend | null;
  cachedSessions: SessionSummary[];
  cachedLastLoadedAt: number | null;
  isOnline: boolean;
  activeTabId?: string | null;
  activeTabConnectionId?: string | null;
  activeTabSessionId?: string | null;
  followActiveTabEnabled?: boolean;
  onUpdateCache: (connectionId: string, sessions: SessionSummary[]) => void;
  onOpenSessionTab: (params: {
    connectionId: string;
    sessionId: string;
    title?: string;
    subtitle?: string | null;
  }) => void;

  onUpdateOpenTabsPresentation?: (params: {
    connectionId: string;
    presentations: Record<string, { title: string; subtitle: string | null }>;
  }) => void;
}

export function SessionsPanel(props: SessionsPanelProps): React.JSX.Element {
  return (
    <ApplicationPluginsProvider backend={props.backend} connectionId={props.connectionId}>
      <SessionsPanelInner {...props} />
    </ApplicationPluginsProvider>
  );
}

function SessionsPanelInner({
  focusedConnectionId,
  focusedConnectionName,
  connectionId,
  backend,
  cachedSessions,
  cachedLastLoadedAt,
  isOnline,
  activeTabId,
  activeTabConnectionId,
  activeTabSessionId,
  followActiveTabEnabled = true,
  onUpdateCache,
  onOpenSessionTab,
  onUpdateOpenTabsPresentation,
}: SessionsPanelProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const {
    controller: sessionsController,
    state: sessionsState,
  } = useSessionsController({
    backend,
    initialSessions: cachedSessions,
    limit: 50,
  });

  const hydrateFromCache = useCallback(
    (
      controller: NonNullable<typeof sessionsController>,
      cache: { sessions: SessionSummary[]; lastLoadedAt: number | null },
    ) => {
      controller.hydrateFromCache(cache);
    },
    [],
  );

  useHydrateControllerFromCache({
    controller: sessionsController,
    cache: { sessions: cachedSessions, lastLoadedAt: cachedLastLoadedAt },
    hydrate: hydrateFromCache,
  });

  const sessionsSnapshot = sessionsState;
  const sessionsLoading = sessionsSnapshot?.loading ?? false;
  const controllerError = sessionsSnapshot?.error ?? null;

  const shouldPreferControllerSessions =
    sessionsSnapshot?.lastLoadedAt != null ||
    (sessionsSnapshot?.sessions != null && sessionsSnapshot.sessions.length > 0);

  const sessions = shouldPreferControllerSessions
    ? sessionsSnapshot?.sessions ?? []
    : cachedSessions;

  const [filterText, setFilterText] = useState('');
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);

  const subtitle = useMemo(() => {
    if (!focusedConnectionName) {
      return 'No focused connection';
    }
    const cachedLabel =
      cachedLastLoadedAt != null
        ? `cached ${new Date(cachedLastLoadedAt).toLocaleTimeString()}`
        : 'no cache';
    const liveLabel = isOnline ? 'online' : 'offline';
    return `Focused: ${focusedConnectionName} • ${liveLabel} • ${cachedLabel}`;
  }, [cachedLastLoadedAt, focusedConnectionName, isOnline]);

  const refreshSessions = useCallback(async () => {
    if (!connectionId) {
      return;
    }
    if (!sessionsController) {
      Alert.alert('No connection', 'Open a connection to refresh sessions.');
      return;
    }

    try {
      const list = await sessionsController.load({ force: true });
      onUpdateCache(connectionId, list);
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to load sessions');
    }
  }, [connectionId, onUpdateCache, sessionsController]);

  useEffect(() => {
    if (!connectionId) return;
    if (!sessionsController) return;
    if (!isOnline) return;

    sessionsController
      .loadIfStale({ staleMs: SESSIONS_STALE_MS })
      .then((list) => {
        if (list) {
          onUpdateCache(connectionId, list);
        }
      })
      .catch(() => {
      });
  }, [connectionId, isOnline, onUpdateCache, sessionsController]);

  useEffect(() => {
    if (!connectionId) return;
    return desktopEventBus.subscribe('sessionsReloadRequested', (payload) => {
      if (payload.connectionId !== connectionId) {
        return;
      }
      refreshSessions();
    });
  }, [connectionId, refreshSessions]);

  const {
    actionsById,
    sessionListActions,
    sessionListFields,
    sessionListPinnedToggles,
  } = useApplicationPlugins();

  const fieldGroups = useMemo(
    () => groupSessionListFields(sessionListFields || []),
    [sessionListFields],
  );

  const pinnedToggleElement = sessionListPinnedToggles[0] ?? null;

  const pluginActionDefs: ActionDefinition[] = useMemo(() => {
    return (sessionListActions || [])
      .map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
      }))
      .filter((def) => typeof def.key === 'string' && def.key);
  }, [sessionListActions]);

  const pinnedSessionListActionsStorageKey = useMemo(() => {
    return `${PINNED_SESSION_LIST_ACTIONS_STORAGE_KEY_BASE}:${connectionId ?? 'default'}`;
  }, [connectionId]);

  const {
    pinned: pinnedSessionListActionKeys,
    setPinned: setPinnedSessionListActionKeys,
  } = usePersistentPinnedActions<ActionKey>({
    store: asyncStorageKeyValueStore,
    key: pinnedSessionListActionsStorageKey,
    initialPinned: DEFAULT_PINNED_SESSION_LIST_ACTION_KEYS,
  });

  const [pluginActionRunning, setPluginActionRunning] = useState(false);

  const {
    activeElement: activePluginDialogElement,
    context: activePluginDialogContext,
    openForElement: openPluginDialogForElement,
    handleSubmit: handleSubmitPluginDialog,
    handleCancel: handleCancelPluginDialog,
  } = usePluginActionDialog<SessionSummary>(
    useCallback(
      async (
        element: ActionUiElement,
        session: SessionSummary,
        dialogValues: Record<string, any> | undefined,
      ) => {
        if (!backend || !connectionId) {
          Alert.alert('No connection', 'Connect to a server to run actions.');
          return;
        }

        setPluginActionRunning(true);
        try {
          const { ok, effects, errorMessage } = await runApplicationAction({
            backend,
            element,
            actionsById,
            context: {
              sessionId: session.session_id,
              sessionSummary: session,
              dialogValues,
            },
            effects: {
              reloadSessionsListOnMutations: true,
            },
          });

          if (!ok) {
            Alert.alert('Action error', errorMessage || 'Failed to execute action');
            return;
          }

          for (const effect of effects) {
            if (effect.type === 'navigateToSession') {
              onOpenSessionTab({
                connectionId,
                sessionId: effect.sessionId,
                title: effect.sessionId,
              });
              return;
            }
          }

          if (effects.some((effect) => effect.type === 'reloadSessionsList')) {
            desktopEventBus.publish('sessionsReloadRequested', {
              connectionId,
              reason: `action:${element.id}`,
            });
          }
        } finally {
          setPluginActionRunning(false);
        }
      },
      [actionsById, backend, connectionId, onOpenSessionTab],
    ),
  );

  const pluginDialogPrefillContext = useMemo(
    () => ({ session: activePluginDialogContext ?? undefined }),
    [activePluginDialogContext],
  );

  useMacOSApplicationActionDialog({
    ownerId: 'sessions-panel',
    activeElement: activePluginDialogElement,
    prefillContext: pluginDialogPrefillContext,
    onCancel: handleCancelPluginDialog,
    onSubmit: handleSubmitPluginDialog,
  });

  const { controller: agentsController, state: agentsState } = useAgentsController({
    backend,
    cacheKey: connectionId ?? 'default',
    enabled: false,
  });

  const [openingAgentPicker, setOpeningAgentPicker] = useState(false);
  const openAgentPickerWindow = useCallback(async () => {
    if (!backend || !connectionId) {
      Alert.alert('No connection', 'Open a connection to create a session.');
      return;
    }
    if (!agentsController) {
      Alert.alert('Error', 'Agent controller is not available.');
      return;
    }

    setOpeningAgentPicker(true);
    try {
      const agents = await agentsController.ensureLoaded();
      DesktopWindowManager?.openAgentPicker({
        connectionId,
        connectionName: focusedConnectionName ?? connectionId,
        agents,
      });
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to load agents');
    } finally {
      setOpeningAgentPicker(false);
    }
  }, [agentsController, backend, connectionId, focusedConnectionName]);

  const filteredSessions = useMemo(() => {
    const query = filterText.trim().toLowerCase();
    if (!query) {
      return sessions;
    }
    return sessions.filter((sessionSummary) => {
      if (sessionSummary.session_id.toLowerCase().includes(query)) return true;
      if ((sessionSummary.preview || '').toLowerCase().includes(query)) return true;
      const presentation = deriveSessionListPresentationFromGroups(sessionSummary, fieldGroups);
      if (presentation.title.toLowerCase().includes(query)) return true;
      if ((presentation.subtitle || '').toLowerCase().includes(query)) return true;
      if ((presentation.meta || '').toLowerCase().includes(query)) return true;
      return false;
    });
  }, [fieldGroups, filterText, sessions]);

  const {
    selectedSessionId,
    onUserSelectSessionId,
    scrollViewRef,
    getRowLayoutHandler,
  } = useSessionsPanelTabAutoSelect({
    connectionId,
    visibleSessionIds: filteredSessions.map((session) => session.session_id),
    activeTab: {
      tabId: typeof activeTabId === 'string' ? activeTabId : null,
      connectionId:
        typeof activeTabConnectionId === 'string' ? activeTabConnectionId : null,
      sessionId: typeof activeTabSessionId === 'string' ? activeTabSessionId : null,
    },
    enabled: followActiveTabEnabled,
  });

  const lastClickRef = useRef<{ sessionId: string; atMs: number } | null>(null);

  useEffect(() => {
    if (!connectionId) {
      return;
    }
    if (!onUpdateOpenTabsPresentation) {
      return;
    }
    const nextSessions = sessionsState?.sessions;
    if (!Array.isArray(nextSessions) || nextSessions.length === 0) {
      return;
    }

    const presentations: Record<string, { title: string; subtitle: string | null }> = {};
    for (const session of nextSessions) {
      if (!session || typeof session !== 'object') {
        continue;
      }
      const sessionId = (session as any).session_id;
      if (typeof sessionId !== 'string' || !sessionId) {
        continue;
      }
      const presentation = deriveSessionListPresentationFromGroups(session, fieldGroups);
      presentations[sessionId] = {
        title: presentation.title.slice(0, 64) || sessionId,
        subtitle: presentation.subtitle,
      };
    }

    onUpdateOpenTabsPresentation({ connectionId, presentations });
  }, [connectionId, fieldGroups, onUpdateOpenTabsPresentation, sessionsState?.sessions]);

  const openSession = useCallback(
    (session: SessionSummary) => {
      if (!connectionId) {
        return;
      }

      const presentation = deriveSessionListPresentationFromGroups(session, fieldGroups);
      onOpenSessionTab({
        connectionId,
        sessionId: session.session_id,
        title: presentation.title?.slice(0, 64) || session.session_id,
        subtitle: presentation.subtitle,
      });
    },
    [connectionId, fieldGroups, onOpenSessionTab],
  );

  const handleRowPress = useCallback(
    (session: SessionSummary) => {
      const now = Date.now();
      const prev = lastClickRef.current;
      lastClickRef.current = { sessionId: session.session_id, atMs: now };

      onUserSelectSessionId(session.session_id);

      if (prev && prev.sessionId === session.session_id && now - prev.atMs <= SESSION_DOUBLE_CLICK_MS) {
        openSession(session);
      }
    },
    [onUserSelectSessionId, openSession],
  );

  return (
    <View style={styles.root}>
      <PanelHeader
        title="Sessions"
        subtitle={subtitle}
        menuLabel="↻"
        onPressMenu={() => refreshSessions()}
      />

      <View style={styles.controlsRow}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search"
          placeholderTextColor={theme.textMuted}
          value={filterText}
          onChangeText={setFilterText}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <Pressable
          style={(state) => {
            const hovered = (state as any).hovered as boolean | undefined;
            const disabled = !isOnline || openingAgentPicker || (agentsState?.loading ?? false);
            return [
              styles.newButton,
              disabled && styles.newButtonDisabled,
              (hovered || state.pressed) && !disabled && styles.newButtonHovered,
            ];
          }}
          disabled={!isOnline || openingAgentPicker || (agentsState?.loading ?? false)}
          onPress={openAgentPickerWindow}
        >
          <Text style={styles.newButtonText}>{openingAgentPicker ? '…' : 'New'}</Text>
        </Pressable>
      </View>

      {(sessionsLoading || pluginActionRunning) && (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={theme.primary} />
          <Text style={styles.loadingText}>
            {pluginActionRunning ? 'Running action…' : 'Loading sessions…'}
          </Text>
        </View>
      )}

      {controllerError && !sessionsLoading ? (
        <Text style={styles.errorText}>{controllerError}</Text>
      ) : null}

      {!connectionId ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>Select a connection above.</Text>
        </View>
      ) : (
        <ScrollView
          ref={scrollViewRef}
          style={styles.list}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator
        >
          {filteredSessions.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>
                {filterText.trim() ? 'No sessions match your search.' : 'No sessions.'}
              </Text>
              {!isOnline ? (
                <Text style={styles.emptyMeta}>Open the connection to refresh.</Text>
              ) : null}
            </View>
          ) : null}

          {filteredSessions.map((session) => {
            const hovered = hoveredSessionId === session.session_id;
            const selected = selectedSessionId === session.session_id;
            const showRowControls = hovered;

            const presentation = deriveSessionListPresentationFromGroups(session, fieldGroups);
            const title = truncateByChars(
              presentation.title || session.preview || session.session_id,
              80,
            );
            const subtitle = truncateByChars(
              presentation.subtitle ?? session.preview ?? '',
              80,
            );
            const meta = presentation.meta;

            return (
              <Pressable
                key={session.session_id}
                style={(state) => {
                  const pressedOrHovered =
                    ((state as any).hovered as boolean | undefined) || state.pressed;
                  return [
                    styles.row,
                    selected && styles.rowSelected,
                    pressedOrHovered && styles.rowHovered,
                  ];
                }}
                onLayout={getRowLayoutHandler(session.session_id)}
                onPress={() => handleRowPress(session)}
                onHoverIn={() => setHoveredSessionId(session.session_id)}
                onHoverOut={() =>
                  setHoveredSessionId((prev) => (prev === session.session_id ? null : prev))
                }
              >
                <View style={styles.rowMain}>
                  <View style={styles.rowTitleRow}>
                    <Text style={styles.rowTitle}>{title}</Text>
                    {pinnedToggleElement ? (
                      <Pressable
                        style={(state) => {
                          const pinnedHovered = (state as any).hovered as boolean | undefined;
                          return [
                            styles.pinButton,
                            (pinnedHovered || state.pressed) && styles.pinButtonHovered,
                          ];
                        }}
                        disabled={!isOnline}
                        onPress={(event) => {
                          (event as any)?.stopPropagation?.();
                          if (!isOnline) {
                            return;
                          }
                          openPluginDialogForElement(pinnedToggleElement, session);
                        }}
                      >
                        <Text
                          style={[
                            styles.pinButtonText,
                            { color: session.pinned ? '#FFCC00' : theme.textSecondary },
                          ]}
                        >
                          ★
                        </Text>
                      </Pressable>
                    ) : null}
                  </View>
                  <Text style={styles.rowId} numberOfLines={1}>
                    {session.session_id}
                  </Text>
                  <Text style={styles.rowSubtitle}>{subtitle}</Text>
                  {meta ? (
                    <Text style={styles.rowMeta}>
                      {meta}
                    </Text>
                  ) : null}
                </View>



                <View style={styles.rowRight}>

                  <Pressable
                    style={[
                      styles.openButton,
                      styles.openButtonVisible,
                    ]}
                    pointerEvents={showRowControls ? 'auto' : 'none'}
                    onPress={(event) => {
                      (event as any)?.stopPropagation?.();
                      openSession(session);
                    }}
                  >
                    <Text style={styles.openButtonText}>Open</Text>
                  </Pressable>

                  {sessionListActions.length > 0 ? (
                    <View
                      style={[
                        styles.actionsContainer,
                        showRowControls || pinnedSessionListActionKeys.length > 0
                          ? null
                          : styles.actionsContainerHidden,
                      ]}
                      pointerEvents={
                        showRowControls || pinnedSessionListActionKeys.length > 0 ? 'auto' : 'none'
                      }
                    >
                      <ActionsMenuBar<ActionDefinition>
                        title="Session actions"
                        variant="dropdown"
                        renderIcon={({ name, size, color }) => (
                          <Icon name={name} size={size} color={color} />
                        )}
                        baseActions={[]}
                        extraActions={pluginActionDefs}
                        pinned={pinnedSessionListActionKeys}
                        onChangePinned={(next) => setPinnedSessionListActionKeys(next)}
                        onAction={(key: ActionKey) => {
                          const element = sessionListActions.find((el) => el.id === key);
                          if (element) {
                            openPluginDialogForElement(element, session);
                          }
                        }}
                        isActionDisabled={() => !isOnline || pluginActionRunning}
                      />
                    </View>
                  ) : null}


                </View>
              </Pressable>
            );
          })}
        </ScrollView>
      )}

      {Platform.OS === 'macos' ? null : (
        <ApplicationActionDialog
          visible={!!activePluginDialogElement}
          dialog={(activePluginDialogElement as any)?.dialog}
          titleFallback={activePluginDialogElement?.label}
          prefillContext={{ session: activePluginDialogContext }}
          onSubmit={(values) => handleSubmitPluginDialog(values)}
          onCancel={handleCancelPluginDialog}
        />
      )}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const separatorWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    controlsRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
    },
    searchInput: {
      flex: 1,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 7,
      fontSize: 12,
      color: theme.text,
      backgroundColor: theme.backgroundAlt,
    },
    newButton: {
      borderWidth: separatorWidth,
      borderColor: theme.primary,
      backgroundColor: theme.primary,
      borderRadius: 10,
      paddingHorizontal: 12,
      paddingVertical: 7,
      alignItems: 'center',
      justifyContent: 'center',
    },
    newButtonHovered: {
      opacity: 0.92,
    },
    newButtonDisabled: {
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
    },
    newButtonText: {
      fontSize: 12,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
    },
    loadingText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    errorText: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      fontSize: 12,
      color: theme.danger,
    },
    list: {
      flex: 1,
    },
    listContent: {
      paddingVertical: 6,
    },
    row: {
      flexDirection: 'column',
      alignItems: 'stretch',
      justifyContent: 'space-between',
      gap: 5,
      paddingHorizontal: 10,
      paddingVertical: 8,
    },
    rowHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    rowSelected: {
      backgroundColor: theme.primaryMuted,
    },
    rowMain: {
      flex: 1,
      gap: 2,
    },
    rowTitleRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      gap: 8,
    },
    rowTitle: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
      flexGrow: 1,
      flexShrink: 1,
    },
    rowId: {
      fontSize: 11,
      color: theme.textSecondary,
    },
    rowSubtitle: {
      fontSize: 11,
      color: theme.textSecondary,
    },
    rowMeta: {
      fontSize: 11,
      color: theme.textMuted,
    },
    rowRight: {
      flexDirection: 'row',
      alignItems: 'flex-end',
      justifyContent: 'flex-end',
      gap: 4,
    },
    openButton: {
      borderWidth: separatorWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 8,
      paddingVertical: 4,
      backgroundColor: theme.surface,
    },
    openButtonHidden: {
      opacity: 0,
    },
    openButtonVisible: {
      opacity: 1,
    },
    openButtonText: {
      fontSize: 11,
      fontWeight: '700',
      color: theme.primary,
    },
    actionsContainer: {
      minWidth: 44,
    },
    actionsContainerHidden: {
      opacity: 0,
    },
    pinButton: {
      paddingHorizontal: 4,
      paddingVertical: 4,
      borderRadius: 10,
    },
    pinButtonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    pinButtonText: {
      fontSize: 14,
      fontWeight: '800',
    },
    empty: {
      padding: 12,
      gap: 4,
    },
    emptyText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    emptyMeta: {
      fontSize: 11,
      color: theme.textMuted,
    },
  });
}
