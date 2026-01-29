import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import { useChatController } from '@crystal-lattice/frontend-sdk-react';
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
import { useTheme, type Theme } from './theme';
import { extractByPath, renderTemplate } from './uiSchemaUtils';
import { useApplicationPlugins } from './ApplicationPluginsContext';
import { executeApplicationAction } from './applicationActionsExecutor';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import { useSessionAgents } from './useSessionAgents';
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
  cachedCursorEventId: string | null;
  onUpdateCache: (messages: IndexedMessage[], cursorEventId: string | null) => void;
  onBack: () => void;
  onNavigateToSession?: (sessionId: string) => void;
  initialComposeText: string;
  initialScrollOffset: number;
  onSaveComposeText: (composeText: string) => void;
  onSaveScrollOffset: (scrollOffset: number) => void;
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
  cachedCursorEventId,
  onUpdateCache,
  onBack,
  onNavigateToSession,
  initialComposeText,
  initialScrollOffset,
  onSaveComposeText,
  onSaveScrollOffset,
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
  const { availableAgents, agentLoading, ensureAgentsLoaded, setAgentLoading } =
    useSessionAgents();
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
  const [shouldAutoScroll, setShouldAutoScroll] = useState(false);
  const [initialCheckpointId, setInitialCheckpointId] = useState<string | null>(
    cachedCursorEventId,
  );
  const [snapshotReady, setSnapshotReady] = useState<boolean>(!!cachedMessages);
  const [debugVisible, setDebugVisible] = useState(false);
  const [debugEvents, setDebugEvents] = useState<Event[]>([]);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [uiSchemaElements, setUiSchemaElements] = useState<UiSchemaElement[]>([]);
  const [pluginActionInProgress, setPluginActionInProgress] = useState(false);
  const {
    actionsById,
    sessionActions: pluginSessionActions,
    messageActions: pluginMessageActions,
    sessionListFields,
  } = useApplicationPlugins();
  const scrollViewRef = useRef<ScrollView | null>(null);
  const composeTextRef = useRef<string>(initialComposeText ?? '');
  const scrollOffsetRef = useRef<number>(initialScrollOffset || 0);
  const hasRestoredScrollRef = useRef(false);
  const hasAutoScrolledRef = useRef(false);
  const hasHydratedCacheRef = useRef(false);

  const appendEventsToDebugBuffer = useCallback((events: Event[]) => {
    if (!events || events.length === 0) return;
    setDebugEvents((prev) => {
      const combined = [...prev, ...events];
      const max = 200;
      return combined.length > max ? combined.slice(combined.length - max) : combined;
    });
  }, []);

  const eventsEnabled = !!(backend && sessionId && snapshotReady);
  const { controller: chatController, state: chatState } = useChatController({
    backend,
    sessionId,
    initialMessages: cachedMessages ?? [],
    initialCursorEventId: cachedCursorEventId ?? null,
    eventsEnabled,
    initialSinceId: initialCheckpointId,
    onEvents: appendEventsToDebugBuffer,
  });

  const messages: IndexedMessage[] = chatState?.messages ?? cachedMessages ?? [];
  const streamingRow = chatState?.streamingRow ?? null;
  const activeRequestId = chatState?.activeRequestId ?? null;
  const activeError = chatState?.requestError ?? null;
  const loadingMessages = chatState?.loading ?? false;

  useEffect(() => {
    hasHydratedCacheRef.current = false;
  }, [chatController]);

  useEffect(() => {
    if (!chatController) {
      return;
    }
    if (hasHydratedCacheRef.current) {
      return;
    }
    if (cachedMessages == null) {
      return;
    }

    chatController.hydrateFromCache({
      messages: cachedMessages,
      cursorEventId: cachedCursorEventId ?? null,
    });
    hasHydratedCacheRef.current = true;
  }, [chatController, cachedMessages, cachedCursorEventId]);

  useEffect(() => {
    composeTextRef.current = composeText;
  }, [composeText]);

  useEffect(() => {
    if (!backend) return;
    ensureAgentsLoaded(backend).catch(() => {
      // Non-fatal; status bar should still render.
    });
  }, [backend, ensureAgentsLoaded]);

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

  useEffect(() => {
    if (!backend) {
      setUiSchemaElements([]);
      return;
    }
    let cancelled = false;
    const loadSchema = async () => {
      try {
        const els = await backend.getSessionUiSchema(sessionId);
        if (!cancelled) {
          setUiSchemaElements(Array.isArray(els) ? els : []);
        }
      } catch (err) {
        console.log('Failed to load UI schema for session', err);
        if (!cancelled) {
          setUiSchemaElements([]);
        }
      }
    };
    loadSchema();
    return () => {
      cancelled = true;
    };
  }, [backend, sessionId]);

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

	    await chatController.loadMessages({ start, end });
	    const snapshot = chatController.getSnapshot();
	    setInitialCheckpointId(snapshot.cursorEventId ?? null);
		      if (!hasAutoScrolledRef.current) {
		        setShouldAutoScroll(true);
		        hasAutoScrolledRef.current = true;
		      }
		      setLastReloadAt(new Date());
	    onUpdateCache(snapshot.messages, snapshot.cursorEventId ?? null);
      setSnapshotReady(true);
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
          const { ok, response } = await executeApplicationAction(
            backend,
            element,
            actionsById,
            {
              sessionId,
              messageContext: isMessage
                ? { index: (context as any).index, message: (context as any).message }
                : undefined,
              dialogValues,
            },
          );
          if (!ok) return;

          const result: any = (response as any)?.result || {};
          const created: string[] = Array.isArray(result.created_session_ids)
            ? (result.created_session_ids as string[])
            : [];
          const selectedId: string | undefined =
            typeof result.selected_session_id === 'string'
              ? result.selected_session_id
              : created.length > 0 && typeof created[0] === 'string'
              ? created[0]
              : undefined;
          if (selectedId && onNavigateToSession) {
            onNavigateToSession(selectedId);
            return;
          }

          const updated: string[] = Array.isArray(result.updated_session_ids)
            ? (result.updated_session_ids as string[])
            : [];
          if (updated.includes(sessionId)) {
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
    if (sessionId && connectionId !== null) {
      setInitialCheckpointId(cachedCursorEventId ?? null);
      setSnapshotReady(!!cachedMessages);
    }
  }, [cachedCursorEventId, cachedMessages, sessionId, connectionId]);

  useEffect(() => {
    if (!cachedMessages && chatController) {
      loadMessages();
    }
  }, [chatController, cachedMessages, loadMessages]);

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
      onSaveComposeText(composeTextRef.current);
      onSaveScrollOffset(scrollOffsetRef.current);
    };
  }, []);

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
      await loadMessages();
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
      await loadMessages();
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
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to delete messages.');
      return;
    }
    try {
      await chatController.deleteMessages({ range: { start, end } });
      setDeleteRangeVisible(false);
      await loadMessages();
    } catch (err: any) {
      console.log('Failed to delete range', err);
      const message = err?.message || 'Failed to delete messages';
      Alert.alert('Error', message);
    }
  };

  const handleSwitchAgent = async (agentId: string) => {
	    if (!backend) {
	      Alert.alert('No connection', 'Connect to a server to switch agent.');
	      return;
	    }
	    try {
	      setAgentLoading(true);
	      await backend.switchSessionAgent(sessionId, agentId);
	      setSessionAgentId(agentId && agentId.trim() ? agentId.trim() : null);
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
	        await ensureAgentsLoaded(backend);
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

	  const titleFields = useMemo(
	    () =>
	      (sessionListFields || [])
	        .filter((el) => (el as any).role === 'title')
	        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
	    [sessionListFields],
	  );

	  const sessionLabel = `Session ${sessionId.slice(0, 8)}`;

	  const sessionHeaderTitle = useMemo(() => {
	    if (sessionSummary) {
	      for (const field of titleFields) {
	        const path = field.data;
	        if (typeof path !== 'string' || !path) continue;
	        const value = extractByPath(sessionSummary as any, path);
	        if (value === undefined || value === null || value === '') continue;
	        const text = renderTemplate(field.template ?? '{{data}}', value);
	        if (text) return text;
	      }
	    }
	    return sessionLabel;
	  }, [sessionSummary, titleFields, sessionLabel]);

	  const footerElements = useMemo(
	    () =>
	      (uiSchemaElements || []).filter(
	        (el) => el && el.ui_type === 'message_footer' && typeof el.data === 'string' && el.data,
	      ),
	    [uiSchemaElements],
	  );

	  const statusBarElements = useMemo(
	    () =>
	      (uiSchemaElements || []).filter(
	        (el) => el && el.ui_type === 'status_bar' && typeof el.data === 'string' && el.data,
	      ),
	    [uiSchemaElements],
	  );

	  const lastAssistantMessage = useMemo(() => {
	    if (streamingRow && (streamingRow.content || streamingRow.reasoning)) {
	      return {
	        role: 'assistant',
	        content: streamingRow.content,
	        metadata: streamingRow.metadata || {},
	      } as ApiMessage;
	    }
	    for (let i = messages.length - 1; i >= 0; i -= 1) {
	      const m = messages[i].message;
	      if ((m.role || 'unknown') === 'assistant') {
	        return m;
	      }
	    }
	    return null;
	  }, [messages, streamingRow]);

	  const statusBarParts = useMemo(() => {
	    const parts: string[] = [];
	    const agentLabel =
	      sessionAgentId &&
	      sessionAgentId !== 'default' &&
	      availableAgents.includes(sessionAgentId)
	        ? sessionAgentId
	        : null;
	    if (agentLabel) {
	      parts.push(`Agent: ${agentLabel}`);
	    }
	    parts.push(`Session: ${sessionId.slice(0, 8)}`);
	    if (!lastAssistantMessage || !statusBarElements.length) {
	      return parts;
	    }
	    statusBarElements.forEach((el) => {
	      if (!el || el.ui_type !== 'status_bar') return;
	      const value = extractByPath(lastAssistantMessage, el.data);
	      if (value === undefined || value === null || value === '') return;
	      const text = renderTemplate(el.template ?? '{{data}}', value);
	      if (text) parts.push(text);
	    });
	    return parts;
	  }, [
	    lastAssistantMessage,
	    statusBarElements,
	    sessionAgentId,
	    availableAgents,
	    sessionId,
	  ]);

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

	      {(loadingMessages || pluginActionInProgress) && (
	        <View style={styles.loadingContainer}>
	          <ActivityIndicator size="small" color={theme.primary} />
	          <Text style={styles.loadingText}>
	            {loadingMessages ? 'Loading messages...' : 'Running action...'}
	          </Text>
	        </View>
	      )}
	
	      <ScrollView
	        style={styles.messagesContainer}
	        ref={scrollViewRef}
	        onScroll={(event) => {
	          scrollOffsetRef.current = event.nativeEvent.contentOffset.y;
	        }}
	        onContentSizeChange={() => {
	          if (
	            !hasRestoredScrollRef.current &&
	            typeof initialScrollOffset === 'number' &&
	            initialScrollOffset > 0 &&
	            scrollViewRef.current
	          ) {
	            scrollViewRef.current.scrollTo({
	              x: 0,
	              y: initialScrollOffset,
	              animated: false,
	            });
	            hasRestoredScrollRef.current = true;
	            return;
	          }
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
      })}
      {streamingRow && (streamingRow.content || streamingRow.reasoning) && (
        <MessageBubble
          key={`stream-${streamingRow.requestId}`}
          index={messages.length > 0 ? messages[messages.length - 1].index + 1 : 0}
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
      )}
	      {statusBarParts.length > 0 && (
	        <View style={styles.statusBarContainer}>
	          <Text style={styles.statusBarText}>{statusBarParts.join('   ')}</Text>
	        </View>
	      )}
      </ScrollView>

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
	        loading={agentLoading}
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
