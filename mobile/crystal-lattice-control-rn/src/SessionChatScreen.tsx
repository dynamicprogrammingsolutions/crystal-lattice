import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { ConnectionAdapter } from '../App';
import {
  apiAppendMessage,
  apiDeleteMessagesByRange,
  apiForkSession,
  apiGetSessionAgent,
  apiListAgents,
  apiListMessages,
  apiSend,
  apiSwitchSessionAgent,
  type IndexedMessage,
} from './api';
import MessageBubble from './components/MessageBubble';
import SessionActionsBar from './components/SessionActionsBar';
import { SESSION_ACTIONS, type SessionActionKey } from './sessionActions';

interface SessionChatScreenProps {
  adapter: ConnectionAdapter;
  sessionId: string;
  onBack: () => void;
  onNavigateToSession?: (sessionId: string) => void;
}

const SessionChatScreen: React.FC<SessionChatScreenProps> = ({
  adapter,
  sessionId,
  onBack,
  onNavigateToSession,
}) => {
  const [messages, setMessages] = useState<IndexedMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sendInProgress, setSendInProgress] = useState(false);
  const [composeText, setComposeText] = useState('');
  const [rangeStartText, setRangeStartText] = useState('-50');
  const [rangeEndText, setRangeEndText] = useState('');
  const [lastReloadAt, setLastReloadAt] = useState<Date | null>(null);
  const [messageLimitVisible, setMessageLimitVisible] = useState(false);
  const [deleteRangeVisible, setDeleteRangeVisible] = useState(false);
  const [deleteRangeStartText, setDeleteRangeStartText] = useState('');
  const [deleteRangeEndText, setDeleteRangeEndText] = useState('');
  const [pinnedSessionActions, setPinnedSessionActions] = useState<SessionActionKey[]>(() =>
    Object.values(SESSION_ACTIONS)
      .filter((def) => def.defaultPinned)
      .map((def) => def.key),
  );
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [sessionAgentId, setSessionAgentId] = useState<string | null>(null);
  const [agentModalVisible, setAgentModalVisible] = useState(false);
  const [agentLoading, setAgentLoading] = useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(false);
  const scrollViewRef = useRef<ScrollView | null>(null);

  const applyMessageLimitAndReload = () => {
    setMessageLimitVisible(false);
    loadMessages();
  };

  const loadMessages = useCallback(async () => {
    setLoadingMessages(true);
		    try {
		      let start: number | undefined;
		      let end: number | undefined;
		      const startTrimmed = rangeStartText.trim();
		      const endTrimmed = rangeEndText.trim();
		      if (startTrimmed) {
		        const parsed = parseInt(startTrimmed, 10);
		        if (!Number.isNaN(parsed)) {
		          start = parsed;
		        }
		      }
		      if (endTrimmed) {
		        const parsedEnd = parseInt(endTrimmed, 10);
		        if (!Number.isNaN(parsedEnd)) {
		          end = parsedEnd;
		        }
		      }
		      const list = await apiListMessages(adapter, sessionId, start, end);
		      setMessages(list);
		      setShouldAutoScroll(true);
		      setLastReloadAt(new Date());
    } catch (err: any) {
      console.log('Failed to load messages', err);
      const message = err?.message || 'Failed to load messages';
      Alert.alert('Error', message);
    } finally {
      setLoadingMessages(false);
	    }
	  }, [adapter, sessionId, rangeStartText, rangeEndText]);

	  useEffect(() => {
	    loadMessages();
	  }, [loadMessages]);

	  const handleAppend = async () => {
    const text = composeText.trim();
    if (!text) {
      return;
    }
    setSendInProgress(true);
    try {
      await apiAppendMessage(adapter, sessionId, 'user', text);
      await loadMessages();
    } catch (err: any) {
      console.log('Failed to append message', err);
      const message = err?.message || 'Failed to append message';
      Alert.alert('Error', message);
    } finally {
      setSendInProgress(false);
    }
  };

  const handleSend = async () => {
    const text = composeText.trim();
    setSendInProgress(true);
    try {
      if (text) {
        await apiAppendMessage(adapter, sessionId, 'user', text);
      }
      await apiSend(adapter, sessionId);
      await loadMessages();
      setComposeText('');
    } catch (err: any) {
      console.log('Failed to send request', err);
      const message = err?.message || 'Failed to send request';
      Alert.alert('Error', message);
    } finally {
      setSendInProgress(false);
    }
  };

	  const confirmDeleteRange = async () => {
	    const startTrimmed = deleteRangeStartText.trim();
	    const endTrimmed = deleteRangeEndText.trim();
	    let start: number | undefined;
	    let end: number | undefined;
	    if (startTrimmed) {
	      const parsed = parseInt(startTrimmed, 10);
	      if (!Number.isNaN(parsed)) {
	        start = parsed;
	      }
	    }
	    if (endTrimmed) {
	      const parsedEnd = parseInt(endTrimmed, 10);
	      if (!Number.isNaN(parsedEnd)) {
	        end = parsedEnd;
	      }
	    }
	    if (start === undefined && end === undefined) {
	      Alert.alert('Invalid range', 'Provide at least a start or end index.');
	      return;
	    }
	    try {
	      await apiDeleteMessagesByRange(adapter, sessionId, start, end);
	      setDeleteRangeVisible(false);
	      await loadMessages();
	    } catch (err: any) {
	      console.log('Failed to delete range', err);
	      const message = err?.message || 'Failed to delete messages';
	      Alert.alert('Error', message);
	    }
	  };

	  const handleSwitchAgent = async (agentId: string) => {
	    try {
	      setAgentLoading(true);
	      await apiSwitchSessionAgent(adapter, sessionId, agentId);
	      setSessionAgentId(agentId);
	      setAgentModalVisible(false);
	    } catch (err: any) {
	      console.log('Failed to switch agent', err);
	      const message = err?.message || 'Failed to switch agent';
	      Alert.alert('Error', message);
	    } finally {
	      setAgentLoading(false);
	    }
	  };

	  const togglePinnedSessionAction = (action: SessionActionKey) => {
	    setPinnedSessionActions((prev) => {
	      if (prev.includes(action)) {
	        return prev.filter((a) => a !== action);
	      }
	      return [...prev, action];
	    });
	  };

  const handleSessionAction = async (action: SessionActionKey) => {
    if (action === 'reload') {
      await loadMessages();
      return;
    }
    if (action === 'resend') {
      setSendInProgress(true);
      try {
        await apiSend(adapter, sessionId);
        await loadMessages();
      } catch (err: any) {
        console.log('Failed to resend request', err);
        const message = err?.message || 'Failed to resend request';
        Alert.alert('Error', message);
      } finally {
        setSendInProgress(false);
      }
      return;
    }
    if (action === 'messageLimit') {
      setMessageLimitVisible(true);
      return;
    }
    if (action === 'copy') {
      try {
        const result = await apiForkSession(adapter, sessionId, -1);
        const newId = result.session.session_id;
        if (onNavigateToSession && typeof newId === 'string' && newId) {
          onNavigateToSession(newId);
        }
      } catch (err: any) {
        console.log('Failed to fork session', err);
        const message = err?.message || 'Failed to copy session';
        Alert.alert('Error', message);
      }
      return;
    }
    if (action === 'deleteRange') {
      setDeleteRangeStartText('');
      setDeleteRangeEndText('');
      setDeleteRangeVisible(true);
      return;
    }
    if (action === 'agentSwitch') {
      setAgentModalVisible(true);
      if (availableAgents.length === 0 || sessionAgentId === null) {
        try {
          setAgentLoading(true);
          const agents = await apiListAgents(adapter);
          setAvailableAgents(agents);
          const current = await apiGetSessionAgent(adapter, sessionId);
          setSessionAgentId(current);
        } catch (err: any) {
          console.log('Failed to load agents', err);
          const message = err?.message || 'Failed to load agents';
          Alert.alert('Error', message);
        } finally {
          setAgentLoading(false);
        }
      }
      return;
    }
  };

	  const sessionLabel = `Session ${sessionId.slice(0, 8)}`;

		  return (
	    <KeyboardAvoidingView
	      style={styles.keyboardAvoiding}
	      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
	      keyboardVerticalOffset={8}
	    >
	      <View style={styles.container}>
	        <View style={styles.headerRow}>
	          <TouchableOpacity style={styles.backButton} onPress={onBack}>
	            <Text style={styles.backButtonText}>← Sessions</Text>
	          </TouchableOpacity>
	          <Text style={styles.title} numberOfLines={1}>
	            {sessionLabel}
	          </Text>
	          <View style={styles.headerButtons}>
	            <SessionActionsBar
	              pinned={pinnedSessionActions}
	              onChangePinned={setPinnedSessionActions}
	              onAction={handleSessionAction}
	              isActionDisabled={(action) =>
	                sendInProgress && (action === 'reload' || action === 'resend')
	              }
	            />
	          </View>
	        </View>

	      {loadingMessages && (
	        <View style={styles.loadingContainer}>
	          <ActivityIndicator size="small" color="#007AFF" />
	          <Text style={styles.loadingText}>Loading messages...</Text>
	        </View>
	      )}
	
	      <ScrollView
	        style={styles.messagesContainer}
	        ref={scrollViewRef}
	        onContentSizeChange={() => {
	          if (shouldAutoScroll && scrollViewRef.current) {
	            scrollViewRef.current.scrollToEnd({ animated: false });
	            setShouldAutoScroll(false);
	          }
	        }}
	      >
        {messages.map((m) => (
          <MessageBubble key={m.index} index={m.index} message={m.message} />
        ))}
      </ScrollView>

	      <View style={styles.composer}>
        <TextInput
          style={styles.composerInput}
          placeholder="Type your message..."
          value={composeText}
          onChangeText={setComposeText}
          multiline
        />
        <View style={styles.composerButtonsRow}>
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton, styles.composerButton]}
            onPress={handleAppend}
            disabled={sendInProgress}
          >
            <Text style={styles.buttonTextSecondary}>Append</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton, styles.composerButton]}
            onPress={handleSend}
            disabled={sendInProgress}
          >
            <Text style={styles.buttonText}>Send</Text>
          </TouchableOpacity>
        </View>
	      </View>

	      <Modal
	        visible={messageLimitVisible}
	        transparent
	        animationType="fade"
	        onRequestClose={() => setMessageLimitVisible(false)}
	      >
	        <View style={styles.modalOverlay}>
	          <View style={styles.modalContent}>
	            <Text style={styles.modalTitle}>Message range</Text>
	            <Text style={styles.modalSubtitle}>
	              Python-style range (start:end). Example: -50: for last 50 messages.
	            </Text>
	            <View style={styles.rangeRow}>
	              <View style={styles.rangeInputContainer}>
	                <Text style={styles.rangeLabel}>Start</Text>
	                <TextInput
	                  style={styles.modalInput}
	                  value={rangeStartText}
	                  onChangeText={setRangeStartText}
	                  placeholder="e.g. -50"
	                  keyboardType="number-pad"
	                />
	              </View>
	              <View style={styles.rangeInputContainer}>
	                <Text style={styles.rangeLabel}>End</Text>
	                <TextInput
	                  style={styles.modalInput}
	                  value={rangeEndText}
	                  onChangeText={setRangeEndText}
	                  placeholder="optional"
	                  keyboardType="number-pad"
	                />
	              </View>
	            </View>
	            <View style={styles.modalButtonsRow}>
	              <TouchableOpacity
	                style={[styles.button, styles.secondaryButton, styles.modalButton]}
	                onPress={() => setMessageLimitVisible(false)}
	              >
	                <Text style={styles.buttonTextSecondary}>Cancel</Text>
	              </TouchableOpacity>
	              <TouchableOpacity
	                style={[styles.button, styles.primaryButton, styles.modalButton]}
	                onPress={applyMessageLimitAndReload}
	              >
	                <Text style={styles.buttonText}>Apply</Text>
	              </TouchableOpacity>
	            </View>
	            {lastReloadAt && (
	              <Text style={styles.modalHelperText}>
	                Last reload at {lastReloadAt.toLocaleTimeString()}
	              </Text>
	            )}
	          </View>
	        </View>
	      </Modal>

	      <Modal
	        visible={deleteRangeVisible}
	        transparent
	        animationType="fade"
	        onRequestClose={() => setDeleteRangeVisible(false)}
	      >
	        <View style={styles.modalOverlay}>
	          <View style={styles.modalContent}>
	            <Text style={styles.modalTitle}>Delete range</Text>
	            <Text style={styles.modalSubtitle}>
	              Python-style range (start:end). Messages in this range will be removed.
	            </Text>
	            <View style={styles.rangeRow}>
	              <View style={styles.rangeInputContainer}>
	                <Text style={styles.rangeLabel}>Start</Text>
	                <TextInput
	                  style={styles.modalInput}
	                  value={deleteRangeStartText}
	                  onChangeText={setDeleteRangeStartText}
	                  placeholder="e.g. 0 or -10"
	                  keyboardType="number-pad"
	                />
	              </View>
	              <View style={styles.rangeInputContainer}>
	                <Text style={styles.rangeLabel}>End</Text>
	                <TextInput
	                  style={styles.modalInput}
	                  value={deleteRangeEndText}
	                  onChangeText={setDeleteRangeEndText}
	                  placeholder="optional"
	                  keyboardType="number-pad"
	                />
	              </View>
	            </View>
	            <View style={styles.modalButtonsRow}>
	              <TouchableOpacity
	                style={[styles.button, styles.secondaryButton, styles.modalButton]}
	                onPress={() => setDeleteRangeVisible(false)}
	              >
	                <Text style={styles.buttonTextSecondary}>Cancel</Text>
	              </TouchableOpacity>
	              <TouchableOpacity
	                style={[styles.button, styles.primaryButton, styles.modalButton]}
	                onPress={confirmDeleteRange}
	              >
	                <Text style={styles.buttonText}>Delete</Text>
	              </TouchableOpacity>
	            </View>
	          </View>
	        </View>
	      </Modal>

	      {renderSessionActionsMenu()}
	      <Modal
	        visible={agentModalVisible}
	        transparent
	        animationType="fade"
	        onRequestClose={() => setAgentModalVisible(false)}
	      >
	        <View style={styles.modalOverlay}>
	          <View style={styles.modalContent}>
	            <Text style={styles.modalTitle}>Switch agent</Text>
	            {agentLoading && (
	              <View style={styles.loadingContainer}>
	                <ActivityIndicator size="small" color="#007AFF" />
	                <Text style={styles.loadingText}>Loading agents...</Text>
	              </View>
	            )}
	            {!agentLoading && availableAgents.length === 0 && (
	              <Text style={styles.modalSubtitle}>No agents available.</Text>
	            )}
	            {!agentLoading && availableAgents.length > 0 && (
	              <ScrollView style={styles.agentList}>
	                {availableAgents.map((agentId) => {
	                  const selected = sessionAgentId === agentId;
	                  return (
	                    <TouchableOpacity
	                      key={agentId}
	                      style={[styles.agentItem, selected && styles.agentItemSelected]}
	                      onPress={() => handleSwitchAgent(agentId)}
	                    >
	                      <Text style={styles.agentItemText}>{agentId}</Text>
	                      {selected && <Icon name="check" size={16} color="#34C759" />}
	                    </TouchableOpacity>
	                  );
	                })}
	              </ScrollView>
	            )}
	            <View style={styles.modalButtonsRow}>
	              <TouchableOpacity
	                style={[styles.button, styles.secondaryButton, styles.modalButton]}
	                onPress={() => setAgentModalVisible(false)}
	              >
	                <Text style={styles.buttonTextSecondary}>Close</Text>
	              </TouchableOpacity>
	            </View>
	          </View>
	        </View>
	      </Modal>
	    </View>
	    </KeyboardAvoidingView>
  );
};

	const styles = StyleSheet.create({
	  keyboardAvoiding: {
	    flex: 1,
	  },
	  container: {
	    flex: 1,
	  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  backButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  backButtonText: {
    color: '#007AFF',
    fontSize: 14,
  },
  title: {
    flex: 1,
    textAlign: 'center',
    fontSize: 18,
    fontWeight: '600',
  },
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginLeft: 4,
  },
  button: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    marginLeft: 6,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#E5E5EA',
  },
  smallButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginLeft: 8,
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
  messagesContainer: {
    flex: 1,
    marginBottom: 8,
  },
  composer: {
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    paddingTop: 8,
  },
  composerInput: {
    minHeight: 60,
    maxHeight: 120,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 14,
    marginBottom: 8,
  },
  composerButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  composerButton: {
    minWidth: 90,
    alignItems: 'center',
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
  modalInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    fontSize: 14,
    marginBottom: 12,
  },
  modalButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 4,
  },
  modalButton: {
    minWidth: 90,
    alignItems: 'center',
  },
  modalHelperText: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'right',
  },
	  rangeRow: {
	    flexDirection: 'row',
	    justifyContent: 'space-between',
	    marginBottom: 12,
	    marginTop: 8,
	  },
	  rangeInputContainer: {
	    flex: 1,
	    marginRight: 8,
	  },
	  rangeLabel: {
	    fontSize: 12,
	    color: '#8E8E93',
	    marginBottom: 4,
	  },
	  menuOverlay: {
	    flex: 1,
	    backgroundColor: 'rgba(0, 0, 0, 0.3)',
	    justifyContent: 'center',
	    alignItems: 'center',
	  },
	  menuContent: {
	    width: '80%',
	    backgroundColor: '#FFFFFF',
	    borderRadius: 12,
	    paddingVertical: 8,
	  },
	  menuItem: {
	    flexDirection: 'row',
	    alignItems: 'center',
	    justifyContent: 'space-between',
	    paddingHorizontal: 12,
	    paddingVertical: 8,
	  },
	  menuItemLeft: {
	    flexDirection: 'row',
	    alignItems: 'center',
	  },
	  menuItemText: {
	    marginLeft: 8,
	    fontSize: 14,
	    color: '#000000',
	  },
	  pinButton: {
	    paddingHorizontal: 4,
	    paddingVertical: 4,
	  },
	  agentList: {
	    maxHeight: 220,
	    marginTop: 8,
	    marginBottom: 8,
	  },
	  agentItem: {
	    flexDirection: 'row',
	    alignItems: 'center',
	    justifyContent: 'space-between',
	    paddingVertical: 8,
	    paddingHorizontal: 10,
	    borderRadius: 8,
	    borderWidth: 1,
	    borderColor: '#E5E5EA',
	    marginBottom: 6,
	  },
	  agentItemSelected: {
	    borderColor: '#007AFF',
	    backgroundColor: 'rgba(0, 122, 255, 0.08)',
	  },
	  agentItemText: {
	    fontSize: 14,
	    color: '#000000',
	  },
});

export default SessionChatScreen;
