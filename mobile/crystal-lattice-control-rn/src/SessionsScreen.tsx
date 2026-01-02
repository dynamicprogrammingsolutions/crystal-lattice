import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { ConnectionAdapter } from '../App';
import { useTheme, type Theme } from './theme';
import SessionActionsBar from './components/SessionActionsBar';
import SessionSettingsModal from './components/SessionSettingsModal';
import { type SessionActionKey, type SessionActionDefinition } from './sessionActions';
import {
  apiCreateSession,
  apiListAgents,
  apiListSessions,
  apiSend,
  apiGetSessionAgent,
  apiSwitchSessionAgent,
  apiExecuteAction,
  apiListApplicationUiSchema,
  type ActionUiElement,
  type SessionSummary,
} from './api';
import ApplicationActionDialog from './components/ApplicationActionDialog';

interface SessionsScreenProps {
  adapter: ConnectionAdapter | null;
  connectionId: string | null;
  cachedSessions: SessionSummary[] | null;
  lastLoadedAt: number | null;
  isActive: boolean;
  onUpdateCache: (sessions: SessionSummary[]) => void;
  onSelectSession: (sessionId: string) => void;
}

const STORAGE_KEY_SESSION_LIST_ACTIONS = 'clc_pinned_session_list_actions_v1';

const SESSION_LIST_PLUGIN_CACHE: Record<string, ActionUiElement[] | null> = {};

const BUILTIN_SESSION_LIST_ACTIONS: SessionActionKey[] = ['resend', 'agentSwitch', 'settings'];

