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
  View,
} from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';
import Icon from 'react-native-vector-icons/Feather';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  deriveSessionListPresentationFromGroups,
  groupSessionListFields,
  normalizeActionDisplayForSurface,
  pickDefaultAgentId,
  runApplicationAction,
  type RunActionContext,
} from '@crystal-lattice/frontend-sdk';
import {
  ApplicationActionDialog,
  SessionActionsBar,
  type SessionActionDefinition,
  type SessionActionKey,
} from '@crystal-lattice/frontend-rn-components';
import {
  useAgentsController,
  useHydrateControllerFromCache,
  useSessionsController,
} from '@crystal-lattice/frontend-sdk-react';
import { useTheme, type Theme } from './theme';
import SessionSettingsModal from './components/SessionSettingsModal';
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
import AgentSwitchModal from './components/AgentSwitchModal';
import ActionResultModal from './components/ActionResultModal';
import ActionResultInlineCard from './components/ActionResultInlineCard';

interface SessionsScreenProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  cachedSessions: SessionSummary[] | null;
  lastLoadedAt: number | null;
  isActive: boolean;
  onUpdateCache: (sessions: SessionSummary[]) => void;
  onSelectSession: (sessionId: string) => void;
}

const STORAGE_KEY_SESSION_LIST_ACTIONS = 'clc_pinned_session_list_actions_v1';

const DEFAULT_PINNED_SESSION_LIST_ACTIONS: SessionActionKey[] = ['agentSwitch', 'settings'];

const BUILTIN_SESSION_LIST_ACTIONS: SessionActionKey[] = ['agentSwitch', 'settings', 'plugins'];

