import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Linking,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';
import Icon from 'react-native-vector-icons/Feather';
import {
  applicationActionKey,
  deriveSessionListPresentationFromGroups,
  emitDisplayPresentation,
  getDefaultPinnedSessionListActionKeys,
  groupSessionListFields,
  normalizeDisplayEnvelope,
  normalizeActionDisplayForSurface,
  pickDefaultAgentId,
  runApplicationAction,
  subscribeSessionsListRefreshInvalidations,
  selectSessionListRichActionForPlacement,
  type AgentBackend,
  type ApplicationActionUiElement,
  type RunActionContext,
  type SessionListActionElement,
  type SessionRequestStatus,
} from '@crystal-lattice/frontend-sdk';
import {
  ActionsMenuBar,
  ApplicationActionDialog,
  SessionListActionsBar,
  SessionListRichActionControl,
  SessionListRichActionList,
  SessionListFiltersPanel,
  ACTIONS_MENU_BAR_ITEM_WIDTH,
  ALL_SESSION_ACTIONS,
  type SessionActionKey,
  type SessionActionDefinition,
  type ActionDefinition,
} from '@crystal-lattice/frontend-rn-components';
import {
  useAgentsController,
  useHydrateControllerFromCache,
  useSessionListFilters,
  useSessionsController,
} from '@crystal-lattice/frontend-sdk-react';
import { useTheme, type Theme } from './theme';
import SessionSettingsModal from './components/SessionSettingsModal';
import ServerSettingsModal from './components/ServerSettingsModal';
import SessionPluginsModal from './components/SessionPluginsModal';
import {
  type ActionDisplayFollowupAction,
  type ActionUiElement,
  type ActionDisplayPayload,
  type SessionSummary,
} from './api';
import { useApplicationPlugins, useApplicationPluginsContext } from './ApplicationPluginsContext';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import { usePluginActionDialog } from './usePluginActionDialog';
import { handleGeneratedFileFollowupAction } from './utils/generatedFileActions';
import AgentSwitchModal from './components/AgentSwitchModal';
import ActionResultModal from './components/ActionResultModal';
import ActionResultInlineCard from './components/ActionResultInlineCard';
import { MobileDisplayHost } from './components/GlobalDisplayLayer';
import { useMobileApplicationActionDialogFieldRenderers } from './components/applicationActionDialogRenderers';
import { getMobileHeaderMaxPinnedActions } from './responsiveHeaderActions';
import { useHomeWorkspace } from './HomeWorkspaceContext';
import SessionNoteModal from './components/SessionNoteModal';
import SessionRequestStatusBadge from './components/SessionRequestStatusBadge';

interface SessionsScreenProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  connectionName?: string;
  cachedSessions: SessionSummary[] | null;
  lastLoadedAt: number | null;
  isActive: boolean;
  onUpdateCache: (sessions: SessionSummary[]) => void;
  onSelectSession: (sessionId: string) => void;
  requestStatuses?: Readonly<Record<string, SessionRequestStatus>>;
  newSessionRequestToken?: number;
}

const STORAGE_KEY_SESSION_LIST_ACTIONS = 'clc_pinned_session_list_actions_v1';
const STORAGE_KEY_SESSIONS_HEADER_ACTIONS = 'clc_pinned_sessions_header_actions_v1';

const DEFAULT_PINNED_SESSION_LIST_ACTIONS: SessionActionKey[] = ['agentSwitch', 'settings'];

const BUILTIN_SESSION_LIST_ACTIONS: SessionActionKey[] = [
  'agentSwitch',
  'settings',
  'plugins',
  'localNote',
];
const SESSION_LIST_BASE_ACTIONS: SessionActionDefinition[] = [
  ...ALL_SESSION_ACTIONS,
  {
    key: 'localNote',
    label: 'Local note',
    iconName: 'edit-3',
    defaultPinned: false,
  },
];

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

