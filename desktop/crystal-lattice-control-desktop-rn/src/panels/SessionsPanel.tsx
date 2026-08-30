import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { LayoutChangeEvent } from 'react-native';
import {
  ActivityIndicator,
  Alert,
  Clipboard,
  findNodeHandle,
  Linking,
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
  getLastActionsPopoverAnchorTag,
  SessionListActionsBar,
  SessionListRichActionControl,
  SessionListRichActionList,
  SessionListFiltersPanel,
  useTheme,
  type ActionDefinition,
} from '@crystal-lattice/frontend-rn-components';

import type {
  ActionDisplayFollowupAction,
  ActionUiElement,
  ActionDisplayPayload,
  AgentBackend,
  ApplicationActionUiElement,
  SessionSummary,
  RunActionContext,
  SessionListActionElement,
} from '@crystal-lattice/frontend-sdk';
import {
  applicationActionKey,
  deriveSessionListPresentationFromGroups,
  emitDisplayPresentation,
  getDefaultPinnedSessionListActionKeys,
  groupSessionListFields,
  normalizeActionDisplayForSurface,
  normalizeDisplayEnvelope,
  runApplicationAction,
  subscribeSessionsListRefreshInvalidations,
  selectSessionListRichActionForPlacement,
} from '@crystal-lattice/frontend-sdk';

import {
  ApplicationPluginsProvider,
  useAgentsController,
  useApplicationPlugins,
  useHydrateControllerFromCache,
  usePersistentPinnedActions,
  usePluginActionDialog,
  useSessionListFilters,
  useSessionsController,
} from '@crystal-lattice/frontend-sdk-react';

import { asyncStorageKeyValueStore } from '../storage/asyncStorageKeyValueStore';
import { desktopEventBus } from '../events/desktopEventBus';
import { PanelHeader } from '../ui/PanelHeader';
import { ActionResultModal } from '../ui/ActionResultModal';
import { ActionResultInlineCard } from '../ui/ActionResultInlineCard';
import { DesktopWindowManager } from '../windows/desktopWindowManager';
import {
  closeDesktopPopover,
  openDesktopPopover,
  updateActiveDesktopPopover,
} from '../windows/desktopPopoverCoordinator';
import { useMacOSApplicationActionDialog } from '../windows/useMacOSApplicationActionDialog';
import { truncateByChars } from '../utils/text';
import { useSessionsPanelTabAutoSelect } from './useSessionsPanelTabAutoSelect';
import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';

const PINNED_SESSION_LIST_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_session_list_actions_v1';
const PINNED_SESSIONS_HEADER_ACTIONS_STORAGE_KEY_BASE =
  'clc_pinned_sessions_header_actions_v1';
const SESSION_DOUBLE_CLICK_MS = 300;
const SESSIONS_STALE_MS = 30_000;
type ActionDisplayEntry = {
  key: string;
  display: ActionDisplayPayload;
  context: RunActionContext;
};

interface SessionsHeaderActionDefinition extends ActionDefinition {
  kind: 'builtin' | 'plugin';
  element?: ApplicationActionUiElement;
}

function createDisplayEntry(display: ActionDisplayPayload, context: RunActionContext): ActionDisplayEntry {
  const key =
    typeof display.display_id === 'string' && display.display_id
      ? display.display_id
      : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  return { key, display, context };
}

function upsertInlineDisplay(
  current: ActionDisplayEntry[],
  nextEntry: ActionDisplayEntry,
): ActionDisplayEntry[] {
  const displayId = nextEntry.display.display_id;
  if (typeof displayId === 'string' && displayId) {
    const existingIndex = current.findIndex((entry) => entry.display.display_id === displayId);
    if (existingIndex >= 0) {
      const updated = current.slice();
      updated[existingIndex] = nextEntry;
      return updated;
    }
  }
  return [...current, nextEntry];
}