type ActionDisplayEntry = {
  key: string;
  display: ActionDisplayPayload;
  context: RunActionContext;
};

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
  cachedSessions,
  lastLoadedAt,
  isActive,
  onUpdateCache,
  onSelectSession,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

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

  const [filterText, setFilterText] = useState('');
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
    sessionListActions,
    actionsById,
    sessionListFields,
    sessionListPinnedToggles,
  } = useApplicationPlugins();
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

  const { pinned: pinnedSessionActions, setPinned: setPinnedSessionActions } =
    usePersistentPinnedActions<SessionActionKey>(
      scopedSessionListActionsStorageKey,
	      DEFAULT_PINNED_SESSION_LIST_ACTIONS,
      { migrateFromKeys: [STORAGE_KEY_SESSION_LIST_ACTIONS] },
    );
  const [agentSwitchVisible, setAgentSwitchVisible] = useState(false);
  const [agentSwitchSessionId, setAgentSwitchSessionId] = useState<string | null>(null);
  const [agentSwitchCurrentId, setAgentSwitchCurrentId] = useState<string | null>(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [settingsSessionId, setSettingsSessionId] = useState<string | null>(null);
  const [pluginsVisible, setPluginsVisible] = useState(false);
  const [pluginsSessionId, setPluginsSessionId] = useState<string | null>(null);

  const closeNonPluginOverlays = useCallback(() => {
    setAgentPickerVisible(false);
    setAgentSwitchVisible(false);
    setSettingsVisible(false);
    setPluginsVisible(false);
  }, []);

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
      return;
    }
    try {
      const [list] = await Promise.all([
        sessionsController.load({ force: true }),
        refreshApplicationPlugins(),
      ]);
      onUpdateCache(list);
    } catch (err: any) {
      console.log('Failed to load sessions', err);
      const message = err?.message || 'Failed to load sessions';
      Alert.alert('Error', message);
    }
	  }, [sessionsController, onUpdateCache, refreshApplicationPlugins]);

  const presentActionDisplay = useCallback((display: ActionDisplayPayload, context: RunActionContext) => {
    const nextEntry = createDisplayEntry(display, context);
    const presentation = display.presentation ?? 'modal';
    if (presentation === 'inline' || presentation === 'banner') {
      setActionResultDisplay(null);
      setInlineActionDisplays((current) => upsertInlineDisplay(current, nextEntry));
      return;
    }
    setActionResultDisplay(nextEntry);
  }, []);

  const executePluginAction = useCallback(
    async (element: ActionUiElement, context: RunActionContext) => {
      if (!backend) {
        Alert.alert('Error', 'No active connection');
        return;
      }

      setActionLoading(true);
      try {
        const { ok, effects, display, errorMessage } = await runApplicationAction({
          backend,
          element,
          actionsById,
          context,
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
          surface: 'session_list_action',
          host: 'mobile',
        });
        if (normalizedDisplay) {
          presentActionDisplay(normalizedDisplay, context);
        }
      } finally {
        setActionLoading(false);
      }
    },
    [actionsById, backend, loadSessions, navigateToSession, presentActionDisplay],
  );

  const handleDisplayFollowupAction = useCallback(
    async (entry: ActionDisplayEntry, action: ActionDisplayFollowupAction) => {
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
            },
            entry.context,
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
	  } = usePluginActionDialog<SessionSummary>(
	    useCallback(
      async (
        element: ActionUiElement,
        session: SessionSummary,
        dialogValues: Record<string, any> | undefined,
      ) => {
        await executePluginAction(element, {
          sessionId: session.session_id,
          sessionSummary: session,
          dialogValues,
        });
      },
	      [executePluginAction],
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

  const handleBuiltinSessionAction = useCallback(
    async (action: SessionActionKey, s: SessionSummary) => {

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

  const pluginSessionActionDefs: SessionActionDefinition[] = useMemo(
    () =>
      (sessionListActions ?? []).map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
        defaultPinned: false,
      })),
    [sessionListActions],
  );

  const sessionListFieldGroups = useMemo(
    () => groupSessionListFields(sessionListFields || []),
    [sessionListFields],
  );

  const filteredSessions = sessions.filter((s) => {
    if (!filterText.trim()) return true;
    const q = filterText.toLowerCase();
    return (
      s.session_id.toLowerCase().includes(q) ||
      (s.preview || '').toLowerCase().includes(q)
    );
  });

  const renderSessionItem = (s: SessionSummary) => {
    const modifiedDate = new Date(s.modified * 1000);
    const modifiedLabel = modifiedDate.toLocaleString();

	    const presentation = deriveSessionListPresentationFromGroups(s, sessionListFieldGroups);
	    const title = presentation.title;
	    const subtitle = presentation.subtitle;
	    const metaText = presentation.meta;

    const isPinned = !!s.pinned;
    const pinnedToggleElement = sessionListPinnedToggles[0];

    const actions = sessionListActions ?? [];

    const handleRowAction = (key: SessionActionKey) => {
      if (BUILTIN_SESSION_LIST_ACTIONS.includes(key)) {
        handleBuiltinSessionAction(key, s);
        return;
      }
      const element = actions.find((el) => el.id === key);
      if (element) {
        openPluginDialogForElement(element, s);
      }
    };

    const hasAnyActions =
      BUILTIN_SESSION_LIST_ACTIONS.length > 0 || (actions && actions.length > 0);

    return (
      <TouchableOpacity
        key={s.session_id}
        style={styles.sessionItem}
	      onPress={() => navigateToSession(s.session_id)}
      >
        <View style={styles.sessionHeaderRow}>
          <View style={styles.sessionHeaderTextColumn}>
            <Text style={styles.sessionTitle}>{title}</Text>
          </View>
          {pinnedToggleElement ? (
            <TouchableOpacity
              style={styles.pinIconButton}
              onPress={() => {
                if (!backend) {
                  Alert.alert('Error', 'No active connection');
                  return;
                }
                openPluginDialogForElement(pinnedToggleElement, s);
              }}
            >
              <Icon
                name="star"
                size={18}
                color={isPinned ? '#FFCC00' : theme.textSecondary}
              />
            </TouchableOpacity>
          ) : null}
        </View>
        <Text style={styles.sessionId}>{s.session_id}</Text>
        {subtitle ? (
          <Text style={styles.sessionSubtitle}>{subtitle}</Text>
        ) : s.preview ? (
          <Text style={styles.sessionPreview}>{s.preview}</Text>
        ) : null}
        <Text style={styles.sessionMeta}>{metaText || `Updated: ${modifiedLabel}`}</Text>
        {hasAnyActions && (
          <View style={styles.sessionActionsRow}>
            <SessionActionsBar
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
              onAction={handleRowAction}
              extraActions={pluginSessionActionDefs}
              availableActions={BUILTIN_SESSION_LIST_ACTIONS}
              isActive={isActive}
              modalContentStyle={styles.sessionActionsModalContent}
            />
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <View style={styles.headerButtons}>
          <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={loadSessions}>
            <Text style={styles.buttonTextSecondary}>Reload</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.button, styles.primaryButton]} onPress={handleNewSession}>
            <Text style={styles.buttonText}>New Session</Text>
          </TouchableOpacity>
        </View>
      </View>

      <TextInput
        style={styles.input}
        placeholder="Filter by id or preview"
        placeholderTextColor={theme.textSecondary}
        value={filterText}
        onChangeText={setFilterText}
        autoCapitalize="none"
        autoCorrect={false}
      />

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
        <Text style={styles.emptyText}>No sessions found. Create one to get started.</Text>
      )}

      <FlatList
        style={styles.list}
        data={filteredSessions}
        keyExtractor={(item) => item.session_id}
        renderItem={({ item }) => renderSessionItem(item)}
      />

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
        visible={!!activePluginDialogElement}
        dialog={(activePluginDialogElement as any)?.dialog || null}
        titleFallback={activePluginDialogElement?.label}
        prefillContext={{
          session: activePluginDialogContext || undefined,
        }}
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
          onFollowupAction={(action) => handleDisplayFollowupAction(entry, action)}
        />
      ))}

      <ActionResultModal
        visible={!!actionResultDisplay}
        display={actionResultDisplay?.display ?? null}
        activeActionId={activeDisplayActionId}
        onRequestClose={() => setActionResultDisplay(null)}
        onFollowupAction={(action) => {
          if (!actionResultDisplay) return;
          handleDisplayFollowupAction(actionResultDisplay, action);
        }}
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
      justifyContent: 'flex-end',
      marginBottom: 12,
    },
    headerButtons: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    button: {
      paddingHorizontal: 12,
      paddingVertical: 8,
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
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      padding: 10,
      marginBottom: 12,
      fontSize: 14,
      color: theme.text,
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
    sessionTitle: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: 2,
      color: theme.text,
    },
    sessionSubtitle: {
      fontSize: 14,
      color: theme.textSecondary,
      marginBottom: 2,
    },
    pinIconButton: {
      paddingHorizontal: 4,
      paddingVertical: 4,
      marginLeft: 4,
    },
    sessionId: {
      fontSize: 12,
      color: theme.textSecondary,
      marginBottom: 4,
    },
    sessionPreview: {
      fontSize: 14,
      color: theme.text,
      marginBottom: 4,
    },
    sessionMeta: {
      fontSize: 12,
      color: theme.textSecondary,
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

export default SessionsScreen;
