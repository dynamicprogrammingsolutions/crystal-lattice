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
import AsyncStorage from '@react-native-async-storage/async-storage';
import Clipboard from '@react-native-clipboard/clipboard';
import Icon from 'react-native-vector-icons/Feather';
import type { ConnectionAdapter } from '../App';
import {
  apiAppendMessage,
  apiDeleteMessagesByIndices,
  apiDeleteMessagesByRange,
  apiForkSession,
  apiGetSessionAgent,
  apiListAgents,
  apiListMessages,
  apiModifyMessage,
  apiSend,
  apiSwitchSessionAgent,
  type ApiMessage,
  type IndexedMessage,
} from './api';
import MessageBubble from './components/MessageBubble';
import SessionActionsBar from './components/SessionActionsBar';
import { SESSION_ACTIONS, type SessionActionKey } from './sessionActions';
import { ALL_MESSAGE_ACTIONS, type MessageActionKey } from './messageActions';
import { selectDisplayContent } from './messageUtils';

interface SessionChatScreenProps {
  adapter: ConnectionAdapter | null;
  connectionId: string | null;
  sessionId: string;
  cachedMessages: IndexedMessage[] | null;
  lastLoadedAt: number | null;
  isActive: boolean;
  onUpdateCache: (messages: IndexedMessage[]) => void;
  onBack: () => void;
  onNavigateToSession?: (sessionId: string) => void;
  initialComposeText: string;
  initialScrollOffset: number;
  onUpdateUiState: (composeText: string, scrollOffset: number) => void;
}

const STORAGE_KEY_SESSION_ACTIONS = 'clc_pinned_session_actions_v1';
const STORAGE_KEY_MESSAGE_ACTIONS = 'clc_pinned_message_actions_by_role_v1';

