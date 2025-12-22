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
import type { ConnectionAdapter } from '../App';
import { useTheme, type Theme } from './theme';
import {
  apiCreateSession,
  apiListAgents,
  apiListSessions,
  type SessionSummary,
} from './api';

interface SessionsScreenProps {
  adapter: ConnectionAdapter | null;
  connectionId: string | null;
  cachedSessions: SessionSummary[] | null;
  lastLoadedAt: number | null;
  isActive: boolean;
  onUpdateCache: (sessions: SessionSummary[]) => void;
  onSelectSession: (sessionId: string) => void;
}

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
    const isStale = !lastLoadedAt || now - lastLoadedAt > 30000;

    if (!hasAutoLoaded || isStale) {
      loadSessions().catch(() => {
        // Error is already handled inside loadSessions.
      });
      setHasAutoLoaded(true);
    }
  }, [isActive, adapter, lastLoadedAt, hasAutoLoaded, loadSessions]);

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
