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
import type { ConnectionAdapter } from '../App';
import {
  apiAppendMessage,
  apiDeleteMessagesByRange,
  apiGetSessionAgent,
  apiListMessages,
  apiModifyMessage,
  apiSend,
  apiSwitchSessionAgent,
  type ApiMessage,
  type IndexedMessage,
  type ActionUiElement,
  apiGetSessionUiSchema,
  type UiSchemaElement,
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
import { useSessionEvents } from './useSessionEvents';
import { extractByPath, renderTemplate } from './uiSchemaUtils';
import { useApplicationPlugins } from './ApplicationPluginsContext';
import { executeApplicationAction } from './applicationActionsExecutor';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import { useSessionAgents } from './useSessionAgents';
import { usePluginActionDialog } from './usePluginActionDialog';
import type {
  AssistantMessageEvent,
  ErrorEvent,
  Event,
  FinalEvent,
  MessageAppendedEvent,
  PartialEvent,
  ToolResultsEvent,
} from './eventsTypes';

interface SessionChatScreenProps {
  adapter: ConnectionAdapter | null;
  connectionId: string | null;
  sessionId: string;
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
  | { kind: 'session' }
  | { kind: 'message'; index: number; message: ApiMessage };

const SessionChatScreen: React.FC<SessionChatScreenProps> = ({
  adapter,
  connectionId,
  sessionId,
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
  const [activeError, setActiveError] = useState<
    { detail: string; requestId: string | null } | null
  >(null);
  const [streamingRow, setStreamingRow] = useState<
    | {
        requestId: string;
        reasoning: string;
        content: string;
        metadata?: Record<string, any> | null;
      }
    | null
  >(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [uiSchemaElements, setUiSchemaElements] = useState<UiSchemaElement[]>([]);
  const { actionsById, sessionActions: pluginSessionActions, messageActions: pluginMessageActions } =
    useApplicationPlugins();
  const scrollViewRef = useRef<ScrollView | null>(null);
  const composeTextRef = useRef<string>(initialComposeText ?? '');
  const scrollOffsetRef = useRef<number>(initialScrollOffset || 0);
  const hasRestoredScrollRef = useRef(false);
  const hasAutoScrolledRef = useRef(false);

  useEffect(() => {
    composeTextRef.current = composeText;
  }, [composeText]);

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
    if (!adapter) {
      setUiSchemaElements([]);
      return;
    }
    let cancelled = false;
    const loadSchema = async () => {
      try {
        const els = await apiGetSessionUiSchema(adapter, sessionId);
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
  }, [adapter, sessionId]);

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
      const { messages: list, cursor_event_id } = await apiListMessages(
		        adapter,
		        sessionId,
		        start,
		        end,
		      );
		      setMessages(list);
      setInitialCheckpointId(cursor_event_id ?? null);
      setStreamingRow(null);
		      if (!hasAutoScrolledRef.current) {
		        setShouldAutoScroll(true);
		        hasAutoScrolledRef.current = true;
		      }
		      setLastReloadAt(new Date());
      onUpdateCache(list, cursor_event_id ?? null);
      setSnapshotReady(true);
    } catch (err: any) {
      console.log('Failed to load messages', err);
      const message = err?.message || 'Failed to load messages';
      Alert.alert('Error', message);
    } finally {
      setLoadingMessages(false);
	    }
  }, [adapter, sessionId, rangeStartText, rangeEndText, onUpdateCache]);

  const {
    activeElement: activePluginDialogElement,
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
        if (!adapter) {
          Alert.alert('No connection', 'Connect to a server to run actions.');
          return;
        }

        const isMessage = context.kind === 'message';
        const { ok, response } = await executeApplicationAction(
          adapter,
          element,
          actionsById,
          {
            sessionId,
            messageContext: isMessage
              ? { index: context.index, message: context.message }
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
        await loadMessages();
      },
      [adapter, actionsById, sessionId, loadMessages, onNavigateToSession],
    ),
  );

  useEffect(() => {
    setMessages(cachedMessages ?? []);
    if (cachedMessages && lastLoadedAt) {
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
    if (!cachedMessages && adapter) {
      loadMessages();
    }
  }, [adapter, cachedMessages, loadMessages]);

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
      setActiveError(null);
      setStreamingRow(null);
      await apiSend(adapter, sessionId);
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
      setActiveError(null);
      setStreamingRow(null);
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
        setActiveError(null);
        setStreamingRow(null);
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
    if (action === 'deleteRange') {
      setDeleteRangeStartText('');
      setDeleteRangeEndText('');
      setDeleteRangeVisible(true);
      return;
    }
    if (action === 'agentSwitch') {
      setAgentModalVisible(true);
      if (!adapter) {
        Alert.alert('No connection', 'Connect to a server to switch agent.');
        return;
      }
      if (availableAgents.length === 0 || sessionAgentId === null) {
        try {
          await ensureAgentsLoaded(adapter);
          const current = await apiGetSessionAgent(adapter, sessionId);
          setSessionAgentId(current);
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
      openPluginDialogForElement(pluginEl, { kind: 'session' });
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
      openPluginDialogForElement(pluginEl, { kind: 'message', index, message });
    }
  };

  const appendEventsToDebugBuffer = (events: Event[]) => {
    if (!events || events.length === 0) return;
    setDebugEvents((prev) => {
      const combined = [...prev, ...events];
      const max = 200;
      return combined.length > max ? combined.slice(combined.length - max) : combined;
    });
  };

  const applyFinalEvent = (ev: FinalEvent) => {
    if (!Array.isArray(ev.messages) || ev.messages.length === 0) return;
    setMessages((prev) => {
      const current = [...prev];
      let lastIndex = current.length > 0 ? current[current.length - 1].index : -1;
      for (const msg of ev.messages) {
	        if (!msg) continue;
        lastIndex += 1;
        current.push({ index: lastIndex, message: msg });
      }
      return current;
    });
  };

	  const applyMessageAppendedEvent = (ev: MessageAppendedEvent) => {
	    const message = ev.message;
	    if (!message) return;
	    setMessages((prev) => {
	      const lastIndex = prev.length > 0 ? prev[prev.length - 1].index : -1;
	      return [...prev, { index: lastIndex + 1, message }];
	    });
	  };
  const applyToolResultsEvent = (ev: ToolResultsEvent) => {
    if (!Array.isArray(ev.messages) || ev.messages.length === 0) return;
    setMessages((prev) => {
      const current = [...prev];
      let lastIndex = current.length > 0 ? current[current.length - 1].index : -1;
      for (const msg of ev.messages) {
	        if (!msg) continue;
        lastIndex += 1;
        current.push({ index: lastIndex, message: msg });
      }
      return current;
    });
  };

  const AUTO_RELOAD_ON_REQUEST_COMPLETED = false;

  const handleEvents = (events: Event[]) => {
    if (!events || events.length === 0) return;
    const relevant = events.filter((ev) => ev.session_id === sessionId);

    relevant.forEach((ev) => {
      if (ev.type === 'request_started') {
        // New request: clear error and streaming state.
        setActiveError(null);
        setStreamingRow(null);
      } else if (ev.type === 'assistant_message') {
        const msgEv = ev as AssistantMessageEvent;
        if (msgEv.phase === 'start') {
          setStreamingRow({
            requestId: msgEv.request_id ?? 'unknown',
            reasoning: '',
            content: '',
            metadata: null,
          });
        }
      } else if (ev.type === 'partial') {
        const p = ev as PartialEvent;
        const rawMessage = p.message || ({} as ApiMessage);
        const rawMetadata = (rawMessage.metadata || {}) as Record<string, any>;
        const reasoningDelta =
          typeof rawMetadata.reasoning === 'string' ? rawMetadata.reasoning : '';
        const contentDelta =
          typeof rawMessage.content === 'string' ? rawMessage.content : '';
        if (!reasoningDelta && !contentDelta) return;
        const evRequestId = p.request_id ?? null;
        setStreamingRow((prev) => {
          const base =
            prev && (!evRequestId || prev.requestId === evRequestId)
              ? prev
              : {
                  requestId: evRequestId || 'unknown',
                  reasoning: '',
                  content: '',
                  metadata: null,
                };
          const nextReasoning = base.reasoning + reasoningDelta;
          const mergedMetadata = {
            ...(base.metadata || {}),
            ...(rawMessage.metadata || {}),
            reasoning: nextReasoning,
          } as Record<string, any>;
          return {
            requestId: base.requestId,
            reasoning: nextReasoning,
            content: base.content + contentDelta,
            metadata: mergedMetadata,
          };
        });
      } else if (ev.type === 'final') {
        applyFinalEvent(ev as FinalEvent);
        setStreamingRow(null);
      } else if (ev.type === 'message_appended') {
        applyMessageAppendedEvent(ev as MessageAppendedEvent);
      } else if (ev.type === 'tool_results') {
        applyToolResultsEvent(ev as ToolResultsEvent);
      } else if (ev.type === 'error') {
        const err = ev as ErrorEvent;
        const detail =
          (typeof err.detail === 'string' && err.detail) || 'Request failed with an error.';
        setActiveError({ detail, requestId: err.request_id ?? null });
      } else if (ev.type === 'request_completed' && AUTO_RELOAD_ON_REQUEST_COMPLETED) {
        loadMessages();
      }
    });

    appendEventsToDebugBuffer(events);
  };

  const eventsEnabled = !!(adapter && sessionId && snapshotReady);
  const { lastEventId: _lastEventId, status: _eventsStatus } = useSessionEvents(
    {
      adapter,
      sessionId,
      enabled: eventsEnabled,
      initialSinceId: initialCheckpointId,
    },
    handleEvents,
  );

	  const sessionLabel = `Session ${sessionId.slice(0, 8)}`;

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
	    const agentLabel = sessionAgentId || 'default';
	    parts.push(`Agent: ${agentLabel}`);
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
	  }, [lastAssistantMessage, statusBarElements, sessionAgentId, sessionId]);

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
              extraActions={pluginSessionActionDefs}
            />
          </View>
	        </View>

	      {loadingMessages && (
	        <View style={styles.loadingContainer}>
	          <ActivityIndicator size="small" color={theme.primary} />
	          <Text style={styles.loadingText}>Loading messages...</Text>
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
	      <AgentSwitchModal
	        visible={agentModalVisible}
	        loading={agentLoading}
	        agents={availableAgents}
	        selectedAgentId={sessionAgentId}
	        onRequestClose={() => setAgentModalVisible(false)}
	        onSelectAgent={handleSwitchAgent}
	      />

	      <SessionSettingsModal
	        adapter={adapter}
	        sessionId={sessionId}
	        visible={settingsVisible}
	        onRequestClose={() => setSettingsVisible(false)}
	      />
	      <ApplicationActionDialog
	        visible={!!activePluginDialogElement}
	        dialog={(activePluginDialogElement as any)?.dialog || null}
	        titleFallback={activePluginDialogElement?.label}
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
      justifyContent: 'flex-end',
    },
    composerButton: {
      minWidth: 90,
      alignItems: 'center',
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