const SessionChatScreen: React.FC<SessionChatScreenProps> = ({
  adapter,
  connectionId,
  sessionId,
  cachedMessages,
  lastLoadedAt,
  isActive,
  onUpdateCache,
  onBack,
  onNavigateToSession,
  initialComposeText,
  initialScrollOffset,
  onUpdateUiState,
}) => {
  const [messages, setMessages] = useState<IndexedMessage[]>(cachedMessages ?? []);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sendInProgress, setSendInProgress] = useState(false);
  const [composeText, setComposeText] = useState(initialComposeText ?? '');
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
  const [pinnedMessageActionsByRole, setPinnedMessageActionsByRole] = useState<
    Record<string, MessageActionKey[]>
  >({});
  const [hasAutoLoaded, setHasAutoLoaded] = useState(false);
  const [messageViewModeByIndex, setMessageViewModeByIndex] = useState<
    Record<number, 'markdown' | 'raw'>
  >({});
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [shouldAutoScroll, setShouldAutoScroll] = useState(false);
  const scrollViewRef = useRef<ScrollView | null>(null);
  const scrollOffsetRef = useRef<number>(initialScrollOffset || 0);
  const composeTextRef = useRef<string>(initialComposeText ?? '');

  useEffect(() => {
    composeTextRef.current = composeText;
  }, [composeText]);

  useEffect(() => {
    const loadPinnedFromStorage = async () => {
      try {
        const [sessionRaw, messageRaw] = await Promise.all([
          AsyncStorage.getItem(STORAGE_KEY_SESSION_ACTIONS),
          AsyncStorage.getItem(STORAGE_KEY_MESSAGE_ACTIONS),
        ]);

        if (sessionRaw) {
          try {
            const parsed = JSON.parse(sessionRaw);
            if (Array.isArray(parsed)) {
              const valid = parsed.filter((key: any) =>
                Object.prototype.hasOwnProperty.call(SESSION_ACTIONS, key),
              );
              if (valid.length > 0 || parsed.length === 0) {
                // Allow empty array (no pinned session actions).
                setPinnedSessionActions(valid as SessionActionKey[]);
              }
            }
          } catch (err) {
            console.log('Failed to parse stored pinned session actions', err);
          }
        }

        if (messageRaw) {
          try {
            const parsed = JSON.parse(messageRaw);
            if (parsed && typeof parsed === 'object') {
              const next: Record<string, MessageActionKey[]> = {};
              Object.entries(parsed).forEach(([role, value]) => {
                if (Array.isArray(value)) {
                  const filtered = (value as any[]).filter((key) =>
                    ALL_MESSAGE_ACTIONS.some((def) => def.key === key),
                  );
                  next[role] = filtered as MessageActionKey[];
                }
              });
              setPinnedMessageActionsByRole(next);
            }
          } catch (err) {
            console.log('Failed to parse stored pinned message actions', err);
          }
        }
      } catch (err) {
        console.log('Failed to load pinned actions from storage', err);
      }
    };

    loadPinnedFromStorage();
  }, []);

  const applyMessageLimitAndReload = () => {
    setMessageLimitVisible(false);
    loadMessages();
  };

  const loadMessages = useCallback(async () => {
    if (!adapter) {
      const message = 'No active connection';
      Alert.alert('Error', message);
      return;
    }
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
		      onUpdateCache(list);
    } catch (err: any) {
      console.log('Failed to load messages', err);
      const message = err?.message || 'Failed to load messages';
      Alert.alert('Error', message);
    } finally {
      setLoadingMessages(false);
	    }
  }, [adapter, sessionId, rangeStartText, rangeEndText, onUpdateCache]);

  useEffect(() => {
    setMessages(cachedMessages ?? []);
    if (cachedMessages && lastLoadedAt) {
      setLastReloadAt(new Date(lastLoadedAt));
    }
  }, [cachedMessages, connectionId, sessionId, lastLoadedAt]);

  useEffect(() => {
    // Restore initial scroll position once on mount when a cached
    // offset is available.
    if (initialScrollOffset && scrollViewRef.current) {
      scrollViewRef.current.scrollTo({ x: 0, y: initialScrollOffset, animated: false });
    }
  }, [initialScrollOffset]);

  useEffect(() => {
    if (!cachedMessages && adapter) {
      loadMessages();
    }
  }, [adapter, cachedMessages, loadMessages]);

  useEffect(() => {
    const saveSessionPinned = async () => {
      try {
        await AsyncStorage.setItem(
          STORAGE_KEY_SESSION_ACTIONS,
          JSON.stringify(pinnedSessionActions),
        );
      } catch (err) {
        console.log('Failed to save pinned session actions', err);
      }
    };
    saveSessionPinned();
  }, [pinnedSessionActions]);

  useEffect(() => {
    const saveMessagePinned = async () => {
      try {
        await AsyncStorage.setItem(
          STORAGE_KEY_MESSAGE_ACTIONS,
          JSON.stringify(pinnedMessageActionsByRole),
        );
      } catch (err) {
        console.log('Failed to save pinned message actions', err);
      }
    };
    saveMessagePinned();
  }, [pinnedMessageActionsByRole]);

  useEffect(() => {
    // Persist UI state when this screen is unmounted.
    return () => {
      onUpdateUiState(composeTextRef.current, scrollOffsetRef.current);
    };
  }, [onUpdateUiState]);

  useEffect(() => {
    if (!isActive) return;
    if (!adapter) return;

    const now = Date.now();
    const isStale = !lastLoadedAt || now - lastLoadedAt > 30000;

    if (!hasAutoLoaded || isStale || !cachedMessages) {
      loadMessages().catch(() => {
        // Error already handled inside loadMessages.
      });
      setHasAutoLoaded(true);
    }
  }, [isActive, adapter, lastLoadedAt, hasAutoLoaded, loadMessages, cachedMessages]);

	  const handleAppend = async () => {
    const text = composeText.trim();
    if (!text) {
      return;
    }
    if (!adapter) {
      Alert.alert('No connection', 'Connect to a server to append messages.');
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
    if (!adapter) {
      Alert.alert('No connection', 'Connect to a server to send messages.');
      setSendInProgress(false);
      return;
    }
    try {
      if (text) {
        await apiAppendMessage(adapter, sessionId, 'user', text);
      }
      await apiSend(adapter, sessionId);
      await loadMessages();
        setComposeText('');
        onUpdateUiState('', scrollOffsetRef.current);
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
    if (!adapter) {
      Alert.alert('No connection', 'Connect to a server to delete messages.');
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
	    if (!adapter) {
	      Alert.alert('No connection', 'Connect to a server to switch agent.');
	      return;
	    }
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
      if (!adapter) {
        Alert.alert('No connection', 'Connect to a server to resend.');
        setSendInProgress(false);
        return;
      }
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
      if (!adapter) {
        Alert.alert('No connection', 'Connect to a server to copy sessions.');
        return;
      }
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

  const getPinnedActionsForRole = (role: string): MessageActionKey[] => {
    const allowedKeys = ALL_MESSAGE_ACTIONS
      .filter((def) => def.allowedRoles.includes(role))
      .map((def) => def.key as MessageActionKey);

    const existing = pinnedMessageActionsByRole[role];
    if (Array.isArray(existing)) {
      // Respect an explicit empty list (user chose to pin nothing).
      return existing.filter((key) => allowedKeys.includes(key));
    }

    const defaults: MessageActionKey[] = [];
    ALL_MESSAGE_ACTIONS.forEach((def) => {
      if (def.defaultPinnedRoles.includes(role) && def.allowedRoles.includes(role)) {
        defaults.push(def.key as MessageActionKey);
      }
    });
    return defaults;
  };

  const handleChangePinnedForRole = (role: string, pinned: MessageActionKey[]) => {
    setPinnedMessageActionsByRole((prev) => ({ ...prev, [role]: pinned }));
  };

  const handleStartEditMessage = (index: number, message: ApiMessage) => {
    const role = message.role || 'unknown';
    if (role === 'tool') {
      // Tool results cannot be modified.
      return;
    }
    const content = typeof message.content === 'string' ? message.content : '';
    setEditingIndex(index);
    setEditingText(content);
  };

  const handleSubmitEditMessage = async (
    index: number,
    _message: ApiMessage,
    newText: string,
  ) => {
    const trimmed = newText.trim();
    if (!trimmed) {
      Alert.alert('Invalid content', 'Message content cannot be empty.');
      return;
    }
    if (!adapter) {
      Alert.alert('No connection', 'Connect to a server to modify messages.');
      return;
    }
    try {
      await apiModifyMessage(adapter, sessionId, index, trimmed);
      setEditingIndex(null);
      setEditingText('');
      await loadMessages();
    } catch (err: any) {
      console.log('Failed to modify message', err);
      const msg = err?.message || 'Failed to modify message';
      Alert.alert('Error', msg);
    }
  };

  const handleCancelEditMessage = () => {
    setEditingIndex(null);
    setEditingText('');
  };

  const handleMessageAction = async (
    action: MessageActionKey,
    index: number,
    message: ApiMessage,
  ) => {
    if (action === 'delete') {
      const label = `Delete message [${index}]?`;
      const confirmed = await new Promise<boolean>((resolve) => {
        Alert.alert('Confirm delete', label, [
          { text: 'Cancel', style: 'cancel', onPress: () => resolve(false) },
          { text: 'Delete', style: 'destructive', onPress: () => resolve(true) },
        ]);
      });
      if (!confirmed) return;
      if (!adapter) {
        Alert.alert('No connection', 'Connect to a server to delete messages.');
        return;
      }
      try {
        await apiDeleteMessagesByIndices(adapter, sessionId, [index]);
        await loadMessages();
      } catch (err: any) {
        console.log('Failed to delete message', err);
        const msg = err?.message || 'Failed to delete message';
        Alert.alert('Error', msg);
      }
      return;
    }

    if (action === 'modify') {
      handleStartEditMessage(index, message);
      return;
    }

    if (action === 'fork') {
      if (!adapter) {
        Alert.alert('No connection', 'Connect to a server to fork sessions.');
        return;
      }
      try {
        const result = await apiForkSession(adapter, sessionId, index);
        const newId = result.session.session_id;
        if (onNavigateToSession && typeof newId === 'string' && newId) {
          onNavigateToSession(newId);
        }
      } catch (err: any) {
        console.log('Failed to fork session from message', err);
        const msg = err?.message || 'Failed to fork session';
        Alert.alert('Error', msg);
      }
      return;
    }

    if (action === 'toggleMarkdown') {
      const role = message.role || 'unknown';
      if (role !== 'assistant') {
        return;
      }
      setMessageViewModeByIndex((prev) => {
        const current = prev[index] ?? 'markdown';
        const next: 'markdown' | 'raw' = current === 'markdown' ? 'raw' : 'markdown';
        return { ...prev, [index]: next };
      });
      return;
    }

    if (action === 'copy') {
      const content = selectDisplayContent(message);
      if (!content) {
        Alert.alert('Nothing to copy', 'This message has no text content.');
        return;
      }
      Clipboard.setString(content);
      Alert.alert('Copied', 'Message content copied to clipboard.');
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
	      {messages.map((m) => {
	        const role = m.message.role || 'unknown';
	        const allowedActions = ALL_MESSAGE_ACTIONS
	          .filter((def) => def.allowedRoles.includes(role))
	          .map((def) => def.key as MessageActionKey);
	        const pinnedForRole = getPinnedActionsForRole(role);
	        const isEditing = editingIndex === m.index;
	        const defaultModeForRole: 'markdown' | 'raw' =
	          role === 'assistant' ? 'markdown' : 'raw';
	        const renderMode = messageViewModeByIndex[m.index] ?? defaultModeForRole;
	        return (
	          <MessageBubble
	            key={m.index}
	            index={m.index}
	            message={m.message}
	            pinnedActions={pinnedForRole}
	            allowedActions={allowedActions}
	            onAction={handleMessageAction}
	            onChangePinnedForRole={handleChangePinnedForRole}
	            isEditing={isEditing}
	            editingText={isEditing ? editingText : undefined}
	            onChangeEditingText={isEditing ? setEditingText : undefined}
	            onSubmitEdit={handleSubmitEditMessage}
	            onCancelEdit={handleCancelEditMessage}
	            renderMode={renderMode}
	          />
	        );
	      })}
	      </ScrollView>

	      <View style={styles.composer}>
        <TextInput
          style={styles.composerInput}
          placeholder="Type your message..."
          value={composeText}
          onChangeText={(text) => {
            setComposeText(text);
          }}
          onBlur={() => {
            onUpdateUiState(composeTextRef.current, scrollOffsetRef.current);
          }}
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
                  keyboardType="default"
                />
	              </View>
	              <View style={styles.rangeInputContainer}>
	                <Text style={styles.rangeLabel}>End</Text>
                <TextInput
                  style={styles.modalInput}
                  value={rangeEndText}
                  onChangeText={setRangeEndText}
                  placeholder="optional"
                  keyboardType="default"
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
                  keyboardType="default"
                />
	              </View>
	              <View style={styles.rangeInputContainer}>
	                <Text style={styles.rangeLabel}>End</Text>
                <TextInput
                  style={styles.modalInput}
                  value={deleteRangeEndText}
                  onChangeText={setDeleteRangeEndText}
                  placeholder="optional"
                  keyboardType="default"
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