const SessionsScreen: React.FC<SessionsScreenProps> = ({
  backend,
  connectionId,
  connectionName = 'Sessions',
  cachedSessions,
  lastLoadedAt,
  isActive,
  onUpdateCache,
  onSelectSession,
  requestStatuses = {},
  newSessionRequestToken = 0,
}) => {
  const theme = useTheme();
  const { width: windowWidth } = useWindowDimensions();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const maxHeaderPinnedActions = getMobileHeaderMaxPinnedActions(windowWidth);
  const actionDialogFieldRenderers = useMobileApplicationActionDialogFieldRenderers();
  const { notes, setSessionNote, removeSessionNote } = useHomeWorkspace();

  const { controller: sessionsController, state: sessionsState } = useSessionsController({
    backend,
    initialSessions: cachedSessions ?? [],
  });
  const sessions = sessionsState?.sessions ?? cachedSessions ?? [];
  const sessionsLoading = sessionsState?.loading ?? false;

  const hydrateSessionsCache = useCallback(
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
    cache: cachedSessions != null ? { sessions: cachedSessions, lastLoadedAt } : null,
    hydrate: hydrateSessionsCache,
  });

  const [actionLoading, setActionLoading] = useState(false);
  const loading = sessionsLoading || actionLoading;
  const error = sessionsState?.error ?? (!backend ? 'No active connection' : null);
  const [agentPickerVisible, setAgentPickerVisible] = useState(false);
  const [actionResultDisplay, setActionResultDisplay] = useState<ActionDisplayEntry | null>(null);
  const [inlineActionDisplays, setInlineActionDisplays] = useState<ActionDisplayEntry[]>([]);
  const [activeDisplayActionId, setActiveDisplayActionId] = useState<string | null>(null);
  const { controller: agentsController, state: agentsState } = useAgentsController({
    backend,
    cacheKey: connectionId ?? 'default',
    enabled: !!(backend && isActive),
  });
  const availableAgents = agentsState?.agents ?? [];
  const agentsLoading = agentsState?.loading ?? false;
  const [agentSwitchInProgress, setAgentSwitchInProgress] = useState(false);
  const {
    applicationActions = [],
    sessionListActions,
    actionsById,
    actionsByKey = {},
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
  const {
    error: applicationPluginsError,
    refresh: refreshApplicationPlugins,
  } = useApplicationPluginsContext();
  const applicationPluginsErrorRef = useRef<string | null>(applicationPluginsError);

  useEffect(() => {
    applicationPluginsErrorRef.current = applicationPluginsError;
  }, [applicationPluginsError]);

  const scopedSessionListActionsStorageKey = useMemo(
    () => `${STORAGE_KEY_SESSION_LIST_ACTIONS}:${connectionId ?? 'default'}`,
    [connectionId],
  );

  const defaultPinnedSessionActions = useMemo(
    () => [
      ...DEFAULT_PINNED_SESSION_LIST_ACTIONS,
      ...getDefaultPinnedSessionListActionKeys(sessionListActions),
    ],
    [sessionListActions],
  );
  const { pinned: pinnedSessionActions, setPinned: setPinnedSessionActions } =
    usePersistentPinnedActions<string>(
      scopedSessionListActionsStorageKey,
      defaultPinnedSessionActions,
      { migrateFromKeys: [STORAGE_KEY_SESSION_LIST_ACTIONS] },
    );
  const [agentSwitchVisible, setAgentSwitchVisible] = useState(false);
  const [agentSwitchSessionId, setAgentSwitchSessionId] = useState<string | null>(null);
  const [agentSwitchCurrentId, setAgentSwitchCurrentId] = useState<string | null>(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [settingsSessionId, setSettingsSessionId] = useState<string | null>(null);
  const [serverSettingsVisible, setServerSettingsVisible] = useState(false);
  const [activeApplicationAction, setActiveApplicationAction] =
    useState<ApplicationActionUiElement | null>(null);
  const [pluginsVisible, setPluginsVisible] = useState(false);
  const [pluginsSessionId, setPluginsSessionId] = useState<string | null>(null);
  const [noteSessionId, setNoteSessionId] = useState<string | null>(null);
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [activeRichList, setActiveRichList] = useState<{
    element: SessionListActionElement;
    session: SessionSummary;
  } | null>(null);
  const presentRichList = useCallback(
    (element: SessionListActionElement, session: SessionSummary) => {
      // Let the action-menu modal dismiss before presenting the immediate list
      // modal. iOS does not reliably transition directly between two roots.
      setTimeout(() => {
        setActiveRichList({ element, session });
      }, 0);
    },
    [],
  );

  const closeNonPluginOverlays = useCallback(() => {
    setAgentPickerVisible(false);
    setAgentSwitchVisible(false);
    setSettingsVisible(false);
    setServerSettingsVisible(false);
    setPluginsVisible(false);
    setFiltersVisible(false);
    setActiveRichList(null);
    setNoteSessionId(null);
  }, []);

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
  const scopedHeaderActionsStorageKey = useMemo(
    () => `${STORAGE_KEY_SESSIONS_HEADER_ACTIONS}:${connectionId ?? 'default'}`,
    [connectionId],
  );
  const {
    pinned: pinnedHeaderActions,
    setPinned: setPinnedHeaderActions,
  } = usePersistentPinnedActions<string>(
    scopedHeaderActionsStorageKey,
    ['serverSettings', 'refreshSessions', 'newSession'],
  );

  const navigateToSession = useCallback(
    (sessionId: string) => {
      closeNonPluginOverlays();
      onSelectSession(sessionId);
    },
    [closeNonPluginOverlays, onSelectSession],
  );

	  const loadSessions = useCallback(async () => {
    if (!sessionsController) {
      Alert.alert('Error', 'No active connection');
      return false;
    }
    try {
      const [list] = await Promise.all([
        sessionsController.load({ force: true }),
        refreshApplicationPlugins(),
      ]);
      onUpdateCache(list);
      return true;
    } catch (err: any) {
      console.log('Failed to load sessions', err);
      const message = err?.message || 'Failed to load sessions';
      Alert.alert('Error', message);
      return false;
    }
	  }, [sessionsController, onUpdateCache, refreshApplicationPlugins]);

  useEffect(() => {
    if (!backend) return;
    return subscribeSessionsListRefreshInvalidations(backend, loadSessions);
  }, [backend, loadSessions]);

  const presentActionDisplay = useCallback((display: ActionDisplayPayload, context: RunActionContext) => {
    const nextEntry = createDisplayEntry(display, context);
    const presentation = display.presentation ?? 'modal';
    if (presentation === 'banner' && backend) {
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
    if (presentation === 'inline') {
      setActionResultDisplay(null);
      setInlineActionDisplays((current) => upsertInlineDisplay(current, nextEntry));
      return;
    }
    setActionResultDisplay(nextEntry);
  }, [backend, connectionId]);

  const executePluginAction = useCallback(
    async (element: ActionUiElement, context: RunActionContext) => {
      if (!backend) {
        Alert.alert('Error', 'No active connection');
        return;
      }

      setActionLoading(true);
      try {
        const actionContext = {
          ...context,
          connectionId: connectionId ?? undefined,
        };
        const { ok, effects, display, errorMessage } = await runApplicationAction({
          backend,
          element,
          actionsById,
          actionsByKey,
          context: actionContext,
          effects: { reloadSessionsListOnMutations: true },
        });
        if (!ok) {
          Alert.alert('Action error', errorMessage || 'Failed to execute action');
          return;
        }

        for (const effect of effects) {
          if (effect.type === 'navigateToSession') {
            navigateToSession(effect.sessionId);
            return;
          }
        }
        if (effects.some((effect) => effect.type === 'reloadSessionsList')) {
          await loadSessions();
        }
        const normalizedDisplay = normalizeActionDisplayForSurface({
          display,
          surface:
            element.ui_type === 'application_action'
              ? 'application_action'
              : 'session_list_action',
          host: 'mobile',
        });
        if (normalizedDisplay) {
          presentActionDisplay(normalizedDisplay, actionContext);
        }
      } finally {
        setActionLoading(false);
      }
    },
    [
      actionsById,
      actionsByKey,
      backend,
      connectionId,
      loadSessions,
      navigateToSession,
      presentActionDisplay,
    ],
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
      if (action.kind === 'download_attachment_asset') {
        if (!backend) {
          Alert.alert('No connection', 'Connect to a server to download the generated file.');
          return;
        }
        try {
          await handleGeneratedFileFollowupAction({ backend, action });
        } catch (err: any) {
          Alert.alert(
            'File action failed',
            err?.message || 'Unable to open the generated file.',
          );
        }
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
    [backend, executePluginAction],
  );

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
        await executePluginAction(element, {
          sessionId: session.session_id,
          connectionId: connectionId ?? undefined,
          sessionSummary: session,
          dialogValues,
        });
      },
	      [connectionId, executePluginAction],
	    ),
	  );

  const closeAllOverlays = useCallback(() => {
    closeNonPluginOverlays();
    handleCancelPluginDialog();
    setSettingsSessionId(null);
    setAgentSwitchSessionId(null);
    setAgentSwitchCurrentId(null);
    setPluginsSessionId(null);
  }, [closeNonPluginOverlays, handleCancelPluginDialog]);

  useEffect(() => {
    if (!isActive) return;
    if (!sessionsController) return;

    sessionsController
      .loadIfStale({ staleMs: 30000 })
      .then((list) => {
        if (list) {
          onUpdateCache(list);
        }
      })
      .catch(() => {
        // Error is handled in controller + via Alert in manual reload flows.
      });
  }, [isActive, sessionsController, onUpdateCache]);

  useEffect(() => {
    if (!isActive) return;
    if (!applicationPluginsErrorRef.current) return;

    refreshApplicationPlugins().catch(() => {
      // Errors are stored in state and can be retried manually via Reload.
    });
  }, [isActive, refreshApplicationPlugins]);

  useEffect(() => {
    if (isActive) return;
    closeAllOverlays();
  }, [isActive, closeAllOverlays]);

  const createSessionWithAgent = async (agentId: string | null) => {
    setAgentPickerVisible(false); // Fix: If we don't close the picker first, the SessionsScreen become unresponsive.
    if (!sessionsController || !backend) {
      Alert.alert('Error', 'No active connection');
      return;
    }
    let chosenAgent = agentId && agentId.trim() ? agentId.trim() : '';
    if (!chosenAgent) {
	      const fallback = pickDefaultAgentId(availableAgents);
	      if (fallback) {
	        chosenAgent = fallback;
	      } else {
        Alert.alert('Error', 'No agents are available from the server.');
        return;
      }
    }
    setActionLoading(true);
    try {
      const result = await sessionsController.createSession({ agentId: chosenAgent });
      navigateToSession(result.sessionId);
    } catch (err: any) {
      console.log('Failed to create session', err);
      const message = err?.message || 'Failed to create session';
      Alert.alert('Error', message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleNewSession = async () => {
    setAgentPickerVisible(true);
    if (availableAgents.length > 0) {
      return;
    }
    try {
	      await agentsController?.ensureLoaded();
    } catch (err: any) {
      console.log('Failed to load agents for new session', err);
      const message = err?.message || 'Failed to load agents';
      Alert.alert('Error', message);
    }
  };

  const handledNewSessionRequestToken = useRef(newSessionRequestToken);
  useEffect(() => {
    if (
      !isActive ||
      newSessionRequestToken === handledNewSessionRequestToken.current
    ) {
      return;
    }
    handledNewSessionRequestToken.current = newSessionRequestToken;
    void handleNewSession();
  }, [isActive, newSessionRequestToken]);

  const handleBuiltinSessionAction = useCallback(
    async (action: SessionActionKey, s: SessionSummary) => {

      if (action === 'localNote') {
        setNoteSessionId(s.session_id);
        return;
      }

      if (action === 'settings') {
        setSettingsSessionId(s.session_id);
        setSettingsVisible(true);
        return;
      }

      if (action === 'plugins') {
        setPluginsSessionId(s.session_id);
        setPluginsVisible(true);
        return;
      }

      if (action === 'snapshots') {
        navigateToSession(s.session_id);
        return;
      }

      if (action === 'agentSwitch') {
        if (!backend) {
	          Alert.alert('Error', 'No active connection');
          return;
        }
        setAgentSwitchSessionId(s.session_id);
        setAgentSwitchVisible(true);
        try {
          if (availableAgents.length === 0) {
	            await agentsController?.ensureLoaded();
          }
          const current = await backend.getSessionAgent(s.session_id);
          setAgentSwitchCurrentId(current);
        } catch (err: any) {
          console.log('Failed to load agents for switch', err);
          const message = err?.message || 'Failed to load agents';
          Alert.alert('Error', message);
        }
      }
    },
	    [backend, availableAgents.length, agentsController],
  );

  const handleConfirmAgentSwitch = async (agentId: string) => {
    const sid = agentSwitchSessionId;
    if (!sid) {
      setAgentSwitchVisible(false);
      return;
    }
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to switch agent.');
      return;
    }
    try {
	      setAgentSwitchInProgress(true);
      await backend.switchSessionAgent(sid, agentId);
      setAgentSwitchVisible(false);
      setAgentSwitchCurrentId(agentId);
    } catch (err: any) {
      console.log('Failed to switch agent', err);
      const message = err?.message || 'Failed to switch agent';
      Alert.alert('Error', message);
    } finally {
	      setAgentSwitchInProgress(false);
    }
  };

  const sessionListFieldGroups = useMemo(
    () => groupSessionListFields(sessionListFields || []),
    [sessionListFields],
  );

  const filteredSessions = useMemo(
    () => filterSessions(sessions),
    [filterSessions, sessions],
  );
  const hasActiveFilters =
    searchText !== '' || activeNonMainFilterCount > 0;

  const renderSessionItem = (s: SessionSummary) => {
    const modifiedDate = new Date(s.modified * 1000);
    const modifiedLabel = modifiedDate.toLocaleString();

	    const presentation = deriveSessionListPresentationFromGroups(s, sessionListFieldGroups);
	    const title = presentation.title;
	    const subtitle = presentation.subtitle;
	    const metaText = presentation.meta;

    const actions = sessionListActions ?? [];
    const headerLeadingAction = selectSessionListRichActionForPlacement(
      actions,
      'header_leading',
    );
    const headerTrailingAction = selectSessionListRichActionForPlacement(
      actions,
      'header_trailing',
    );

    const hasAnyActions =
      BUILTIN_SESSION_LIST_ACTIONS.length > 0 || (actions && actions.length > 0);

    return (
      <TouchableOpacity
        key={s.session_id}
        style={styles.sessionItem}
        testID={`session-row-${s.session_id}`}
	      onPress={() => navigateToSession(s.session_id)}
      >
        <View style={styles.sessionHeaderRow}>
          {headerLeadingAction ? (
            <View style={styles.sessionHeaderLeadingAction}>
              <SessionListRichActionControl
                element={headerLeadingAction}
                session={s}
                placement="header_leading"
                disabled={!backend || actionLoading}
                onExecuteAction={(element, dialogValues) =>
                  executePluginAction(element, {
                    sessionId: s.session_id,
                    sessionSummary: s,
                    dialogValues,
                  })
                }
                onPresentRichList={(element) => presentRichList(element, s)}
                renderIcon={({ name, size, color }) => (
                  <Icon name={name} size={size} color={color} />
                )}
                testID={`session-rich-header-${s.session_id}-header_leading-${headerLeadingAction.id}`}
              />
            </View>
          ) : null}
          <View style={styles.sessionHeaderTextColumn}>
            <Text
              style={styles.sessionTitle}
              testID={`session-title-${s.session_id}`}
            >
              {title}
            </Text>
          </View>
          {headerTrailingAction ? (
            <View style={styles.sessionHeaderTrailingAction}>
              <SessionListRichActionControl
                element={headerTrailingAction}
                session={s}
                placement="header_trailing"
                disabled={!backend || actionLoading}
                onExecuteAction={(element, dialogValues) =>
                  executePluginAction(element, {
                    sessionId: s.session_id,
                    sessionSummary: s,
                    dialogValues,
                  })
                }
                onPresentRichList={(element) => presentRichList(element, s)}
                renderIcon={({ name, size, color }) => (
                  <Icon name={name} size={size} color={color} />
                )}
                testID={`session-rich-header-${s.session_id}-header_trailing-${headerTrailingAction.id}`}
              />
            </View>
          ) : null}
        </View>
        <Text
          style={styles.sessionId}
          testID={`session-id-${s.session_id}`}
        >
          {s.session_id}
        </Text>
        {subtitle ? (
          <Text
            style={styles.sessionSubtitle}
            testID={`session-subtitle-${s.session_id}`}
          >
            {subtitle}
          </Text>
        ) : s.preview ? (
          <Text
            style={styles.sessionPreview}
            testID={`session-preview-${s.session_id}`}
          >
            {s.preview}
          </Text>
        ) : null}
        <Text
          style={styles.sessionMeta}
          testID={`session-meta-${s.session_id}`}
        >
          {metaText || `Updated: ${modifiedLabel}`}
        </Text>
        <SessionRequestStatusBadge
          status={requestStatuses[s.session_id] ?? null}
          testID={`session-request-status-${s.session_id}`}
        />
        {notes[s.session_id] ? (
          <Text
            style={styles.localNote}
            numberOfLines={2}
            testID={`session-local-note-${s.session_id}`}
          >
            {notes[s.session_id]}
          </Text>
        ) : null}
        {hasAnyActions && (
          <View style={styles.sessionActionsRow}>
            <SessionListActionsBar
              session={s}
              pluginActions={actions}
              baseActions={SESSION_LIST_BASE_ACTIONS}
              renderIcon={({ name, size, color }) => (
                <Icon name={name} size={size} color={color} />
              )}
              renderPinIcon={({ size, color }) => (
                <Icon name="star" size={size} color={color} />
              )}
              renderCloseIcon={({ size, color, renderIcon }) =>
                renderIcon ? renderIcon({ name: 'x', size, color }) : null
              }
              pinned={pinnedSessionActions}
              onChangePinned={setPinnedSessionActions}
              availableActions={BUILTIN_SESSION_LIST_ACTIONS}
              isActive={isActive}
              menuButtonTestID={`session-actions-menu-${s.session_id}`}
              modalContentStyle={styles.sessionActionsModalContent}
              isActionDisabled={(key) =>
                key !== 'localNote' && (!backend || actionLoading)
              }
              onBaseAction={(key) =>
                handleBuiltinSessionAction(key as SessionActionKey, s)
              }
              onExecuteAction={(element, dialogValues) =>
                executePluginAction(element, {
                  sessionId: s.session_id,
                  sessionSummary: s,
                  dialogValues,
                })
              }
              onFallbackAction={(element) => openPluginDialogForElement(element, s)}
              onPresentRichList={(element) => presentRichList(element, s)}
            />
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow} testID="sessions-screen-header">
        <Text
          style={styles.screenTitle}
          numberOfLines={1}
          ellipsizeMode="tail"
          testID="sessions-screen-title"
        >
          {connectionName || 'Sessions'}
        </Text>
        <View style={styles.headerButtons}>
          <ActionsMenuBar<SessionsHeaderActionDefinition>
            title="Sessions actions"
            baseActions={sessionsHeaderActionDefinitions}
            pinned={pinnedHeaderActions}
            maxPinnedActionsForBar={maxHeaderPinnedActions}
            onChangePinned={setPinnedHeaderActions}
            isActive={isActive}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            renderPinIcon={({ size, color }) => (
              <Icon name="star" size={size} color={color} />
            )}
            menuButtonTestID="sessions-actions-menu"
            isActionDisabled={(key) =>
              !backend ||
              actionLoading ||
              (key === 'refreshSessions' && loading) ||
              (key === 'newSession' && agentsLoading)
            }
            onAction={(key) => {
              if (key === 'serverSettings') {
                setServerSettingsVisible(true);
                return;
              }
              if (key === 'refreshSessions') {
                void loadSessions();
                return;
              }
              if (key === 'newSession') {
                void handleNewSession();
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
                setActiveApplicationAction(element);
              }
            }}
          />
        </View>
      </View>

      <View style={styles.filterControlsRow} testID="sessions-search-filter-row">
        <TextInput
          testID="session-main-search"
          accessibilityLabel={mainSearch.label}
          style={styles.input}
          placeholder={mainSearch.label}
          placeholderTextColor={theme.textSecondary}
          value={searchText}
          onChangeText={setSearchText}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {nonMainFilters.length > 0 ? (
          <TouchableOpacity
            testID="session-filters-open"
            accessibilityLabel="Open session filters"
            style={[
              styles.filterButton,
              activeNonMainFilterCount > 0
                ? styles.filterButtonActive
                : null,
            ]}
            onPress={() => setFiltersVisible(true)}
          >
            <Icon
              name="filter"
              size={18}
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
          </TouchableOpacity>
        ) : null}
      </View>

      <MobileDisplayHost
        scope="connection"
        testID="sessions-notification-banner-rail"
      />

      {sessionListFilterSchema.mainSearchConflict ? (
        <Text
          testID="session-filter-schema-warning"
          style={styles.filterWarning}
        >
          Multiple plugins declare the main session search. Using fallback search.
        </Text>
      ) : null}

      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.primary} />
          <Text style={styles.loadingText}>Loading sessions...</Text>
        </View>
      )}

      {error && !loading && (
        <Text style={styles.errorText}>{error}</Text>
      )}

      {!loading && filteredSessions.length === 0 && !error && (
        <Text style={styles.emptyText}>
          {sessions.length === 0
            ? 'No sessions found. Create one to get started.'
            : hasActiveFilters
              ? 'No sessions match the active search or filters.'
              : 'No sessions match the current filter defaults.'}
        </Text>
      )}

      <FlatList
        style={styles.list}
        data={filteredSessions}
        keyExtractor={(item) => item.session_id}
        renderItem={({ item }) => renderSessionItem(item)}
      />

      <Modal
        visible={filtersVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setFiltersVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.filtersModalContent}>
            <SessionListFiltersPanel
              schema={effectiveFilterSchema}
              values={sessionFilterValues}
              onChange={setFilterValue}
              onReset={resetSessionFilters}
              onShowAll={showAllSessions}
              onRequestClose={() => setFiltersVisible(false)}
              renderIcon={({ name, size, color }) => (
                <Icon name={name} size={size} color={color} />
              )}
            />
          </View>
        </View>
      </Modal>

      <Modal
        visible={activeRichList !== null}
        transparent
        animationType="fade"
        onRequestClose={() => setActiveRichList(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.richListModalContent}>
            {activeRichList ? (
              <SessionListRichActionList
                element={activeRichList.element}
                session={activeRichList.session}
                testIDPrefix={`session-rich-list-${activeRichList.session.session_id}-${activeRichList.element.id}`}
                onRequestClose={() => setActiveRichList(null)}
                onExecuteAction={(dialogValues) =>
                  executePluginAction(activeRichList.element, {
                    sessionId: activeRichList.session.session_id,
                    sessionSummary: activeRichList.session,
                    dialogValues,
                  })
                }
                renderIcon={({ name, size, color }) => (
                  <Icon name={name} size={size} color={color} />
                )}
              />
            ) : null}
          </View>
        </View>
      </Modal>

	  {agentPickerVisible && (
	    <Modal
	      visible={agentPickerVisible}
	      transparent
	      animationType="fade"
	      onRequestClose={() => setAgentPickerVisible(false)}
	    >
	      <View style={styles.modalOverlay}>
	        <View style={styles.modalContent}>
	          <Text style={styles.modalTitle}>New session</Text>
	          {agentsLoading && (
	            <View style={styles.loadingContainer}>
	              <ActivityIndicator size="small" color={theme.primary} />
	              <Text style={styles.loadingText}>Loading agents...</Text>
	            </View>
	          )}
	          {!agentsLoading && availableAgents.length === 0 && (
	            <>
	              <Text style={styles.modalSubtitle}>
	                No agents are available from the server.
	              </Text>
	              <View style={styles.modalButtonsRow}>
	                <TouchableOpacity
	                  style={[styles.button, styles.secondaryButton, styles.modalButton]}
	                  onPress={() => setAgentPickerVisible(false)}
	                >
	                  <Text style={styles.buttonTextSecondary}>Cancel</Text>
	                </TouchableOpacity>
	              </View>
	            </>
	          )}
	          {!agentsLoading && availableAgents.length > 0 && (
	            <>
	              <Text style={styles.modalSubtitle}>
	                Choose an agent to start a new session.
	              </Text>
	              <ScrollView style={styles.agentList}>
	                {availableAgents.map((agentId) => (
	                  <TouchableOpacity
	                    key={agentId}
	                    style={styles.agentItem}
	                    onPress={() => {
	                      createSessionWithAgent(agentId);
	                    }}
	                  >
	                    <Text style={styles.agentItemText}>{agentId}</Text>
	                  </TouchableOpacity>
	                ))}
	              </ScrollView>
	              <View style={styles.modalButtonsRow}>
	                <TouchableOpacity
	                  style={[styles.button, styles.secondaryButton, styles.modalButton]}
	                  onPress={() => setAgentPickerVisible(false)}
	                >
	                  <Text style={styles.buttonTextSecondary}>Cancel</Text>
	                </TouchableOpacity>
	              </View>
	            </>
	          )}
	        </View>
	      </View>
	    </Modal>
	  )}

      <ApplicationActionDialog
        visible={activeApplicationAction !== null}
        dialog={activeApplicationAction?.dialog ?? null}
        titleFallback={activeApplicationAction?.label}
        fieldRenderers={actionDialogFieldRenderers}
        onSubmit={(dialogValues) => {
          const element = activeApplicationAction;
          setActiveApplicationAction(null);
          if (element) {
            void executePluginAction(element, {
              connectionId: connectionId ?? undefined,
              dialogValues,
            });
          }
        }}
        onCancel={() => setActiveApplicationAction(null)}
      />

      <ApplicationActionDialog
        visible={!!activePluginDialogElement}
        dialog={(activePluginDialogElement as any)?.dialog || null}
        titleFallback={activePluginDialogElement?.label}
        prefillContext={{
          session: activePluginDialogContext || undefined,
        }}
        fieldRenderers={actionDialogFieldRenderers}
        onSubmit={handleSubmitPluginDialog}
        onCancel={handleCancelPluginDialog}
      />

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
          fieldRenderers={actionDialogFieldRenderers}
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
        fieldRenderers={actionDialogFieldRenderers}
      />

      {settingsSessionId && (
        <SessionSettingsModal
          backend={backend}
          cacheKey={connectionId ?? 'default'}
          sessionId={settingsSessionId}
          visible={settingsVisible}
          onRequestClose={() => setSettingsVisible(false)}
        />
      )}

      <SessionNoteModal
        visible={noteSessionId !== null}
        sessionId={noteSessionId}
        note={noteSessionId ? notes[noteSessionId] ?? null : null}
        onSave={(note) => {
          if (noteSessionId) setSessionNote(noteSessionId, note);
        }}
        onRemove={() => {
          if (noteSessionId) removeSessionNote(noteSessionId);
        }}
        onRequestClose={() => setNoteSessionId(null)}
      />

      <ServerSettingsModal
        backend={backend}
        cacheKey={connectionId ?? 'default'}
        visible={serverSettingsVisible}
        onRequestClose={() => setServerSettingsVisible(false)}
      />

      {pluginsSessionId && (
        <SessionPluginsModal
          backend={backend}
          sessionId={pluginsSessionId}
          visible={pluginsVisible}
          onRequestClose={() => setPluginsVisible(false)}
        />
      )}

      <AgentSwitchModal
        visible={agentSwitchVisible}
	        loading={agentsLoading || agentSwitchInProgress}
        agents={availableAgents}
        selectedAgentId={agentSwitchCurrentId}
        currentAgentId={agentSwitchCurrentId}
        showCurrentLabel
        onRequestClose={() => setAgentSwitchVisible(false)}
        onSelectAgent={handleConfirmAgentSwitch}
      />
    </View>
  );
};
const createStyles = (theme: Theme) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.background,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 12,
    },
    screenTitle: {
      flex: 1,
      flexShrink: 1,
      minWidth: 0,
      marginLeft: 13,
      marginRight: 8,
      fontSize: 16,
      fontWeight: '700',
      color: theme.text,
    },
    headerButtons: {
      flexDirection: 'row',
      alignItems: 'center',
      flexShrink: 1,
      minWidth: ACTIONS_MENU_BAR_ITEM_WIDTH,
    },
    button: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 8,
      marginLeft: 8,
    },
    iconHeaderButton: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 8,
      marginLeft: 8,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: 14,
      fontWeight: '600',
    },
    buttonTextSecondary: {
      color: theme.text,
      fontSize: 14,
      fontWeight: '600',
    },
    input: {
      flex: 1,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 10,
      fontSize: 14,
      color: theme.text,
    },
    filterControlsRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      marginBottom: 12,
    },
    filterButton: {
      width: 42,
      height: 42,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      backgroundColor: theme.surface,
      alignItems: 'center',
      justifyContent: 'center',
    },
    filterButtonActive: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    filterCount: {
      position: 'absolute',
      right: 3,
      top: 1,
      color: theme.primary,
      fontSize: 10,
      fontWeight: '800',
    },
    filterWarning: {
      color: theme.danger,
      fontSize: 12,
      marginBottom: 8,
    },
    loadingContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    loadingText: {
      marginLeft: 8,
      fontSize: 14,
      color: theme.textSecondary,
    },
    errorText: {
      color: theme.danger,
      marginBottom: 8,
    },
    emptyText: {
      fontSize: 14,
      color: theme.textSecondary,
      fontStyle: 'italic',
      marginBottom: 8,
    },
    list: {
      flexGrow: 0,
    },
    sessionItem: {
      padding: 12,
      backgroundColor: theme.surface,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    sessionHeaderRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    sessionHeaderTextColumn: {
      flex: 1,
      paddingRight: 8,
    },
    sessionHeaderLeadingAction: {
      marginRight: 4,
    },
    sessionHeaderTrailingAction: {
      marginLeft: 4,
    },
    sessionTitle: {
      fontSize: theme.typography.fontSize.large,
      lineHeight: theme.typography.lineHeight.large,
      fontWeight: '600',
      marginBottom: 2,
      color: theme.text,
    },
    sessionSubtitle: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
      marginBottom: 2,
    },
    pinIconButton: {
      width: 44,
      height: 44,
      alignItems: 'center',
      justifyContent: 'center',
      marginLeft: 4,
    },
    sessionId: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      marginBottom: 4,
    },
    sessionPreview: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
      marginBottom: 4,
    },
    sessionMeta: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
    },
    localNote: {
      marginTop: 6,
      color: theme.text,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontStyle: 'italic',
    },
    sessionActionsRow: {
      flexDirection: 'row',
      marginTop: 8,
    },
    sessionActionsModalContent: {
      width: '90%',
      maxHeight: '80%',
    },
    sessionActionButton: {
      paddingHorizontal: 10,
      paddingVertical: 4,
    },
    modalOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    modalContent: {
      width: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
    },
    filtersModalContent: {
      width: '90%',
      maxHeight: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
    },
    richListModalContent: {
      width: '82%',
      height: '55%',
      maxHeight: '70%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      overflow: 'hidden',
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: 12,
      color: theme.textSecondary,
      marginBottom: 12,
    },
    modalButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      marginTop: 8,
    },
    modalButton: {
      minWidth: 90,
      alignItems: 'center',
      marginLeft: 8,
    },
    agentList: {
      maxHeight: 220,
      marginTop: 8,
      marginBottom: 8,
    },
    agentItem: {
      paddingVertical: 8,
      paddingHorizontal: 10,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      marginBottom: 6,
    },
    agentItemText: {
      fontSize: 14,
      color: theme.text,
    },
  });

export { createStyles as createSessionsScreenStyles };
export default SessionsScreen;
