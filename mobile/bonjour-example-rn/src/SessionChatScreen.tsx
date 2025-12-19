import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
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
          <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={loadMessages}>
            <Text style={styles.buttonTextSecondary}>Reload</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={handleResend}
            disabled={sendInProgress}
          >
            <Text style={styles.buttonText}>Resend</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.limitRow}>
        <Text style={styles.limitLabel}>Show last</Text>
        <TextInput
          style={styles.limitInput}
          value={limitInput}
          onChangeText={setLimitInput}
          placeholder="e.g., 25"
          keyboardType="number-pad"
        />
        <Text style={styles.limitLabel}>messages</Text>
        <TouchableOpacity style={[styles.button, styles.secondaryButton, styles.smallButton]} onPress={handleApplyLimit}>
          <Text style={styles.buttonTextSecondary}>Apply</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.limitHelperRow}>
        <Text style={styles.helperText}>
          {messageLimit === 'all'
            ? 'Showing all loaded messages'
            : `Showing last ${messageLimit} messages`}
        </Text>
        {lastReloadAt && (
          <Text style={styles.helperText}>
            Reloaded at {lastReloadAt.toLocaleTimeString()}
          </Text>
        )}
      </View>

      {loadingMessages && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.loadingText}>Loading messages...</Text>
        </View>
      )}

      <ScrollView style={styles.messagesContainer}>
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
  limitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  limitLabel: {
    fontSize: 14,
    color: '#000000',
  },
  limitInput: {
    marginHorizontal: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    backgroundColor: '#FFFFFF',
    minWidth: 60,
    fontSize: 14,
  },
  limitHelperRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  helperText: {
    fontSize: 12,
    color: '#8E8E93',
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
});

export default SessionChatScreen;
