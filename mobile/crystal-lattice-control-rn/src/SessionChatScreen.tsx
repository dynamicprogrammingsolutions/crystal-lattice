import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Clipboard from '@react-native-clipboard/clipboard';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  deriveChatStatusBarParts,
  deriveSessionListPresentationFromGroups,
  filterFooterElements,
  filterStatusBarElements,
  groupSessionListFields,
  runApplicationAction,
  selectLastAssistantMessage,
} from '@crystal-lattice/frontend-sdk';
import { useChatController, useAgentsController } from '@crystal-lattice/frontend-sdk-react';
import {
  useHydrateControllerFromCache,
  useSessionUiSchemaController,
} from '@crystal-lattice/frontend-sdk-react';
import {
  type ApiMessage,
  type IndexedMessage,
  type ActionUiElement,
  type UiSchemaElement,
  type SessionSummary,
} from './api';
import MessageBubble from './components/MessageBubble';
import DebugEventsView from './components/DebugEventsView';
import SessionActionsBar from './components/SessionActionsBar';
import SessionSettingsModal from './components/SessionSettingsModal';
import ApplicationActionDialog from './components/ApplicationActionDialog';
import AgentSwitchModal from './components/AgentSwitchModal';
import { SESSION_ACTIONS, type SessionActionKey } from './sessionActions';
import { ALL_MESSAGE_ACTIONS, type MessageActionKey } from './messageActions';
import { selectDisplayContent } from './messageUtils';
import {
  createChatScrollAnchor,
  isChatScrollAnchor,
  PINNED_TO_BOTTOM_THRESHOLD_PX,
  type ChatScrollAnchor,
} from './chatScroll';
import { useTheme, type Theme } from './theme';
import { useApplicationPlugins } from './ApplicationPluginsContext';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import { usePluginActionDialog } from './usePluginActionDialog';
import type { Event } from './eventsTypes';

interface SessionChatScreenProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  isActive: boolean;
  sessionId: string;
  sessionSummary: SessionSummary | null;
  cachedMessages: IndexedMessage[] | null;
  lastLoadedAt: number | null;
  cachedEventsCursorId: string | null;
  cachedActiveRequestId: string | null;
  onUpdateCache: (
    messages: IndexedMessage[],
    eventsCursorId: string | null,
    activeRequestId: string | null,
  ) => void;
  onBack: () => void;
  onNavigateToSession?: (sessionId: string) => void;
  initialComposeText: string;
  initialScrollAnchor: ChatScrollAnchor | null;
  onSaveComposeText: (composeText: string) => void;
  onSaveScrollAnchor: (scrollAnchor: ChatScrollAnchor) => void;
}

const STORAGE_KEY_SESSION_ACTIONS = 'clc_pinned_session_actions_v1';
const STORAGE_KEY_MESSAGE_ACTIONS = 'clc_pinned_message_actions_by_role_v1';

type PluginActionContext =
  | { kind: 'session'; sessionSummary: SessionSummary | null }
  | { kind: 'message'; index: number; message: ApiMessage; sessionSummary: SessionSummary | null };