const SessionsScreen: React.FC<SessionsScreenProps> = ({
  adapter,
  connectionId,
  cachedSessions,
  lastLoadedAt,
  isActive,
  onUpdateCache,
  onSelectSession,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [sessions, setSessions] = useState<SessionSummary[]>(cachedSessions ?? []);
  const [filterText, setFilterText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentPickerVisible, setAgentPickerVisible] = useState(false);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [agentLoading, setAgentLoading] = useState(false);
  const [hasAutoLoaded, setHasAutoLoaded] = useState(false);
  const [sessionListActions, setSessionListActions] = useState<ActionUiElement[] | null>(null);
  const [pinnedSessionActions, setPinnedSessionActions] = useState<SessionActionKey[]>(
    BUILTIN_SESSION_LIST_ACTIONS,
  );
  const [activePluginDialog, setActivePluginDialog] = useState<
    { element: ActionUiElement; session: SessionSummary } | null
  >(null);
  const [agentSwitchVisible, setAgentSwitchVisible] = useState(false);
  const [agentSwitchSessionId, setAgentSwitchSessionId] = useState<string | null>(null);
  const [agentSwitchCurrentId, setAgentSwitchCurrentId] = useState<string | null>(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [settingsSessionId, setSettingsSessionId] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    if (!adapter) {
      const message = 'No active connection';
      setError(message);
      Alert.alert('Error', message);
      return;
    }
    setLoading(true);
    try {
      const list = await apiListSessions(adapter);
      setSessions(list);
      onUpdateCache(list);
      setError(null);
    } catch (err: any) {
      console.log('Failed to load sessions', err);
      const message = err?.message || 'Failed to load sessions';
      setError(message);
      Alert.alert('Error', message);
    } finally {
      setLoading(false);
    }
  }, [adapter, onUpdateCache]);

  useEffect(() => {
    const loadPinned = async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY_SESSION_LIST_ACTIONS);
        if (!raw) return;
        try {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            const valid = parsed.filter((key: any) => typeof key === 'string');
            if (valid.length > 0 || parsed.length === 0) {
              setPinnedSessionActions(valid as SessionActionKey[]);
            }
          }
        } catch (err) {
          console.log('Failed to parse stored session list actions', err);
        }
      } catch (err) {
        console.log('Failed to load session list pinned actions', err);
      }
    };

    loadPinned();
  }, []);

  useEffect(() => {
    const savePinned = async () => {
      try {
        await AsyncStorage.setItem(
          STORAGE_KEY_SESSION_LIST_ACTIONS,
          JSON.stringify(pinnedSessionActions),
        );
      } catch (err) {
        console.log('Failed to save session list pinned actions', err);
      }
    };

    savePinned();
  }, [pinnedSessionActions]);

  useEffect(() => {
    if (cachedSessions) {
      setSessions(cachedSessions);
      setError(null);
    } else if (!adapter) {
      setSessions([]);
    }
  }, [cachedSessions, connectionId, adapter]);

  useEffect(() => {
    if (!isActive) return;
    if (!adapter) return;

    const now = Date.now();
    const hasTimestamp = lastLoadedAt != null;
    const isStale = hasTimestamp && now - lastLoadedAt > 30000;

    if (!hasTimestamp || isStale) {
      loadSessions().catch(() => {
        // Error is already handled inside loadSessions.
      });
      setHasAutoLoaded(true);
    }
  }, [isActive, adapter, lastLoadedAt, loadSessions]);

  useEffect(() => {
    if (!isActive || !adapter) {
      setSessionListActions(null);
      return;
    }

    let cancelled = false;

    const loadUiSchema = async () => {
      try {
        const cacheKey = `${connectionId || 'default'}:application_ui_schema`;
        const cached = SESSION_LIST_PLUGIN_CACHE[cacheKey];
        if (cached !== undefined) {
          if (!cancelled) {
            setSessionListActions(cached && cached.length > 0 ? cached : null);
          }
          return;
        }

        const elements = await apiListApplicationUiSchema(adapter);
        if (cancelled) return;
        const listActions = elements.filter((el) => {
          return (
            el &&
            typeof el === 'object' &&
            (el as any).ui_type === 'session_list_action'
          );
        }) as ActionUiElement[];

        SESSION_LIST_PLUGIN_CACHE[cacheKey] = listActions;
        setSessionListActions(listActions.length > 0 ? listActions : null);
      } catch (err) {
        console.log('Failed to load application UI schema', err);
        if (!cancelled) {
          setSessionListActions(null);
        }
      }
    };

    loadUiSchema().catch(() => {
      // Error already logged above.
    });

    return () => {
      cancelled = true;
    };
  }, [adapter, isActive, connectionId]);

  const createSessionWithAgent = async (agentId: string | null) => {
    const chosenAgent = agentId && agentId.trim() ? agentId.trim() : 'default';
    setLoading(true);
    try {
      const result = await apiCreateSession(adapter, chosenAgent);
      const newId = result.session.session_id;
      setAgentPickerVisible(false);
      if (typeof newId === 'string' && newId) {
        onSelectSession(newId);
      } else {
        // Fallback: reload list if for some reason session id is missing.
        await loadSessions();
      }
    } catch (err: any) {
      console.log('Failed to create session', err);
      const message = err?.message || 'Failed to create session';
      Alert.alert('Error', message);
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = async () => {
    setAgentPickerVisible(true);
    if (availableAgents.length > 0) {
      return;
    }
    try {
      setAgentLoading(true);
      const agents = await apiListAgents(adapter);
      setAvailableAgents(agents);
    } catch (err: any) {
      console.log('Failed to load agents for new session', err);
      const message = err?.message || 'Failed to load agents';
      Alert.alert('Error', message);
    } finally {
      setAgentLoading(false);
    }
  };

  const executePluginSessionAction = useCallback(
    async (
      element: ActionUiElement,
      s: SessionSummary,
      dialogValues: Record<string, any> | undefined,
    ) => {
      if (!adapter) {
        const message = 'No active connection';
        setError(message);
        Alert.alert('Error', message);
        return;
      }

      const inputs: Record<string, any> = {};

      if (element.fixed_params && typeof element.fixed_params === 'object') {
        for (const [k, v] of Object.entries(element.fixed_params)) {
          inputs[k] = v;
        }
      }

      const getFromPath = (root: any, path: string): any => {
        const parts = path.split('.');
        let current: any = root;
        for (const part of parts) {
          if (current == null) return undefined;
          current = (current as any)[part];
        }
        return current;
      };

      if (element.param_map && typeof element.param_map === 'object') {
        for (const [paramName, source] of Object.entries(element.param_map)) {
          if (typeof source !== 'string') continue;
          let value: any;
          if (source.startsWith('$session.')) {
            const path = source.slice('$session.'.length);
            value = getFromPath(s, path);
          } else if (source.startsWith('$dialog.')) {
            const path = source.slice('$dialog.'.length);
            value = getFromPath(dialogValues || {}, path);
          }
          if (value !== undefined) {
            inputs[paramName] = value;
          }
        }
      }

      try {
        const resp = await apiExecuteAction(adapter, element.plugin, element.action_id, inputs);
        if (resp.status !== 'ok') {
          const message = (resp as any).message || 'Failed to execute action';
          Alert.alert('Action error', message);
          return;
        }

        const result: any = (resp as any).result || {};
        const selectedId = result.selected_session_id;
        if (typeof selectedId === 'string' && selectedId) {
          onSelectSession(selectedId);
          return;
        }

        await loadSessions();
      } catch (err: any) {
        console.log('Failed to execute session action', err);
        const message = err?.message || 'Failed to execute action';
        Alert.alert('Action error', message);
      }
    },
    [adapter, loadSessions, onSelectSession],
  );

  const handlePluginElementForSession = useCallback(
    (element: ActionUiElement, s: SessionSummary) => {
      const dialog: any = (element as any).dialog || {};
      if (!dialog || dialog.kind === 'none') {
        executePluginSessionAction(element, s, undefined);
        return;
      }
      setActivePluginDialog({ element, session: s });
    },
    [executePluginSessionAction],
  );

  const handleBuiltinSessionAction = useCallback(
    async (action: SessionActionKey, s: SessionSummary) => {
      if (action === 'resend') {
        if (!adapter) {
          const message = 'No active connection';
          setError(message);
          Alert.alert('Error', message);
          return;
        }
        try {
          setLoading(true);
          await apiSend(adapter, s.session_id);
          await loadSessions();
        } catch (err: any) {
          console.log('Failed to resend for session', err);
          const message = err?.message || 'Failed to resend';
          Alert.alert('Error', message);
        } finally {
          setLoading(false);
        }
        return;
      }

      if (action === 'settings') {
        setSettingsSessionId(s.session_id);
        setSettingsVisible(true);
        return;
      }

      if (action === 'agentSwitch') {
        if (!adapter) {
          const message = 'No active connection';
          setError(message);
          Alert.alert('Error', message);
          return;
        }
        setAgentSwitchSessionId(s.session_id);
        setAgentSwitchVisible(true);
        try {
          setAgentLoading(true);
          if (availableAgents.length === 0) {
            const agents = await apiListAgents(adapter);
            setAvailableAgents(agents);
          }
          const current = await apiGetSessionAgent(adapter, s.session_id);
          setAgentSwitchCurrentId(current);
        } catch (err: any) {
          console.log('Failed to load agents for switch', err);
          const message = err?.message || 'Failed to load agents';
          Alert.alert('Error', message);
        } finally {
          setAgentLoading(false);
        }
      }
    },
    [adapter, availableAgents.length, loadSessions],
  );

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

  const handleSubmitPluginDialog = useCallback(
    async (values: Record<string, any>) => {
      const current = activePluginDialog;
      if (!current) return;
      setActivePluginDialog(null);
      await executePluginSessionAction(current.element, current.session, values);
    },
    [activePluginDialog, executePluginSessionAction],
  );

  const handleCancelPluginDialog = useCallback(() => {
    setActivePluginDialog(null);
  }, []);

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
    const title = s.preview || `Session ${s.session_id.slice(0, 8)}`;

    const actions = sessionListActions ?? [];

    const handleRowAction = (key: SessionActionKey) => {
      if (BUILTIN_SESSION_LIST_ACTIONS.includes(key)) {
        handleBuiltinSessionAction(key, s);
        return;
      }
      const element = actions.find((el) => el.id === key);
      if (element) {
        handlePluginElementForSession(element, s);
      }
    };

    const hasAnyActions =
      BUILTIN_SESSION_LIST_ACTIONS.length > 0 || (actions && actions.length > 0);

    return (
      <TouchableOpacity
        key={s.session_id}
        style={styles.sessionItem}
        onPress={() => onSelectSession(s.session_id)}
      >
        <Text style={styles.sessionTitle}>{title}</Text>
        <Text style={styles.sessionId}>{s.session_id}</Text>
        {s.preview ? <Text style={styles.sessionPreview}>{s.preview}</Text> : null}
        <Text style={styles.sessionMeta}>Updated: {modifiedLabel}</Text>
        {hasAnyActions && (
          <View style={styles.sessionActionsRow}>
            <SessionActionsBar
              pinned={pinnedSessionActions}
              onChangePinned={setPinnedSessionActions}
              onAction={handleRowAction}
              extraActions={pluginSessionActionDefs}
              availableActions={BUILTIN_SESSION_LIST_ACTIONS}
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

      <ScrollView style={styles.list}>
        {filteredSessions.map(renderSessionItem)}
      </ScrollView>

      <Modal
        visible={agentPickerVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setAgentPickerVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>New session</Text>
            {agentLoading && (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color={theme.primary} />
                <Text style={styles.loadingText}>Loading agents...</Text>
              </View>
            )}
            {!agentLoading && availableAgents.length === 0 && (
              <>
                <Text style={styles.modalSubtitle}>
                  No agents are available from the server. A session can still be
                  created with the default agent.
                </Text>
                <View style={styles.modalButtonsRow}>
                  <TouchableOpacity
                    style={[styles.button, styles.secondaryButton, styles.modalButton]}
                    onPress={() => setAgentPickerVisible(false)}
                  >
                    <Text style={styles.buttonTextSecondary}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.button, styles.primaryButton, styles.modalButton]}
                    onPress={() => {
                      createSessionWithAgent('default');
                    }}
                  >
                    <Text style={styles.buttonText}>Create</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
            {!agentLoading && availableAgents.length > 0 && (
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

      <ApplicationActionDialog
        visible={!!activePluginDialog}
        dialog={(activePluginDialog?.element as any)?.dialog || null}
        titleFallback={activePluginDialog?.element?.label}
        onSubmit={handleSubmitPluginDialog}
        onCancel={handleCancelPluginDialog}
      />

      {settingsSessionId && (
        <SessionSettingsModal
          adapter={adapter}
          sessionId={settingsSessionId}
          visible={settingsVisible}
          onRequestClose={() => setSettingsVisible(false)}
        />
      )}

      <Modal
        visible={agentSwitchVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setAgentSwitchVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Switch agent</Text>
            {agentLoading && (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color={theme.primary} />
                <Text style={styles.loadingText}>Loading agents...</Text>
              </View>
            )}
            {!agentLoading && availableAgents.length === 0 && (
              <Text style={styles.modalSubtitle}>No agents available.</Text>
            )}
            {!agentLoading && availableAgents.length > 0 && (
              <>
                {agentSwitchCurrentId && (
                  <Text style={styles.modalSubtitle}>
                    Current agent: {agentSwitchCurrentId}
                  </Text>
                )}
                <ScrollView style={styles.agentList}>
                  {availableAgents.map((agentId) => (
                    <TouchableOpacity
                      key={agentId}
                      style={styles.agentItem}
                      onPress={async () => {
                        if (!adapter || !agentSwitchSessionId) return;
                        try {
                          setAgentLoading(true);
                          await apiSwitchSessionAgent(adapter, agentSwitchSessionId, agentId);
                          setAgentSwitchCurrentId(agentId);
                          setAgentSwitchVisible(false);
                        } catch (err: any) {
                          console.log('Failed to switch agent for session', err);
                          const message = err?.message || 'Failed to switch agent';
                          Alert.alert('Error', message);
                        } finally {
                          setAgentLoading(false);
                        }
                      }}
                    >
                      <Text style={styles.agentItemText}>{agentId}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <View style={styles.modalButtonsRow}>
                  <TouchableOpacity
                    style={[styles.button, styles.secondaryButton, styles.modalButton]}
                    onPress={() => setAgentSwitchVisible(false)}
                  >
                    <Text style={styles.buttonTextSecondary}>Close</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
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
    sessionTitle: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: 2,
      color: theme.text,
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