export interface SessionsPanelProps {
  focusedConnectionId: string | null;
  focusedConnectionName: string | null;
  connectionBaseUrl?: string | null;
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
  connectionBaseUrl,
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

  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);
  const filterAnchorRef = useRef<any>(null);

  // Sliding window pagination for session list
  const INITIAL_WINDOW_SIZE = 50;
  const LOAD_MORE_INCREMENT = 50;
  const MAX_WINDOW_SIZE = 100;
  const [windowStart, setWindowStart] = useState(0);
  const [windowEnd, setWindowEnd] = useState(INITIAL_WINDOW_SIZE);

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
      return false;
    }
    if (!sessionsController) {
      Alert.alert('No connection', 'Open a connection to refresh sessions.');
      return false;
    }

    try {
      const list = await sessionsController.load({ force: true });
      onUpdateCache(connectionId, list);
      return true;
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to load sessions');
      return false;
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

  useEffect(() => {
    if (!backend) return;
    return subscribeSessionsListRefreshInvalidations(
      backend,
      refreshSessions,
    );
  }, [backend, refreshSessions]);

  const {
    actionsById,
    actionsByKey = {},
    applicationActions = [],
    sessionListActions,
    sessionListFields,
    sessionListFilterSchema,
  } = useApplicationPlugins();
  const {
    schema: effectiveFilterSchema,
    values: sessionFilterValues,
    mainSearch,
    searchText,
    nonMainFilters,
    activeNonMainFilterCount,
    setFilterValue,
    setSearchText,
    reset: resetSessionFilters,
    showAll: showAllSessions,
    filterSessions,
  } = useSessionListFilters({
    connectionId,
    schema: sessionListFilterSchema,
  });
  const filterPopoverId = useMemo(
    () =>
      `session-filters:${connectionId ?? 'default'}:${effectiveFilterSchema.identity}`,
    [connectionId, effectiveFilterSchema.identity],
  );
  const closeSessionFiltersPopover = useCallback(() => {
    closeDesktopPopover(filterPopoverId);
  }, [filterPopoverId]);
  const filterPopoverContent = useMemo(
    () => (
      <SessionListFiltersPanel
        schema={effectiveFilterSchema}
        values={sessionFilterValues}
        onChange={setFilterValue}
        onReset={resetSessionFilters}
        onShowAll={showAllSessions}
        onRequestClose={closeSessionFiltersPopover}
        renderIcon={({ name, size, color }) => (
          <Icon name={name} size={size} color={color} />
        )}
      />
    ),
    [
      closeSessionFiltersPopover,
      effectiveFilterSchema,
      resetSessionFilters,
      sessionFilterValues,
      setFilterValue,
      showAllSessions,
    ],
  );

  useEffect(() => {
    updateActiveDesktopPopover(filterPopoverId, {
      content: filterPopoverContent,
      onRequestClose: closeSessionFiltersPopover,
    });
  }, [
    closeSessionFiltersPopover,
    filterPopoverContent,
    filterPopoverId,
  ]);

  useEffect(
    () => () => {
      closeDesktopPopover(filterPopoverId);
    },
    [filterPopoverId],
  );

  const openSessionFiltersPopover = useCallback(() => {
    const anchorTag = filterAnchorRef.current
      ? (findNodeHandle(filterAnchorRef.current) as any)
      : null;
    const estimatedHeight = Math.max(
      260,
      Math.min(560, 150 + nonMainFilters.length * 120),
    );
    openDesktopPopover({
      id: filterPopoverId,
      content: filterPopoverContent,
      onRequestClose: closeSessionFiltersPopover,
      accessibilityId: 'session-filters-native-popover',
      anchorTag: typeof anchorTag === 'number' ? anchorTag : undefined,
      width: 380,
      height: estimatedHeight,
    });
  }, [
    closeSessionFiltersPopover,
    filterPopoverContent,
    filterPopoverId,
    nonMainFilters.length,
  ]);

  const fieldGroups = useMemo(
    () => groupSessionListFields(sessionListFields || []),
    [sessionListFields],
  );

  const pinnedSessionListActionsStorageKey = useMemo(() => {
    return `${PINNED_SESSION_LIST_ACTIONS_STORAGE_KEY_BASE}:${connectionId ?? 'default'}`;
  }, [connectionId]);
  const defaultPinnedSessionListActionKeys = useMemo(
    () => getDefaultPinnedSessionListActionKeys(sessionListActions),
    [sessionListActions],
  );

  const {
    pinned: pinnedSessionListActionKeys,
    setPinned: setPinnedSessionListActionKeys,
  } = usePersistentPinnedActions<string>({
    store: asyncStorageKeyValueStore,
    key: pinnedSessionListActionsStorageKey,
    initialPinned: defaultPinnedSessionListActionKeys,
  });
  const sessionsHeaderActionDefinitions = useMemo<SessionsHeaderActionDefinition[]>(
    () => [
      {
        key: 'serverSettings',
        label: 'Server settings',
        iconName: 'settings',
        kind: 'builtin',
      },
      {
        key: 'refreshSessions',
        label: 'Refresh sessions',
        iconName: 'refresh-cw',
        kind: 'builtin',
      },
      {
        key: 'newSession',
        label: 'New session',
        iconName: 'plus',
        kind: 'builtin',
      },
      ...applicationActions.map((element) => ({
        key: applicationActionKey(element.plugin, element.id),
        label: element.label,
        iconName: typeof element.icon === 'string' ? element.icon : 'zap',
        kind: 'plugin' as const,
        element,
      })),
    ],
    [applicationActions],
  );
  const {
    pinned: pinnedHeaderActionKeys,
    setPinned: setPinnedHeaderActionKeys,
  } = usePersistentPinnedActions<string>({
    store: asyncStorageKeyValueStore,
    key: `${PINNED_SESSIONS_HEADER_ACTIONS_STORAGE_KEY_BASE}:${connectionId ?? 'default'}`,
    initialPinned: ['serverSettings', 'refreshSessions', 'newSession'],
  });

  const [pluginActionRunning, setPluginActionRunning] = useState(false);
  const [actionResultDisplay, setActionResultDisplay] = useState<ActionDisplayEntry | null>(null);
  const [inlineActionDisplays, setInlineActionDisplays] = useState<ActionDisplayEntry[]>([]);
  const [activeDisplayActionId, setActiveDisplayActionId] = useState<string | null>(null);

  const presentActionDisplay = useCallback((display: ActionDisplayPayload, context: RunActionContext) => {
    const nextEntry = createDisplayEntry(display, context);
    if (backend) {
      emitDisplayPresentation(
        backend,
        normalizeDisplayEnvelope({
          id: nextEntry.key,
          source: 'action_response',
          ownershipScope: 'connection',
          connectionId,
          sessionId: context.sessionId,
          display,
        }),
      );
      return;
    }
    setActionResultDisplay(null);
    setInlineActionDisplays((current) => upsertInlineDisplay(current, nextEntry));
  }, [backend, connectionId]);

  const executePluginAction = useCallback(
    async (element: ActionUiElement, context: RunActionContext) => {
      if (!backend || !connectionId) {
        Alert.alert('No connection', 'Connect to a server to run actions.');
        return;
      }

      setPluginActionRunning(true);
      try {
        const { ok, effects, display, errorMessage } = await runApplicationAction({
          backend,
          element,
          actionsById,
          actionsByKey,
          context,
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
        const normalizedDisplay = normalizeActionDisplayForSurface({
          display,
          surface: 'session_list_action',
          host: 'desktop',
        });
        if (normalizedDisplay) {
          presentActionDisplay(normalizedDisplay, context);
        }
      } finally {
        setPluginActionRunning(false);
      }
    },
    [actionsById, actionsByKey, backend, connectionId, onOpenSessionTab, presentActionDisplay],
  );

  const openRichListPopover = useCallback(
    (element: SessionListActionElement, session: SessionSummary) => {
      const popoverId = [
        'session-rich-list',
        connectionId ?? 'default',
        session.session_id,
        element.id,
      ].join(':');
      const close = () => {
        closeDesktopPopover(popoverId);
      };
      const content = (
        <SessionListRichActionList
          element={element}
          session={session}
          testIDPrefix={`session-rich-list-${session.session_id}-${element.id}`}
          onRequestClose={close}
          onExecuteAction={(dialogValues) =>
            executePluginAction(element, {
              sessionId: session.session_id,
              sessionSummary: session,
              dialogValues,
            })
          }
          renderIcon={({ name, size, color }) => (
            <Icon name={name} size={size} color={color} />
          )}
        />
      );
      openDesktopPopover({
        id: popoverId,
        content,
        onRequestClose: close,
        accessibilityId: 'session-rich-list-native-popover',
        anchorTag: getLastActionsPopoverAnchorTag() ?? undefined,
        width: 300,
        height: 280,
      });
    },
    [connectionId, executePluginAction],
  );

  const handleDisplayFollowupAction = useCallback(
    async (
      entry: ActionDisplayEntry,
      action: ActionDisplayFollowupAction,
      formValues?: Record<string, any>,
    ) => {
      if (action.kind === 'open_url') {
        try {
          await Linking.openURL(action.url);
        } catch (err: any) {
          Alert.alert('Open link failed', err?.message || 'Unable to open the link.');
        }
        return;
      }
      if (action.kind === 'copy_text') {
        Clipboard.setString(action.text);
        Alert.alert('Copied', 'Copied to clipboard.');
        return;
      }
      if (action.kind === 'run_action') {
        if ((entry.display.presentation ?? 'modal') !== 'inline' && action.preserve_display !== true) {
          setActionResultDisplay((current) => (current?.key === entry.key ? null : current));
        }
        setActiveDisplayActionId(action.id);
        try {
          await executePluginAction(
            {
              ui_type: 'action_result_followup',
              plugin: action.plugin,
              id: action.id,
              label: action.label,
              action_id: action.action_id,
              action_owner: action.action_owner,
              fixed_params: action.fixed_params as Record<string, any> | undefined,
              param_map: action.param_map,
              form: entry.display.form,
            },
            {
              ...entry.context,
              formValues,
            },
          );
        } finally {
          setActiveDisplayActionId(null);
        }
      }
    },
    [executePluginAction],
  );

  const {
    activeElement: activePluginDialogElement,
    context: activePluginDialogContext,
    openForElement: openPluginDialogForElement,
    handleSubmit: handleSubmitPluginDialog,
    handleCancel: handleCancelPluginDialog,
  } = usePluginActionDialog<SessionSummary | null>(
    useCallback(
      async (
        element: ActionUiElement,
        session: SessionSummary | null,
        dialogValues: Record<string, any> | undefined,
      ) => {
        await executePluginAction(
          element,
          session
            ? {
                sessionId: session.session_id,
                sessionSummary: session,
                dialogValues,
              }
            : {
                connectionId: connectionId ?? undefined,
                dialogValues,
              },
        );
      },
      [connectionId, executePluginAction],
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

  const filteredSessions = useMemo(
    () => filterSessions(sessions),
    [filterSessions, sessions],
  );
  const hasActiveFilters =
    searchText !== '' || activeNonMainFilterCount > 0;

  useEffect(() => {
    setWindowStart(0);
    setWindowEnd(Math.min(INITIAL_WINDOW_SIZE, filteredSessions.length));
  }, [
    effectiveFilterSchema.identity,
    filteredSessions.length,
    sessionFilterValues,
    sessions.length,
  ]);

  // Show only visible window of filtered sessions
  const visibleSessions = filteredSessions.slice(windowStart, windowEnd);
  const hasMoreAtTop = windowStart > 0;
  const hasMoreAtBottom = windowEnd < filteredSessions.length;

  const {
    selectedSessionId,
    onUserSelectSessionId,
    scrollViewRef,
    getRowLayoutHandler,
    rowLayoutsRef,
  } = useSessionsPanelTabAutoSelect({
    connectionId,
    visibleSessionIds: visibleSessions.map((session) => session.session_id),
    activeTab: {
      tabId: typeof activeTabId === 'string' ? activeTabId : null,
      connectionId:
        typeof activeTabConnectionId === 'string' ? activeTabConnectionId : null,
      sessionId: typeof activeTabSessionId === 'string' ? activeTabSessionId : null,
    },
    enabled: followActiveTabEnabled,
  });

  // Store pending scroll adjustment to apply after render
  const pendingScrollAdjustmentRef = useRef<number | null>(null);

  // Measure actual top "Load more" button height for accurate scroll adjustment
  const topButtonHeightRef = useRef<number>(54); // Default fallback
  const handleTopButtonLayout = useCallback((event: LayoutChangeEvent) => {
    const height = event.nativeEvent?.layout?.height;
    if (typeof height === 'number' && height > 0) {
      topButtonHeightRef.current = height;
    }
  }, []);

  // Apply scroll adjustment after render (useLayoutEffect to block paint)
  useLayoutEffect(() => {
    if (pendingScrollAdjustmentRef.current !== null && scrollViewRef.current) {
      const newScrollY = pendingScrollAdjustmentRef.current;
      pendingScrollAdjustmentRef.current = null;
      scrollViewRef.current.scrollTo({ y: newScrollY, animated: false });
    }
  });

  // Load more at bottom - adds items at bottom, may remove from top to maintain max window
  const handleLoadMoreBottom = useCallback(async () => {
    const newEnd = Math.min(windowEnd + LOAD_MORE_INCREMENT, filteredSessions.length);
    const newStart = Math.max(0, newEnd - MAX_WINDOW_SIZE);

    // If we're removing items from top, calculate scroll adjustment to apply after render
    const itemsRemovedFromTop = newStart - windowStart;
    if (itemsRemovedFromTop > 0 && scrollViewRef.current) {
      // Find first row that will remain visible
      const firstKeptSessionId = filteredSessions[newStart]?.session_id;
      const layout = firstKeptSessionId ? rowLayoutsRef.current[firstKeptSessionId] : null;

      if (layout) {
        // This row is currently at `layout.y` pixels from the top of content
        // After removing items, it will be near the top, so we scroll up by `layout.y`
        const metrics = await getMacScrollViewMetrics(scrollViewRef.current);
        if (metrics) {
          let adjustment = metrics.offsetY - layout.y;
          // When there are hidden items, the "Load more" button at top is visible.
          // The row's layout.y was measured INCLUDING the button height, but the button
          // stays visible after the shift, so we need to add back the button height
          // to prevent the content from jumping up by that amount.
          // Use the measured actual height of the button container.
          if (newStart > 0) {
            // There will still be hidden items (and button) after the shift
            adjustment += topButtonHeightRef.current + 6;
          }
          pendingScrollAdjustmentRef.current = Math.max(0, adjustment);
        }
      }
    }

    setWindowEnd(newEnd);
    setWindowStart(newStart);
  }, [windowStart, windowEnd, filteredSessions, rowLayoutsRef, scrollViewRef]);

  // Load more at top - adds items at top, may remove from bottom to maintain max window
  const handleLoadMoreTop = useCallback(() => {
    const newStart = Math.max(0, windowStart - LOAD_MORE_INCREMENT);
    const newEnd = Math.min(filteredSessions.length, newStart + MAX_WINDOW_SIZE);
    setWindowStart(newStart);
    setWindowEnd(newEnd);
  }, [windowStart, filteredSessions.length]);

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
      {inlineActionDisplays.map((entry) => (
        <ActionResultInlineCard
          key={entry.key}
          display={entry.display}
          activeActionId={activeDisplayActionId}
          onDismiss={() =>
            setInlineActionDisplays((current) => current.filter((item) => item.key !== entry.key))
          }
          onFollowupAction={(action, formValues) =>
            handleDisplayFollowupAction(entry, action, formValues)
          }
        />
      ))}
      <ActionResultModal
        visible={!!actionResultDisplay}
        display={actionResultDisplay?.display ?? null}
        activeActionId={activeDisplayActionId}
        onRequestClose={() => setActionResultDisplay(null)}
        onFollowupAction={(action, formValues) => {
          if (!actionResultDisplay) return;
          handleDisplayFollowupAction(actionResultDisplay, action, formValues);
        }}
      />
      <PanelHeader
        title="Sessions"
        subtitle={subtitle}
        right={
          <ActionsMenuBar<SessionsHeaderActionDefinition>
            title="Sessions actions"
            variant="dropdown"
            isActive
            baseActions={sessionsHeaderActionDefinitions}
            pinned={pinnedHeaderActionKeys}
            onChangePinned={setPinnedHeaderActionKeys}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            renderPinIcon={({ size, color }) => (
              <Icon name="star" size={size} color={color} />
            )}
            menuButtonTestID="sessions-actions-menu"
            isActionDisabled={(key) =>
              !isOnline ||
              pluginActionRunning ||
              (key === 'refreshSessions' && sessionsLoading) ||
              (key === 'newSession' &&
                (openingAgentPicker || (agentsState?.loading ?? false)))
            }
            onAction={(key) => {
              if (key === 'serverSettings') {
                if (!backend || !connectionId) return;
                DesktopWindowManager?.openReactWindow({
                  windowKey: 'serverSettings',
                  moduleName: 'ServerSettingsWindow',
                  title: 'Server settings',
                  width: 560,
                  height: 640,
                  initialProps: {
                    connectionId,
                    connectionName: focusedConnectionName ?? connectionId,
                    baseUrl: connectionBaseUrl ?? undefined,
                  },
                });
                return;
              }
              if (key === 'refreshSessions') {
                void refreshSessions();
                return;
              }
              if (key === 'newSession') {
                void openAgentPickerWindow();
                return;
              }
              const element = sessionsHeaderActionDefinitions.find(
                (item) => item.key === key,
              )?.element;
              if (!element) return;
              if ((element.dialog?.kind ?? 'none') === 'none') {
                void executePluginAction(element, {
                  connectionId: connectionId ?? undefined,
                });
              } else {
                openPluginDialogForElement(element, null);
              }
            }}
          />
        }
      />

      <View style={styles.controlsRow}>
        <TextInput
          testID="session-main-search"
          accessibilityLabel={mainSearch.label}
          style={styles.searchInput}
          placeholder={mainSearch.label}
          placeholderTextColor={theme.textMuted}
          value={searchText}
          onChangeText={setSearchText}
          autoCapitalize="none"
          autoCorrect={false}
        />

        {nonMainFilters.length > 0 ? (
          <>
            <View ref={filterAnchorRef} collapsable={false}>
              <Pressable
                testID="session-filters-open"
                accessibilityLabel={
                  activeNonMainFilterCount > 0
                    ? `Open session filters, ${activeNonMainFilterCount} active`
                    : 'Open session filters'
                }
                accessibilityValue={
                  activeNonMainFilterCount > 0
                    ? { text: String(activeNonMainFilterCount) }
                    : undefined
                }
                style={(state) => {
                  const hovered = (state as any).hovered as boolean | undefined;
                  return [
                    styles.filterButton,
                    activeNonMainFilterCount > 0 && styles.filterButtonActive,
                    (hovered || state.pressed) && styles.filterButtonHovered,
                  ];
                }}
                onPress={openSessionFiltersPopover}
              >
                <Icon
                  name="filter"
                  size={15}
                  color={
                    activeNonMainFilterCount > 0
                      ? theme.primary
                      : theme.textSecondary
                  }
                />
                {activeNonMainFilterCount > 0 ? (
                  <Text
                    testID="session-filters-active-count"
                    style={styles.filterCount}
                  >
                    {activeNonMainFilterCount}
                  </Text>
                ) : null}
              </Pressable>
            </View>
          </>
        ) : null}

      </View>

      {sessionListFilterSchema.mainSearchConflict ? (
        <Text
          testID="session-filter-schema-warning"
          style={styles.filterWarning}
        >
          Multiple plugins declare the main session search. Using fallback search.
        </Text>
      ) : null}

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
          {hasMoreAtTop && (
            <View style={styles.loadMoreContainerTop} onLayout={handleTopButtonLayout}>
              <Pressable
                style={(state) => {
                  const hovered = (state as any).hovered as boolean | undefined;
                  return [
                    styles.loadMoreButton,
                    (hovered || state.pressed) && styles.loadMoreButtonHovered,
                  ];
                }}
                onPress={handleLoadMoreTop}
              >
                <Text style={styles.loadMoreButtonText}>
                  {windowStart} items hidden above
                </Text>
              </Pressable>
            </View>
          )}

          {visibleSessions.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>
                {sessions.length === 0
                  ? 'No sessions.'
                  : hasActiveFilters
                    ? 'No sessions match the active search or filters.'
                    : 'No sessions match the current filter defaults.'}
              </Text>
              {!isOnline ? (
                <Text style={styles.emptyMeta}>Open the connection to refresh.</Text>
              ) : null}
            </View>
          ) : null}

          {visibleSessions.map((session) => {
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
            const headerLeadingAction = selectSessionListRichActionForPlacement(
              sessionListActions,
              'header_leading',
            );
            const headerTrailingAction = selectSessionListRichActionForPlacement(
              sessionListActions,
              'header_trailing',
            );
            return (
              <Pressable
                key={session.session_id}
                testID={`session-row-${session.session_id}`}
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
                    {headerLeadingAction ? (
                      <SessionListRichActionControl
                        element={headerLeadingAction}
                        session={session}
                        placement="header_leading"
                        disabled={!isOnline || pluginActionRunning}
                        onExecuteAction={(element, dialogValues) =>
                          executePluginAction(element, {
                            sessionId: session.session_id,
                            sessionSummary: session,
                            dialogValues,
                          })
                        }
                        onPresentRichList={(element) =>
                          openRichListPopover(element, session)
                        }
                        renderIcon={({ name, size, color }) => (
                          <Icon name={name} size={size} color={color} />
                        )}
                        testID={`session-rich-header-${session.session_id}-header_leading-${headerLeadingAction.id}`}
                      />
                    ) : null}
                    <Text
                      style={styles.rowTitle}
                      testID={`session-title-${session.session_id}`}
                    >
                      {title}
                    </Text>
                    {headerTrailingAction ? (
                      <SessionListRichActionControl
                        element={headerTrailingAction}
                        session={session}
                        placement="header_trailing"
                        disabled={!isOnline || pluginActionRunning}
                        onExecuteAction={(element, dialogValues) =>
                          executePluginAction(element, {
                            sessionId: session.session_id,
                            sessionSummary: session,
                            dialogValues,
                          })
                        }
                        onPresentRichList={(element) =>
                          openRichListPopover(element, session)
                        }
                        renderIcon={({ name, size, color }) => (
                          <Icon name={name} size={size} color={color} />
                        )}
                        testID={`session-rich-header-${session.session_id}-header_trailing-${headerTrailingAction.id}`}
                      />
                    ) : null}
                  </View>
                  <Text
                    style={styles.rowId}
                    numberOfLines={1}
                    testID={`session-id-${session.session_id}`}
                  >
                    {session.session_id}
                  </Text>
                  <Text
                    style={styles.rowSubtitle}
                    testID={`session-subtitle-${session.session_id}`}
                  >
                    {subtitle}
                  </Text>
                  {meta ? (
                    <Text
                      style={styles.rowMeta}
                      testID={`session-meta-${session.session_id}`}
                    >
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
                      <SessionListActionsBar
                        session={session}
                        pluginActions={sessionListActions}
                        title="Session actions"
                        variant="dropdown"
                        menuButtonTestID={`session-actions-menu-${session.session_id}`}
                        renderIcon={({ name, size, color }) => (
                          <Icon name={name} size={size} color={color} />
                        )}
                        baseActions={[]}
                        pinned={pinnedSessionListActionKeys}
                        onChangePinned={(next) => setPinnedSessionListActionKeys(next)}
                        isActionDisabled={() => !isOnline || pluginActionRunning}
                        onBaseAction={() => {}}
                        onExecuteAction={(element, dialogValues) =>
                          executePluginAction(element, {
                            sessionId: session.session_id,
                            sessionSummary: session,
                            dialogValues,
                          })
                        }
                        onFallbackAction={(element) =>
                          openPluginDialogForElement(element, session)
                        }
                        onPresentRichList={(element) =>
                          openRichListPopover(element, session)
                        }
                      />
                    </View>
                  ) : null}
                </View>
              </Pressable>
            );
          })}

          {hasMoreAtBottom && (
            <View style={styles.loadMoreContainer}>
              <Pressable
                style={(state) => {
                  const hovered = (state as any).hovered as boolean | undefined;
                  return [
                    styles.loadMoreButton,
                    (hovered || state.pressed) && styles.loadMoreButtonHovered,
                  ];
                }}
                onPress={handleLoadMoreBottom}
              >
                <Text style={styles.loadMoreButtonText}>
                  {filteredSessions.length - windowEnd} items hidden below
                </Text>
              </Pressable>
            </View>
          )}
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
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.text,
      backgroundColor: theme.backgroundAlt,
    },
    filterButton: {
      width: 32,
      height: 32,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      borderRadius: 9,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.backgroundAlt,
    },
    filterButtonActive: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    filterButtonHovered: {
      opacity: 0.9,
    },
    filterCount: {
      position: 'absolute',
      right: 2,
      top: 0,
      color: theme.primary,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      fontWeight: '900',
    },
    filterWarning: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
      color: theme.danger,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
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
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
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
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    errorText: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
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
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '700',
      color: theme.text,
      flexGrow: 1,
      flexShrink: 1,
    },
    rowId: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    rowSubtitle: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      color: theme.textSecondary,
    },
    rowMeta: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
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
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
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
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '800',
    },
    empty: {
      padding: 12,
      gap: 4,
    },
    emptyText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    emptyMeta: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    loadMoreContainer: {
      paddingHorizontal: 12,
      paddingVertical: 12,
      alignItems: 'center',
    },
    loadMoreContainerTop: {
      paddingHorizontal: 12,
      paddingTop: 12,
      paddingBottom: 6,
      alignItems: 'center',
    },
    loadMoreButton: {
      borderWidth: separatorWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 16,
      paddingVertical: 10,
      backgroundColor: theme.surfaceAlt,
    },
    loadMoreButtonHovered: {
      backgroundColor: theme.surface,
    },
    loadMoreButtonText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '600',
      color: theme.textSecondary,
    },
  });
}

export { createStyles as createSessionsPanelStyles };
