import React, { useCallback, useEffect, useState } from 'react';
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
import {
  apiCreateSession,
  apiListAgents,
  apiListSessions,
  type SessionSummary,
} from './api';

interface SessionsScreenProps {
  adapter: ConnectionAdapter;
  onSelectSession: (sessionId: string) => void;
}

const SessionsScreen: React.FC<SessionsScreenProps> = ({ adapter, onSelectSession }) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [filterText, setFilterText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentPickerVisible, setAgentPickerVisible] = useState(false);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [agentLoading, setAgentLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    try {
      const list = await apiListSessions(adapter);
      setSessions(list);
      setError(null);
    } catch (err: any) {
      console.log('Failed to load sessions', err);
      const message = err?.message || 'Failed to load sessions';
      setError(message);
      Alert.alert('Error', message);
    } finally {
      setLoading(false);
    }
  }, [adapter]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

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
        value={filterText}
        onChangeText={setFilterText}
        autoCapitalize="none"
        autoCorrect={false}
      />

      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
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
                <ActivityIndicator size="small" color="#007AFF" />
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

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#E5E5EA',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  buttonTextSecondary: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    fontSize: 14,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#8E8E93',
  },
  errorText: {
    color: '#FF3B30',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  list: {
    flexGrow: 0,
  },
  sessionItem: {
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  sessionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  sessionId: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  sessionPreview: {
    fontSize: 14,
    color: '#000000',
    marginBottom: 4,
  },
  sessionMeta: {
    fontSize: 12,
    color: '#8E8E93',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 12,
    color: '#8E8E93',
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
    borderColor: '#E5E5EA',
    marginBottom: 6,
  },
  agentItemText: {
    fontSize: 14,
    color: '#000000',
  },
});

export default SessionsScreen;