const SessionChatScreen: React.FC<SessionChatScreenProps> = ({
  backend,
  connectionId,
  isActive,
  sessionId,
  sessionSummary,
  cachedMessages,
  lastLoadedAt,
  cachedEventsCursorId,
  cachedActiveRequestId,
  onUpdateCache,
  onBack,
  onNavigateToSession,
  initialComposeText,
  initialScrollAnchor,
  onSaveComposeText,
  onSaveScrollAnchor,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [sendInProgress, setSendInProgress] = useState(false);
  const [composeText, setComposeText] = useState(initialComposeText ?? '');
  const [rangeStartText, setRangeStartText] = useState('-50');
  const [rangeEndText, setRangeEndText] = useState('');
  const [lastReloadAt, setLastReloadAt] = useState<Date | null>(null);
  const [messageLimitVisible, setMessageLimitVisible] = useState(false);
  const [deleteRangeVisible, setDeleteRangeVisible] = useState(false);
  const [deleteRangeStartText, setDeleteRangeStartText] = useState('');
  const [deleteRangeEndText, setDeleteRangeEndText] = useState('');
  const defaultPinnedSessionActions: SessionActionKey[] = Object.values(SESSION_ACTIONS)
    .filter((def) => def.defaultPinned)
    .map((def) => def.key);
  const { pinned: pinnedSessionActions, setPinned: setPinnedSessionActions } =
    usePersistentPinnedActions<SessionActionKey>(
      STORAGE_KEY_SESSION_ACTIONS,
      defaultPinnedSessionActions,
    );
  const { controller: agentsController, state: agentsState } = useAgentsController({
    backend,
    cacheKey: connectionId ?? 'default',
    enabled: !!(backend && isActive),
  });
  const availableAgents = agentsState?.agents ?? [];
  const agentsLoading = agentsState?.loading ?? false;
  const [agentSwitchInProgress, setAgentSwitchInProgress] = useState(false);
  const [sessionAgentId, setSessionAgentId] = useState<string | null>(null);
  const [agentModalVisible, setAgentModalVisible] = useState(false);
  const [pinnedMessageActionsByRole, setPinnedMessageActionsByRole] = useState<
    Record<string, MessageActionKey[]>
  >({});
  const [messageViewModeByIndex, setMessageViewModeByIndex] = useState<
    Record<number, 'markdown' | 'raw'>
  >({});
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [debugVisible, setDebugVisible] = useState(false);
  const [debugEvents, setDebugEvents] = useState<Event[]>([]);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [pluginActionInProgress, setPluginActionInProgress] = useState(false);
  const {
    actionsById,
    sessionActions: pluginSessionActions,
    messageActions: pluginMessageActions,
    sessionListFields,
  } = useApplicationPlugins();

  type ChatRow =
    | { kind: 'status'; key: string; parts: string[] }
    | { kind: 'stream'; key: string }
    | { kind: 'message'; key: string; indexedMessage: IndexedMessage };

  const listRef = useRef<FlatList<ChatRow> | null>(null);
  const composeTextRef = useRef<string>(initialComposeText ?? '');
  const onSaveComposeTextRef = useRef(onSaveComposeText);
  const onSaveScrollAnchorRef = useRef(onSaveScrollAnchor);
  const bottomGapPxRef = useRef<number>(0);
  const pinnedToBottomRef = useRef<boolean>(true);
  const initialScrollAnchorRef = useRef<ChatScrollAnchor | null>(
    isChatScrollAnchor(initialScrollAnchor) ? initialScrollAnchor : null,
  );
  const hasRestoredScrollRef = useRef(false);
  const lastCacheSnapshotRef = useRef<{
    messagesRef: IndexedMessage[] | null;
    activeRequestId: string | null;
    dirty: boolean;
  } | null>(null);

  useEffect(() => {
    onSaveComposeTextRef.current = onSaveComposeText;
  }, [onSaveComposeText]);

  useEffect(() => {
    onSaveScrollAnchorRef.current = onSaveScrollAnchor;
  }, [onSaveScrollAnchor]);

  useEffect(() => {
    if (hasRestoredScrollRef.current) {
      return;
    }
    initialScrollAnchorRef.current = isChatScrollAnchor(initialScrollAnchor)
      ? initialScrollAnchor
      : null;
  }, [initialScrollAnchor]);

  const appendEventsToDebugBuffer = useCallback((events: Event[]) => {
    if (!events || events.length === 0) return;
    setDebugEvents((prev) => {
      const combined = [...prev, ...events];
      const max = 200;
      return combined.length > max ? combined.slice(combined.length - max) : combined;
    });
  }, []);

  const { controller: chatController, state: chatState } = useChatController({
    backend,
    sessionId,
    initialMessages: cachedMessages ?? [],
    initialEventsCursorId: cachedEventsCursorId ?? null,
    initialActiveRequestId: cachedActiveRequestId ?? null,
    onEvents: appendEventsToDebugBuffer,
    eventsEnabled: !!(backend && sessionId && isActive),
  });

  const messages: IndexedMessage[] = chatState?.messages ?? cachedMessages ?? [];
  const streamingRow = chatState?.streamingRow ?? null;
  const activeRequestId = chatState?.activeRequestId ?? cachedActiveRequestId ?? null;
  const activeError = chatState?.requestError ?? null;
  const loadingMessages = chatState?.loading ?? false;
  const sessionDirty = chatState?.dirty ?? false;

  const hydrateChatCache = useCallback(
    (
      controller: NonNullable<typeof chatController>,
      cache: {
        messages: IndexedMessage[];
        eventsCursorId: string | null;
        activeRequestId: string | null;
        updatedAtMs: number | null;
      },
    ) => {
      controller.hydrateFromCache(cache);
    },
    [],
  );

  useHydrateControllerFromCache({
    controller: chatController,
    cache:
      cachedMessages != null
        ? {
            messages: cachedMessages,
            eventsCursorId: cachedEventsCursorId ?? null,
            activeRequestId: cachedActiveRequestId ?? null,
            updatedAtMs: lastLoadedAt ?? null,
          }
        : null,
    hydrate: hydrateChatCache,
  });

  useEffect(() => {
    if (!chatController) {
      return;
    }
    chatController.setHistoryRangeFromRangeText({
      startText: rangeStartText,
      endText: rangeEndText,
    });
  }, [chatController, rangeStartText, rangeEndText]);

  useEffect(() => {
    composeTextRef.current = composeText;
  }, [composeText]);

  useEffect(() => {
    if (!backend) return;
    agentsController?.ensureLoaded().catch(() => {
      // Non-fatal; status bar should still render.
    });
  }, [agentsController, backend]);

  useEffect(() => {
    const md = sessionSummary?.metadata;
    const raw = (md as any)?.agent_id;
    if (typeof raw === 'string' && raw.trim()) {
      setSessionAgentId(raw.trim());
    } else {
      setSessionAgentId(null);
    }
  }, [sessionId, sessionSummary]);

  useEffect(() => {
    const loadPinnedFromStorage = async () => {
      try {
        const messageRaw = await AsyncStorage.getItem(STORAGE_KEY_MESSAGE_ACTIONS);
        if (messageRaw) {
          try {
            const parsed = JSON.parse(messageRaw);
            if (parsed && typeof parsed === 'object') {
              const next: Record<string, MessageActionKey[]> = {};
              Object.entries(parsed).forEach(([role, value]) => {
                if (Array.isArray(value)) {
                  const filtered = (value as any[]).filter((key) => typeof key === 'string');
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
        console.log('Failed to load pinned message actions from storage', err);
      }
    };

    loadPinnedFromStorage();
  }, []);

  const { state: sessionUiSchemaState } = useSessionUiSchemaController({
    backend,
    cacheKey: connectionId ?? 'default',
    sessionId,
    enabled: !!(backend && isActive),
  });
  const uiSchemaElements = sessionUiSchemaState?.elements ?? [];

  const pluginSessionActionDefs = useMemo(
    () =>
      pluginSessionActions.map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
        defaultPinned: false,
      })),
    [pluginSessionActions],
  );

  const pluginMessageActionDefs = useMemo(
    () =>
      pluginMessageActions.map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
        defaultPinnedRoles: ['user', 'assistant', 'system', 'tool'],
        allowedRoles: ['user', 'assistant', 'system', 'tool'],
      })),
    [pluginMessageActions],
  );

  const applyMessageLimitAndReload = () => {
    setMessageLimitVisible(false);
    loadMessages();
  };

  const loadMessages = useCallback(async () => {
    if (!chatController) {
      const message = 'No active connection';
      Alert.alert('Error', message);
      return;
    }
    try {
	  await chatController.loadMessagesFromRangeText({
	    startText: rangeStartText,
	    endText: rangeEndText,
	  });
	  const snapshot = chatController.getCacheSnapshot();
	  setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
	  onUpdateCache(
	    snapshot.messages,
	    snapshot.eventsCursorId ?? null,
	    snapshot.activeRequestId ?? null,
	  );
    } catch (err: any) {
      console.log('Failed to load messages', err);
      const message = err?.message || 'Failed to load messages';
      Alert.alert('Error', message);
    }
  }, [chatController, rangeStartText, rangeEndText, onUpdateCache]);

  const {
    activeElement: activePluginDialogElement,
    context: activePluginDialogContext,
    openForElement: openPluginDialogForElement,
    handleSubmit: handleSubmitPluginDialog,
    handleCancel: handleCancelPluginDialog,
  } = usePluginActionDialog<PluginActionContext>(
    useCallback(
      async (
        element: ActionUiElement,
        context: PluginActionContext,
        dialogValues: Record<string, any> | undefined,
      ) => {
        if (!backend) {
          Alert.alert('No connection', 'Connect to a server to run actions.');
          return;
        }

        setPluginActionInProgress(true);
        try {
          const isMessage = context.kind === 'message';
	          const { ok, effects, errorMessage } = await runApplicationAction({
	            backend,
	            element,
	            actionsById,
	            context: {
	              sessionId,
	              messageContext: isMessage
	                ? { index: (context as any).index, message: (context as any).message }
	                : undefined,
	              dialogValues,
	            },
	            effects: {
	              currentSessionId: sessionId,
	              navigateOnCreatedSession: true,
	            },
	          });
	          if (!ok) {
	            Alert.alert('Action error', errorMessage || 'Failed to execute action');
	            return;
	          }

	          for (const effect of effects) {
	            if (effect.type === 'navigateToSession') {
	              if (onNavigateToSession) {
	                onNavigateToSession(effect.sessionId);
	              }
	              return;
	            }
	          }
	          if (effects.some((effect) => effect.type === 'reloadSession')) {
	            await loadMessages();
	          }
        } finally {
          setPluginActionInProgress(false);
        }
      },
      [backend, actionsById, sessionId, loadMessages, onNavigateToSession],
    ),
  );

  const closeOverlays = useCallback(() => {
    setMessageLimitVisible(false);
    setDeleteRangeVisible(false);
    setAgentModalVisible(false);
    setSettingsVisible(false);
    setDebugVisible(false);
    handleCancelPluginDialog();
  }, [handleCancelPluginDialog]);

  useEffect(() => {
    if (isActive) return;
    closeOverlays();
  }, [closeOverlays, isActive]);

  const handleBack = useCallback(() => {
    closeOverlays();
    onBack();
  }, [closeOverlays, onBack]);

  useEffect(() => {
    if (cachedMessages != null && lastLoadedAt) {
      setLastReloadAt(new Date(lastLoadedAt));
    }
  }, [cachedMessages, connectionId, sessionId, lastLoadedAt]);

  useEffect(() => {
    if (!cachedMessages && chatController) {
      loadMessages();
    }
  }, [chatController, cachedMessages, loadMessages]);

  useEffect(() => {
    if (!chatState) {
      return;
    }

    const prev = lastCacheSnapshotRef.current;
    const next = {
      messagesRef: chatState.messages,
      activeRequestId: chatState.activeRequestId ?? null,
      dirty: chatState.dirty ?? false,
    };

    const shouldPersist =
      prev == null ||
      prev.messagesRef !== next.messagesRef ||
      prev.activeRequestId !== next.activeRequestId ||
      prev.dirty !== next.dirty;
    if (!shouldPersist) {
      return;
    }

    lastCacheSnapshotRef.current = next;
    onUpdateCache(
      chatState.messages,
      chatState.eventsCursorId ?? null,
      chatState.activeRequestId ?? null,
    );
  }, [chatState?.messages, chatState?.activeRequestId, chatState?.dirty, onUpdateCache]);

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

  const persistScrollAnchor = useCallback(() => {
    onSaveScrollAnchorRef.current(
      createChatScrollAnchor({
        bottomGapPx: bottomGapPxRef.current,
        pinnedToBottom: pinnedToBottomRef.current,
      }),
    );
  }, []);

  const persistUiState = useCallback(() => {
    onSaveComposeTextRef.current(composeTextRef.current);
    persistScrollAnchor();
  }, [persistScrollAnchor]);

  useEffect(() => {
    return () => {
      persistUiState();
    };
  }, [persistUiState]);

  useEffect(() => {
    if (isActive) return;
    persistUiState();
  }, [isActive, persistUiState]);

  const handleAppend = async () => {
    const text = composeText.trim();
    if (!text) {
      return;
    }
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to append messages.');
      return;
    }
    setSendInProgress(true);
    try {
      await chatController.appendMessage({ role: 'user', content: text });
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
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to send messages.');
      setSendInProgress(false);
      return;
    }
    try {
      if (text) {
        await chatController.appendMessage({ role: 'user', content: text });
      }

      chatController.clearRequestState();
      await chatController.send();
	    setComposeText('');
	    onSaveComposeText('');
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
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to resend.');
      setSendInProgress(false);
      return;
    }
    try {
      chatController.clearRequestState();
      await chatController.send();
    } catch (err: any) {
      console.log('Failed to resend request', err);
      const message = err?.message || 'Failed to resend request';
      Alert.alert('Error', message);
    } finally {
      setSendInProgress(false);
    }
  };

  const handleCancel = async () => {
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to cancel.');
      return;
    }
    if (!activeRequestId) {
      Alert.alert('No active request', 'There is no active request to cancel.');
      return;
    }
    try {
      await chatController.cancelActiveRequest();
      // We rely on subsequent events (request_cancelled / request_completed)
      // to clear activeRequestId and update any streaming state.
    } catch (err: any) {
      console.log('Failed to cancel request', err);
      const message = err?.message || 'Failed to cancel request';
      Alert.alert('Error', message);
    }
  };
	  const confirmDeleteRange = async () => {
	    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to delete messages.');
      return;
    }
    try {
	      await chatController.deleteMessagesFromRangeText({
	        startText: deleteRangeStartText,
	        endText: deleteRangeEndText,
	      });
      setDeleteRangeVisible(false);
    } catch (err: any) {
	      const rawMessage = err?.message;
	      if (typeof rawMessage === 'string' && rawMessage.includes('Provide at least')) {
	        Alert.alert('Invalid range', rawMessage);
	        return;
	      }
	      console.log('Failed to delete range', err);
	      const message = rawMessage || 'Failed to delete messages';
	      Alert.alert('Error', message);
    }
  };

  const handleSwitchAgent = async (agentId: string) => {
	    if (!backend) {
	      Alert.alert('No connection', 'Connect to a server to switch agent.');
	      return;
	    }
	    try {
		      setAgentSwitchInProgress(true);
	      await backend.switchSessionAgent(sessionId, agentId);
	      setSessionAgentId(agentId && agentId.trim() ? agentId.trim() : null);
	      setAgentModalVisible(false);
	    } catch (err: any) {
	      console.log('Failed to switch agent', err);
	      const message = err?.message || 'Failed to switch agent';
	      Alert.alert('Error', message);
	    } finally {
		      setAgentSwitchInProgress(false);
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
      chatController?.clearRequestState();
      await loadMessages();
      return;
    }
    if (action === 'messageLimit') {
      setMessageLimitVisible(true);
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
      if (!backend) {
        Alert.alert('No connection', 'Connect to a server to switch agent.');
        return;
      }
      if (availableAgents.length === 0 || sessionAgentId === null) {
        try {
		        await agentsController?.ensureLoaded();
	        const current = await backend.getSessionAgent(sessionId);
	          setSessionAgentId(current && current.trim() ? current.trim() : null);
        } catch (err: any) {
          console.log('Failed to load agents', err);
          const message = err?.message || 'Failed to load agents';
          Alert.alert('Error', message);
        }
      }
      return;
    }
    if (action === 'debugEvents') {
      setDebugVisible(true);
      return;
    }
    if (action === 'settings') {
      setSettingsVisible(true);
      return;
    }

    const pluginEl = pluginSessionActions.find((el) => el.id === action);
    if (pluginEl) {
      openPluginDialogForElement(pluginEl, { kind: 'session', sessionSummary });
    }
  };

  const getPinnedActionsForRole = (role: string): MessageActionKey[] => {
    const allowedKeys = ALL_MESSAGE_ACTIONS
      .filter((def) => def.allowedRoles.includes(role))
      .map((def) => def.key as MessageActionKey);

    const existing = pinnedMessageActionsByRole[role];
    if (Array.isArray(existing)) {
      // Respect an explicit empty list (user chose to pin nothing).
      return existing;
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
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to modify messages.');
      return;
    }
    try {
      await chatController.modifyMessage(index, trimmed);
      setEditingIndex(null);
      setEditingText('');
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
    if (action === 'modify') {
      handleStartEditMessage(index, message);
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
    const pluginEl = pluginMessageActions.find((el) => el.id === action);
    if (pluginEl) {
      openPluginDialogForElement(pluginEl, {
        kind: 'message',
        index,
        message,
        sessionSummary,
      });
    }
  };


	  const sessionListFieldGroups = useMemo(
	    () => groupSessionListFields(sessionListFields || []),
	    [sessionListFields],
	  );

	  const sessionLabel = `Session ${sessionId.slice(0, 8)}`;

	  const sessionHeaderTitle = useMemo(() => {
	    if (!sessionSummary) {
	      return sessionLabel;
	    }
	    return deriveSessionListPresentationFromGroups(sessionSummary, sessionListFieldGroups).title;
	  }, [sessionSummary, sessionListFieldGroups, sessionLabel]);

	  const footerElements = useMemo(
	    () => filterFooterElements(uiSchemaElements),
	    [uiSchemaElements],
	  );

	  const statusBarElements = useMemo(
	    () => filterStatusBarElements(uiSchemaElements),
	    [uiSchemaElements],
	  );

	  const lastAssistantMessage = useMemo(
	    () => selectLastAssistantMessage({ messages, streamingRow }),
	    [messages, streamingRow],
	  );

	  const statusBarParts = useMemo(
	    () =>
	      deriveChatStatusBarParts({
	        sessionId,
	        sessionAgentId,
	        availableAgents,
	        lastAssistantMessage,
	        statusBarElements,
	      }),
	    [
	      sessionId,
	      sessionAgentId,
	      availableAgents,
	      lastAssistantMessage,
	      statusBarElements,
	    ],
	  );

	  const chatRows = useMemo<ChatRow[]>(() => {
	    const rows: ChatRow[] = [
	      { kind: 'status', key: 'row-status', parts: statusBarParts },
	      { kind: 'stream', key: 'row-stream' },
	    ];
	    for (let idx = messages.length - 1; idx >= 0; idx -= 1) {
	      const indexedMessage = messages[idx];
	      rows.push({
	        kind: 'message',
	        key: `msg-${indexedMessage.index}`,
	        indexedMessage,
	      });
	    }
	    return rows;
	  }, [messages, statusBarParts, streamingRow]);

	  const handleListScroll = useCallback((event: any) => {
	    const offset = event?.nativeEvent?.contentOffset?.y;
	    if (typeof offset !== 'number' || !Number.isFinite(offset)) {
	      return;
	    }
	    bottomGapPxRef.current = Math.max(0, offset);
	    pinnedToBottomRef.current =
	      bottomGapPxRef.current <= PINNED_TO_BOTTOM_THRESHOLD_PX;
	  }, []);

	  const maybeRestoreScroll = useCallback(() => {
	    if (hasRestoredScrollRef.current) {
	      return;
	    }
	    const list = listRef.current;
	    if (!list) {
	      return;
	    }
	
	    const anchor = initialScrollAnchorRef.current;
	    const offset = anchor && !anchor.pinnedToBottom ? anchor.bottomGapPx : 0;
	    list.scrollToOffset({ offset, animated: false });
	    bottomGapPxRef.current = offset;
	    pinnedToBottomRef.current = offset <= PINNED_TO_BOTTOM_THRESHOLD_PX;
	    hasRestoredScrollRef.current = true;
	  }, []);

	  return (
	    <KeyboardAvoidingView
	      style={styles.keyboardAvoiding}
	      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
	      keyboardVerticalOffset={64}
	    >
	      <View style={styles.container}>
	        <View style={styles.headerRow}>
	          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
	            <Text style={styles.backButtonText}>← Sessions</Text>
	          </TouchableOpacity>
	          <Text style={styles.title} numberOfLines={1}>
	            {sessionHeaderTitle}
	          </Text>
          <View style={styles.headerButtons}>
            <SessionActionsBar
              pinned={pinnedSessionActions}
              onChangePinned={setPinnedSessionActions}
              onAction={handleSessionAction}
              isActionDisabled={(action) =>
                pluginActionInProgress ||
                (sendInProgress && action === 'reload')
              }
              extraActions={pluginSessionActionDefs}
              isActive={isActive}
            />
          </View>
	        </View>

	      {sessionDirty && (
	        <View style={styles.dirtyBanner}>
	          <Text style={styles.dirtyBannerText} numberOfLines={1}>
	            Out of sync — Reload to recover
	          </Text>
	          <TouchableOpacity
	            style={[styles.button, styles.secondaryButton, styles.smallButton]}
	            onPress={async () => {
	              chatController?.clearRequestState();
	              await loadMessages();
	            }}
	            disabled={!chatController || sendInProgress || loadingMessages}
	          >
	            <Text
	              style={[
	                styles.buttonTextSecondary,
	                (!chatController || sendInProgress || loadingMessages) &&
	                  styles.buttonTextDisabled,
	              ]}
	            >
	              Reload
	            </Text>
	          </TouchableOpacity>
	        </View>
	      )}

	      {(loadingMessages || pluginActionInProgress) && (
	        <View style={styles.loadingContainer}>
	          <ActivityIndicator size="small" color={theme.primary} />
	          <Text style={styles.loadingText}>
	            {loadingMessages ? 'Loading messages...' : 'Running action...'}
	          </Text>
	        </View>
	      )}
	
	      <FlatList
	        style={styles.messagesContainer}
	        ref={listRef}
	        data={chatRows}
	        inverted
	        onLayout={() => {
	          maybeRestoreScroll();
	        }}
	        onContentSizeChange={() => {
	          maybeRestoreScroll();
	        }}
	        onScroll={handleListScroll}
	        scrollEventThrottle={16}
	        maintainVisibleContentPosition={{
	          minIndexForVisible: 0,
	          autoscrollToTopThreshold: PINNED_TO_BOTTOM_THRESHOLD_PX,
	        }}
	        keyExtractor={(row) => row.key}
	        extraData={{
	          isActive,
	          editingIndex,
	          editingText,
	          messageViewModeByIndex,
	          pinnedMessageActionsByRole,
	          footerElements,
	          pluginMessageActionDefs,
	          statusBarParts,
	          streamingRow,
	        }}
	        renderItem={({ item: row }) => {
	          if (row.kind === 'status') {
	            if (!row.parts || row.parts.length === 0) {
	              return null;
	            }
	            return (
	              <View style={styles.statusBarContainer}>
	                <Text style={styles.statusBarText}>{row.parts.join('   ')}</Text>
	              </View>
	            );
	          }
	
	          if (row.kind === 'stream') {
	            if (!streamingRow || (!streamingRow.content && !streamingRow.reasoning)) {
	              return null;
	            }
	            const streamingIndex =
	              messages.length > 0 ? messages[messages.length - 1].index + 1 : 0;
	            return (
	              <MessageBubble
	                index={streamingIndex}
	                isActive={isActive}
	                message={{
	                  role: 'assistant',
	                  content: streamingRow.content,
	                  metadata: {
	                    ...(streamingRow.metadata || {}),
	                    reasoning: streamingRow.reasoning,
	                  },
	                }}
	                pinnedActions={[]}
	                allowedActions={[]}
	                onAction={handleMessageAction}
	                onChangePinnedForRole={handleChangePinnedForRole}
	                isEditing={false}
	                renderMode="markdown"
	                footerElements={footerElements}
	                pluginActionDefs={pluginMessageActionDefs}
	              />
	            );
	          }

	          const m = row.indexedMessage;
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
	              index={m.index}
	              isActive={isActive}
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
	              footerElements={footerElements}
	              pluginActionDefs={pluginMessageActionDefs}
	            />
	          );
	        }}
	      />

      {activeError && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Error</Text>
          <Text style={styles.errorText}>{activeError.detail}</Text>
        </View>
      )}

      <View style={styles.composer}>
        <TextInput
          style={styles.composerInput}
          placeholder="Type your message..."
          placeholderTextColor={theme.textSecondary}
          value={composeText}
          onChangeText={(text) => {
            setComposeText(text);
          }}
          onBlur={() => {
            onSaveComposeText(composeTextRef.current);
          }}
          multiline
        />
        {/** Compute per-button enablement so we can style text when disabled. */}
        {(() => {
          const canAppend = !!backend && !sendInProgress && !activeRequestId;
          const canResend = !!backend && !sendInProgress && !activeRequestId;
          const canCancel = !!backend && !sendInProgress && !!activeRequestId;
          const canSend = !!backend && !sendInProgress && !activeRequestId;

          return (
        <View style={styles.composerButtonsRow}>
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton, styles.composerButton]}
            onPress={handleAppend}
            disabled={!canAppend}
          >
            <Text
              style={[
                styles.buttonTextSecondary,
                !canAppend && styles.buttonTextDisabled,
              ]}
            >
              Append
            </Text>
          </TouchableOpacity>
      <TouchableOpacity
        style={[styles.button, styles.secondaryButton, styles.composerButton]}
        onPress={handleResend}
            disabled={!canResend}
      >
            <Text
              style={[
                styles.buttonTextSecondary,
                !canResend && styles.buttonTextDisabled,
              ]}
            >
              Resend
            </Text>
      </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton, styles.composerButton]}
            onPress={handleCancel}
            disabled={!canCancel}
          >
            <Text
              style={[
                styles.buttonTextSecondary,
                !canCancel && styles.buttonTextDisabled,
              ]}
            >
              Cancel
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton, styles.composerButton]}
            onPress={handleSend}
            disabled={!canSend}
          >
            {sendInProgress || activeRequestId ? (
              <ActivityIndicator size="small" color={theme.textOnPrimary} />
            ) : (
              <Text
                style={[
                  styles.buttonText,
                  !canSend && styles.buttonTextDisabled,
                ]}
              >
                Send
              </Text>
            )}
          </TouchableOpacity>
        </View>
          );
        })()}
      </View>

	      {messageLimitVisible && (
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
	      )}

	      {deleteRangeVisible && (
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
	      )}
	      <AgentSwitchModal
	        visible={agentModalVisible}
	        loading={agentsLoading || agentSwitchInProgress}
	        agents={availableAgents}
	        selectedAgentId={sessionAgentId}
	        onRequestClose={() => setAgentModalVisible(false)}
	        onSelectAgent={handleSwitchAgent}
	      />

	      <SessionSettingsModal
	        backend={backend}
	        sessionId={sessionId}
	        visible={settingsVisible}
	        onRequestClose={() => setSettingsVisible(false)}
	      />
	      <ApplicationActionDialog
	        visible={!!activePluginDialogElement}
	        dialog={(activePluginDialogElement as any)?.dialog || null}
	        titleFallback={activePluginDialogElement?.label}
	        prefillContext={{
	          session:
	            activePluginDialogContext && 'sessionSummary' in activePluginDialogContext
	              ? activePluginDialogContext.sessionSummary || undefined
	              : undefined,
	          message:
	            activePluginDialogContext && activePluginDialogContext.kind === 'message'
	              ? {
	                  index: (activePluginDialogContext as any).index,
	                  ...(activePluginDialogContext as any).message,
	                }
	              : undefined,
	        }}
	        onSubmit={handleSubmitPluginDialog}
	        onCancel={handleCancelPluginDialog}
	      />
	      {debugVisible && (
	        <View style={styles.debugOverlay}>
	          <DebugEventsView events={debugEvents} onClose={() => setDebugVisible(false)} />
	        </View>
	      )}
	    </View>
	    </KeyboardAvoidingView>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    keyboardAvoiding: {
      flex: 1,
      backgroundColor: theme.background,
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
      color: theme.primary,
      fontSize: 14,
    },
    title: {
      flex: 1,
      textAlign: 'center',
      fontSize: 18,
      fontWeight: '600',
      color: theme.text,
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
      backgroundColor: theme.primary,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    smallButton: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      marginLeft: 8,
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
    buttonTextDisabled: {
      color: theme.textSecondary,
    },
	    dirtyBanner: {
	      flexDirection: 'row',
	      alignItems: 'center',
	      marginHorizontal: 4,
	      marginBottom: 8,
	      paddingHorizontal: 10,
	      paddingVertical: 8,
	      borderRadius: 8,
	      borderWidth: 1,
	      borderColor: theme.primary,
	      backgroundColor: theme.primaryMuted,
	    },
	    dirtyBannerText: {
	      flex: 1,
	      fontSize: 14,
	      fontWeight: '600',
	      color: theme.text,
	      marginRight: 8,
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
    messagesContainer: {
      flex: 1,
      marginBottom: 8,
    },
    errorContainer: {
      marginHorizontal: 4,
      marginBottom: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.danger,
      backgroundColor: theme.surface,
    },
    errorTitle: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.danger,
      marginBottom: 4,
    },
    errorText: {
      fontSize: 13,
      color: theme.text,
    },
    composer: {
      borderTopWidth: 1,
      borderTopColor: theme.border,
      paddingTop: 8,
    },
    composerInput: {
      minHeight: 60,
      maxHeight: 120,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      fontSize: 14,
      marginBottom: 8,
      color: theme.text,
    },
    composerButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
    composerButton: {
      flex: 1,
      minWidth: 0,
      alignItems: 'center',
      marginHorizontal: 4,
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
    modalInput: {
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      fontSize: 14,
      marginBottom: 12,
      color: theme.text,
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
      color: theme.textSecondary,
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
      color: theme.textSecondary,
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
      borderColor: theme.border,
      marginBottom: 6,
    },
    agentItemSelected: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    agentItemText: {
      fontSize: 14,
      color: theme.text,
    },
    debugOverlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: theme.modalBackdrop,
    },
    statusBarContainer: {
      marginTop: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderTopWidth: 1,
      borderTopColor: theme.divider,
      backgroundColor: theme.surfaceAlt,
    },
    statusBarText: {
      fontSize: 11,
      color: theme.textSecondary,
      fontFamily: 'Courier',
    },
  });

export default SessionChatScreen;
