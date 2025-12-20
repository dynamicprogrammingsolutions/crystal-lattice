import React, { useCallback, useEffect, useRef, useState } from 'react';
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
import Icon from 'react-native-vector-icons/Feather';
import type { ConnectionAdapter } from '../App';
import { apiAppendMessage, apiListMessages, apiSend, type IndexedMessage } from './api';
import MessageBubble from './components/MessageBubble';

interface SessionChatScreenProps {
  adapter: ConnectionAdapter;
  sessionId: string;
  onBack: () => void;
}

const SessionChatScreen: React.FC<SessionChatScreenProps> = ({ adapter, sessionId, onBack }) => {
  const [messages, setMessages] = useState<IndexedMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sendInProgress, setSendInProgress] = useState(false);
  const [composeText, setComposeText] = useState('');
  const [messageLimit, setMessageLimit] = useState<number | 'all'>(25);
  const [limitInput, setLimitInput] = useState('25');
  const [lastReloadAt, setLastReloadAt] = useState<Date | null>(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const scrollViewRef = useRef<ScrollView | null>(null);

  const loadMessages = useCallback(async () => {
    setLoadingMessages(true);
    try {
      let start: number | undefined;
      if (messageLimit !== 'all' && messageLimit > 0) {
        start = -messageLimit;
      }
      const list = await apiListMessages(adapter, sessionId, start);
      setMessages(list);
      setLastReloadAt(new Date());
    } catch (err: any) {
      console.log('Failed to load messages', err);
      const message = err?.message || 'Failed to load messages';
      Alert.alert('Error', message);
    } finally {
      setLoadingMessages(false);
    }
  }, [adapter, sessionId, messageLimit]);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  const handleApplyLimit = () => {
    const trimmed = limitInput.trim();
    if (!trimmed) {
      setMessageLimit('all');
      return;
    }
    const parsed = parseInt(trimmed, 10);
    if (Number.isNaN(parsed) || parsed <= 0) {
      setMessageLimit('all');
    } else {
      setMessageLimit(parsed);
    }
  };

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

  const handleResend = async () => {
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
  };

  const sessionLabel = `Session ${sessionId.slice(0, 8)}`;

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Text style={styles.backButtonText}>← Sessions</Text>
        </TouchableOpacity>
        <Text style={styles.title} numberOfLines={1}>
          {sessionLabel}
        </Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity
            style={[styles.iconButton]}
            onPress={loadMessages}
            disabled={sendInProgress}
          >
            <Icon name="refresh-ccw" size={18} color="#007AFF" />
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.iconButton]}
            onPress={handleResend}
            disabled={sendInProgress}
          >
            <Icon name="repeat" size={18} color="#007AFF" />
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.iconButton]}
            onPress={() => {
              if (messageLimit === 'all') {
                setLimitInput('');
              } else {
                setLimitInput(String(messageLimit));
              }
              setSettingsVisible(true);
            }}
          >
            <Icon name="settings" size={18} color="#007AFF" />
          </TouchableOpacity>
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
          if (scrollViewRef.current) {
            scrollViewRef.current.scrollToEnd({ animated: false });
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
        visible={settingsVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setSettingsVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Message limit</Text>
            <Text style={styles.modalSubtitle}>
              {messageLimit === 'all'
                ? 'Currently showing all loaded messages.'
                : `Currently showing last ${messageLimit} messages.`}
            </Text>
            <TextInput
              style={styles.modalInput}
              value={limitInput}
              onChangeText={setLimitInput}
              placeholder="Leave empty for all"
              keyboardType="number-pad"
            />
            <View style={styles.modalButtonsRow}>
              <TouchableOpacity
                style={[styles.button, styles.secondaryButton, styles.modalButton]}
                onPress={() => setSettingsVisible(false)}
              >
                <Text style={styles.buttonTextSecondary}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.button, styles.primaryButton, styles.modalButton]}
                onPress={() => {
                  handleApplyLimit();
                  setSettingsVisible(false);
                }}
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
});

export default SessionChatScreen;
