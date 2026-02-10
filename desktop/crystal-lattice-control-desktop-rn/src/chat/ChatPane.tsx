import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Clipboard,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  ActionsMenuBar,
  getLastActionsPopoverAnchorTag,
  useTheme,
  type ActionDefinition,
  type ActionKey,
} from '@crystal-lattice/frontend-rn-components';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';
import { filterFooterElements, selectDisplayContent } from '@crystal-lattice/frontend-sdk';
import {
  useAgentsController,
  useChatController,
  useHydrateControllerFromCache,
  usePersistentPinnedActions,
  useSessionUiSchemaController,
} from '@crystal-lattice/frontend-sdk-react';

import type { MessagesCacheEntry } from '../cache/types';
import type { TabStripStyle } from '../tabs/tabStripStyle';
import { asyncStorageKeyValueStore } from '../storage/asyncStorageKeyValueStore';
import { PlaceholderFlatList } from '../ui/PlaceholderFlatList';
import { DesktopWindowManager } from '../windows/desktopWindowManager';
import { setActiveSessionSettingsWindow } from '../windows/sessionSettingsCoordinator';
import { setActiveMessageLimitPopover } from '../windows/messageLimitPopoverCoordinator';
import { MacTextView, type MacTextViewHandle } from '../native/MacTextView';
import DesktopMessageBubble from './DesktopMessageBubble';
import { ALL_MESSAGE_ACTIONS, type MessageActionKey } from './messageActions';
import { PinnedMessageActionsProvider } from './PinnedMessageActionsContext';

const DEFAULT_HISTORY_WINDOW = 50;
const PINNED_SESSION_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_chat_session_actions_v1';
const PINNED_MESSAGE_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_message_actions_by_role_v1';
const LEGACY_PINNED_MESSAGE_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_chat_message_actions_v1';

const DEFAULT_PINNED_MESSAGE_ACTIONS_BY_ROLE: Record<string, MessageActionKey[]> = {
  user: ['modify', 'copy'],
  assistant: ['modify', 'toggleMarkdown', 'copy'],
  system: ['modify', 'copy'],
  tool: ['copy'],
};

type ChatSessionActionKey = 'reload' | 'cancel' | 'agentSwitch' | 'messageLimit' | 'settings';

const BUILTIN_SESSION_ACTIONS: ActionDefinition[] = [
  { key: 'reload', label: 'Reload', iconName: 'refresh-ccw' },
  { key: 'cancel', label: 'Cancel', iconName: 'x-circle' },
  { key: 'agentSwitch', label: 'Switch agent', iconName: 'user' },
  { key: 'messageLimit', label: 'Message limit', iconName: 'sliders' },
  { key: 'settings', label: 'Settings…', iconName: 'settings' },
];

const DEFAULT_PINNED_SESSION_ACTION_KEYS: ActionKey[] = ['reload', 'cancel'];

export interface ChatPaneProps {
	isActive: boolean;
  connectionId: string;
  connectionName: string;
  sessionId: string;
  title: string;
  subtitle?: string;
  backend: AgentBackend | null;
  cachedEntry: MessagesCacheEntry | null;
  onUpdateCache: (params: {
    connectionId: string;
    sessionId: string;
    messages: IndexedMessage[];
    cursorEventId?: string | null;
    activeRequestId?: string | null;
  }) => void;
  styleVariant?: TabStripStyle;
}

export const ChatPane = React.memo(function ChatPane({
	isActive,
	connectionId,
	connectionName,
	sessionId,
	title,
	subtitle,
	backend,
	cachedEntry,
	onUpdateCache,
	styleVariant = 'toolbarTabs',
}: ChatPaneProps): React.JSX.Element {

  console.log(`Rendering ChatPane for session ${sessionId} (active: ${isActive})`);

  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, styleVariant), [theme, styleVariant]);

  const [messageViewModeByIndex, setMessageViewModeByIndex] = useState<
    Record<number, 'markdown' | 'raw'>
  >({});
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [editingInitialText, setEditingInitialText] = useState('');
  const [pinnedMessageActionsByRole, setPinnedMessageActionsByRole] = useState<
    Record<string, MessageActionKey[]>
  >({});

  const [loadError, setLoadError] = useState<string | null>(null);
  const [composeText, setComposeText] = useState('');
  const [rangeStartText, setRangeStartText] = useState('');
  const [rangeEndText, setRangeEndText] = useState('');
  const [lastReloadAt, setLastReloadAt] = useState<Date | null>(null);
  const [messageLimitVisible, setMessageLimitVisible] = useState(false);
  const [sendInFlight, setSendInFlight] = useState(false);
  const [reloadInFlight, setReloadInFlight] = useState(false);
  const [cancelInFlight, setCancelInFlight] = useState(false);
  const [openingAgentPicker, setOpeningAgentPicker] = useState(false);
  const composerRef = useRef<MacTextViewHandle | null>(null);
  const composeTextRef = useRef('');
  const attemptedInitialLoadRef = useRef(false);
  const pendingPersistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastPersistKeyRef = useRef<string | null>(null);

  const [composerHeight, setComposerHeight] = useState(34);
  const handleComposerHeightChange = useCallback((height: number) => {
    const next = Math.round(height);
    setComposerHeight((prev) => {
      if (Math.abs(prev - next) < 1) {
        return prev;
	}
      return next;
    });
  }, []);

  // Debug logging removed; composer uses native MacTextView on macOS.

  const { controller: chatController, state: chatState } = useChatController({
    backend,
    sessionId,
    initialMessages: cachedEntry?.messages ?? [],
    initialEventsCursorId: cachedEntry?.cursorEventId ?? null,
    initialActiveRequestId: cachedEntry?.activeRequestId ?? null,
	  eventsEnabled: isActive && backend != null,
  });

  const pinnedSessionActionsStorageKey = useMemo(() => {
    return `${PINNED_SESSION_ACTIONS_STORAGE_KEY_BASE}:${connectionId}`;
  }, [connectionId]);

  const { pinned: pinnedSessionActionKeys, setPinned: setPinnedSessionActionKeys } =
    usePersistentPinnedActions<ActionKey>({
      store: asyncStorageKeyValueStore,
      key: pinnedSessionActionsStorageKey,
      initialPinned: DEFAULT_PINNED_SESSION_ACTION_KEYS,
    });

  const pinnedMessageActionsStorageKey = useMemo(
    () => `${PINNED_MESSAGE_ACTIONS_STORAGE_KEY_BASE}:${connectionId}`,
    [connectionId],
  );

  useEffect(() => {
    const loadPinnedFromStorage = async () => {
      console.log('Loading pinned message actions from storage with key', pinnedMessageActionsStorageKey);
      try {
        const messageRaw = await asyncStorageKeyValueStore.get(pinnedMessageActionsStorageKey);
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
          return;
        }

      } catch (err) {
        console.log('Failed to load pinned message actions from storage', err);
      }
    };

    //loadPinnedFromStorage();
    }, [connectionId, pinnedMessageActionsStorageKey]);

  useEffect(() => {
    const saveMessagePinned = async () => {
      console.log('Saving pinned message actions to storage with key', pinnedMessageActionsStorageKey, pinnedMessageActionsByRole);
      try {
        await asyncStorageKeyValueStore.set(
          pinnedMessageActionsStorageKey,
          JSON.stringify(pinnedMessageActionsByRole),
        );
      } catch (err) {
        console.log('Failed to save pinned message actions', err);
      }
    };
    //saveMessagePinned();
  }, [pinnedMessageActionsByRole, pinnedMessageActionsStorageKey]);

  const { controller: agentsController, state: agentsState } = useAgentsController({
    backend,
    cacheKey: connectionId,
    enabled: false,
  });

  const { state: sessionUiSchemaState } = useSessionUiSchemaController({
    backend,
    cacheKey: connectionId,
    sessionId,
	  enabled: !!(backend && isActive),
  });
	  const footerElements = useMemo(
	    () => filterFooterElements(sessionUiSchemaState?.elements ?? []),
	    [sessionUiSchemaState?.elements],
	  );

  const hydrateFromCache = useCallback(
    (
      controller: NonNullable<typeof chatController>,
      cache: {
        messages: IndexedMessage[];
        eventsCursorId: string | null;
        activeRequestId: string | null;
        updatedAtMs: number | null;
      },
    ) => {
      const snapshot = controller.getSnapshot();
      const hasInitialSnapshot = snapshot.eventsCursorId != null || snapshot.messages.length > 0;
      if (hasInitialSnapshot) {
        return;
      }
      controller.hydrateFromCache(cache);
    },
    [],
  );

  useHydrateControllerFromCache({
    controller: chatController,
    cache:
      cachedEntry != null
        ? {
            messages: cachedEntry.messages,
            eventsCursorId: cachedEntry.cursorEventId ?? null,
            activeRequestId: cachedEntry.activeRequestId ?? null,
            updatedAtMs: cachedEntry.lastLoadedAt ?? null,
          }
        : null,
    hydrate: hydrateFromCache,
  });

  useEffect(() => {
    if (!chatController) {
      return;
    }

    chatController.setHistoryRangeFromRangeText({
      startText: rangeStartText,
      endText: rangeEndText,
    });
  }, [chatController, rangeEndText, rangeStartText]);

  useEffect(() => {
    attemptedInitialLoadRef.current = false;
    setLoadError(null);
  }, [chatController]);

  const loadInitialMessages = useCallback(async () => {
    if (!chatController) {
      return;
    }

    try {
      setLoadError(null);
      await chatController.loadMessagesFromRangeText({
        startText: rangeStartText,
        endText: rangeEndText,
      });
      const snapshot = chatController.getCacheSnapshot();
      setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to load messages.';
      setLoadError(message);
      Alert.alert('Failed to load messages', message);
    }
  }, [chatController, rangeEndText, rangeStartText]);

  const persistCacheSnapshot = useCallback(() => {
    if (!chatController) {
      return;
    }

    const snapshot = chatController.getCacheSnapshot();
    onUpdateCache({
      connectionId,
      sessionId,
      messages: snapshot.messages,
      cursorEventId: snapshot.eventsCursorId,
      activeRequestId: snapshot.activeRequestId,
    });
  }, [chatController, connectionId, onUpdateCache, sessionId]);

  useEffect(() => {
    if (!chatController) {
      return;
    }

    const snapshot = chatController.getCacheSnapshot();
    const messages = snapshot.messages;
    const firstIndex = messages[0]?.index ?? -1;
    const lastIndex = messages[messages.length - 1]?.index ?? -1;
    const nextKey = [
      messages.length,
      firstIndex,
      lastIndex,
      snapshot.eventsCursorId ?? '',
      snapshot.activeRequestId ?? '',
    ].join('|');

    if (nextKey === lastPersistKeyRef.current) {
      return;
    }
    lastPersistKeyRef.current = nextKey;

    if (pendingPersistTimerRef.current) {
      clearTimeout(pendingPersistTimerRef.current);
    }

    pendingPersistTimerRef.current = setTimeout(() => {
      pendingPersistTimerRef.current = null;
      persistCacheSnapshot();
    }, 250);
  }, [
    chatController,
    chatState?.activeRequestId,
    chatState?.eventsCursorId,
    chatState?.messages,
    persistCacheSnapshot,
  ]);

  useEffect(() => {
    return () => {
      if (pendingPersistTimerRef.current) {
        clearTimeout(pendingPersistTimerRef.current);
        pendingPersistTimerRef.current = null;
      }
      persistCacheSnapshot();
    };
  }, [persistCacheSnapshot]);

  useEffect(() => {
	  if (!isActive) {
      return;
    }
    if (!chatController) {
      return;
    }
    if (chatState?.loading) {
      return;
    }

    const hasInitialSnapshot =
      (chatState?.eventsCursorId != null) ||
      (Array.isArray(chatState?.messages) && chatState.messages.length > 0);
    if (hasInitialSnapshot) {
      return;
    }

    if (attemptedInitialLoadRef.current) {
      return;
    }

    attemptedInitialLoadRef.current = true;
    loadInitialMessages().catch(() => {
      // errors are handled in `loadInitialMessages`
    });
	}, [chatController, chatState?.eventsCursorId, chatState?.loading, chatState?.messages, isActive, loadInitialMessages]);

  const messages: IndexedMessage[] = useMemo(() => {
    return chatState?.messages ?? cachedEntry?.messages ?? [];
  }, [chatState?.messages, cachedEntry?.messages]);

  const streamingRow = chatState?.streamingRow ?? null;

  const messagesCount = messages.length;

	const canSend = backend != null && chatController != null && isActive && !sendInFlight;

  const handleSend = useCallback(async (overrideText?: string) => {
    if (!canSend) {
      return;
    }

    const content = overrideText ?? composeTextRef.current ?? composeText;
    if (!content.trim()) {
      return;
    }

    setSendInFlight(true);
    try {
      await chatController.appendMessage({ role: 'user', content });
      setComposeText('');
      composeTextRef.current = '';
      composerRef.current?.setText('');
      await chatController.send();
      composerRef.current?.focus();
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to send message.';
      Alert.alert('Failed to send', message);
    } finally {
      setSendInFlight(false);
    }
  }, [canSend, chatController, composeText]);

	const canRunHeaderActions = backend != null && chatController != null && isActive;

  const handleReload = useCallback(async () => {
    if (!canRunHeaderActions) {
      return;
    }
    if (reloadInFlight) {
      return;
    }

    setReloadInFlight(true);
    try {
      setLoadError(null);
      chatController.clearRequestState();
      await chatController.loadMessagesFromRangeText({
        startText: rangeStartText,
        endText: rangeEndText,
      });
      const snapshot = chatController.getCacheSnapshot();
      setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to reload messages.';
      setLoadError(message);
      Alert.alert('Failed to reload', message);
    } finally {
      setReloadInFlight(false);
    }
  }, [canRunHeaderActions, chatController, rangeEndText, rangeStartText, reloadInFlight]);

  const applyMessageLimitAndReload = useCallback(
    async (params: { startText: string; endText: string }) => {
      setRangeStartText(params.startText);
      setRangeEndText(params.endText);

      if (!chatController || !backend) {
        return;
      }
      try {
        setLoadError(null);
        chatController.clearRequestState();
        await chatController.loadMessagesFromRangeText({
          startText: params.startText,
          endText: params.endText,
        });
        const snapshot = chatController.getCacheSnapshot();
        setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
      } catch (err: any) {
        const message = err?.message || 'Failed to reload messages.';
        setLoadError(message);
        Alert.alert('Failed to reload', message);
      }
    },
    [backend, chatController],
  );

  const openMessageLimitPopover = useCallback(() => {
    if (Platform.OS !== 'macos') {
      setMessageLimitVisible(true);
      return;
    }
    if (!DesktopWindowManager?.openMessageLimitPopover) {
      Alert.alert('Not supported', 'Message limit popover is not available.');
      return;
    }

    const id = `message-limit:${connectionId}:${sessionId}`;
    setActiveMessageLimitPopover({
      state: {
        id,
        connectionId,
        sessionId,
        startText: rangeStartText,
        endText: rangeEndText,
        lastReloadAtMs: lastReloadAt?.getTime() ?? null,
      },
      handlers: {
        onApply: (params) => {
          applyMessageLimitAndReload(params).catch(() => {});
        },
        onCancel: () => {},
      },
    });

    const anchorTag = getLastActionsPopoverAnchorTag() ?? undefined;
    DesktopWindowManager.openMessageLimitPopover({
      anchorTag,
      width: 420,
      height: 260,
    });
  }, [applyMessageLimitAndReload, connectionId, lastReloadAt, rangeEndText, rangeStartText, sessionId]);

  const handleCancel = useCallback(async () => {
    if (!canRunHeaderActions) {
      return;
    }
    if (cancelInFlight) {
      return;
    }
    if (!chatState?.activeRequestId) {
      return;
    }

    setCancelInFlight(true);
    try {
      await chatController.cancelActiveRequest();
    } catch (err: any) {
      const message = err?.message || 'Failed to cancel request';
      Alert.alert('Failed to cancel', message);
    } finally {
      setCancelInFlight(false);
    }
  }, [canRunHeaderActions, cancelInFlight, chatController, chatState?.activeRequestId]);

  const openAgentPickerForSwitch = useCallback(async () => {
    if (!backend) {
      return;
    }
    if (!agentsController) {
      Alert.alert('Error', 'Agent controller is not available.');
      return;
    }
    if (openingAgentPicker) {
      return;
    }

    setOpeningAgentPicker(true);
    try {
      const agents = await agentsController.ensureLoaded();

      let initialAgentId: string | undefined;
      try {
        const current = await backend.getSessionAgent(sessionId);
        const trimmed = typeof current === 'string' ? current.trim() : '';
        if (trimmed) {
          initialAgentId = trimmed;
        }
      } catch {
        // Ignore; agent picker will fall back to first agent.
      }

      DesktopWindowManager?.openAgentPicker({
        mode: 'switchSessionAgent',
        title: 'Switch Agent',
        primaryButtonLabel: 'Switch',
        sessionId,
        connectionId,
        connectionName,
        initialAgentId,
        agents,
      });
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to load agents');
    } finally {
      setOpeningAgentPicker(false);
    }
  }, [agentsController, backend, connectionId, connectionName, openingAgentPicker, sessionId]);

  const handleSessionAction = useCallback(
    (key: ActionKey) => {
      const action = key as ChatSessionActionKey;
      if (action === 'reload') {
        handleReload().catch(() => {});
        return;
      }
      if (action === 'cancel') {
        handleCancel().catch(() => {});
        return;
      }
      if (action === 'agentSwitch') {
        openAgentPickerForSwitch().catch(() => {});
        return;
      }
      if (action === 'messageLimit') {
        openMessageLimitPopover();
        return;
      }
      if (action === 'settings') {
        if (!backend) {
          return;
        }
        const caps = backend.getCapabilities?.();
        if (caps && (!caps.sessionUiSchema || !caps.sessionConfigOverrides)) {
          Alert.alert('Not supported', 'This backend does not support session settings.');
          return;
        }
        setActiveSessionSettingsWindow({
          state: {
            id: `session-settings:${connectionId}:${sessionId}`,
            connectionId,
            connectionName,
            sessionId,
            backend,
          },
        });
        DesktopWindowManager?.openSessionSettingsWindow({ title: 'Session settings' });
      }
    },
    [
      backend,
      connectionId,
      connectionName,
      handleCancel,
      handleReload,
      openAgentPickerForSwitch,
      openMessageLimitPopover,
      sessionId,
    ],
  );

	const getPinnedActionsForRole = useCallback(
	  (role: string): MessageActionKey[] => {
	    const existing = pinnedMessageActionsByRole[role];
	    if (Array.isArray(existing)) {
	      return existing;
	    }
	    return DEFAULT_PINNED_MESSAGE_ACTIONS_BY_ROLE[role] ?? [];
	  },
	  [pinnedMessageActionsByRole],
	);

	const setPinnedActionsForRole = useCallback(
	  (role: string, pinned: MessageActionKey[]) => {
	    setPinnedMessageActionsByRole((prev) => ({ ...prev, [role]: pinned }));
	  },
	  [],
	);

	const pinnedMessageActionsContextValue = useMemo(
	  () => ({
		    isActive,
	    getPinnedForRole: getPinnedActionsForRole,
	    setPinnedForRole: setPinnedActionsForRole,
	  }),
		  [getPinnedActionsForRole, isActive, setPinnedActionsForRole],
	);

  const handleStartEditMessage = useCallback(
    (index: number, message: { role?: string; content?: unknown }) => {
      const role = message.role || 'unknown';
      if (role === 'tool') {
        return;
      }
      const content = typeof message.content === 'string' ? message.content : '';
      setEditingIndex(index);
      setEditingText(content);
      setEditingInitialText(content);
    },
    [],
  );

  const handleSubmitEditMessage = useCallback(
    async (index: number, newText: string) => {
      const trimmed = newText.trim();
      if (!trimmed) {
        Alert.alert('Invalid content', 'Message content cannot be empty.');
        return;
      }

      if (!chatController || !backend) {
        Alert.alert('Offline', 'Connect to a server to modify messages.');
        return;
      }

      try {
        await chatController.modifyMessage(index, trimmed);
        setEditingIndex(null);
        setEditingText('');
        setEditingInitialText('');
      } catch (err: any) {
        const message = err?.message || 'Failed to modify message.';
        Alert.alert('Error', message);
      }
    },
    [backend, chatController],
  );

  const handleCancelEditMessage = useCallback(() => {
    setEditingIndex(null);
    setEditingText('');
    setEditingInitialText('');
  }, []);

  const handleMessageAction = useCallback(
    async (action: MessageActionKey, index: number, message: any) => {
      if (action === 'modify') {
        handleStartEditMessage(index, message);
        return;
      }

      if (action === 'toggleMarkdown') {
        if ((message?.role || 'unknown') !== 'assistant') {
          return;
        }
        setMessageViewModeByIndex((prev) => {
          const current = prev[index] ?? 'markdown';
          const next = current === 'markdown' ? 'raw' : 'markdown';
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
        try {
          Clipboard.setString(content);
          Alert.alert('Copied', 'Message content copied to clipboard.');
        } catch {
          Alert.alert('Copy failed', 'Clipboard is not available.');
        }
      }
    },
    [handleStartEditMessage],
  );

  const streamingFooter = useMemo(() => {
    if (!streamingRow || (!streamingRow.content && !streamingRow.reasoning)) {
      return null;
    }

    const streamingIndex = messages.length > 0 ? messages[messages.length - 1].index + 1 : 0;
    return (
      <DesktopMessageBubble
        index={streamingIndex}
        message={{
          role: 'assistant',
          content: streamingRow.content,
          metadata: {
            ...(streamingRow.metadata || {}),
            reasoning: streamingRow.reasoning,
          },
        }}
        renderMode="markdown"
        footerElements={footerElements}
      />
    );
  }, [
    footerElements,
    messages,
    streamingRow,
  ]);

  const renderMessageItem = useCallback(
    ({ item: msg }: { item: IndexedMessage; index: number }) => {
      const role = msg.message.role || 'unknown';
      const allowedActions = ALL_MESSAGE_ACTIONS
        .filter((def) => def.allowedRoles.includes(role))
        .map((def) => def.key as MessageActionKey);
      const isEditing = editingIndex === msg.index;
      const defaultModeForRole: 'markdown' | 'raw' = role === 'assistant' ? 'markdown' : 'raw';
      const renderMode = messageViewModeByIndex[msg.index] ?? defaultModeForRole;

      return (
        <DesktopMessageBubble
          index={msg.index}
          message={msg.message}
          allowedActions={allowedActions}
          onAction={(action, index, message) => handleMessageAction(action, index, message)}
          isEditing={isEditing}
          editingInitialText={isEditing ? editingInitialText : undefined}
          editingText={isEditing ? editingText : undefined}
          onChangeEditingText={isEditing ? setEditingText : undefined}
          onSubmitEdit={(index, _message, nextText) => handleSubmitEditMessage(index, nextText)}
          onCancelEdit={handleCancelEditMessage}
          renderMode={renderMode}
          footerElements={footerElements}
        />
      );
    },
    [
      editingIndex,
      editingInitialText,
      editingText,
      footerElements,
      handleCancelEditMessage,
      handleMessageAction,
      handleSubmitEditMessage,
      messageViewModeByIndex,
    ],
  );

  return (
	  <View style={styles.root}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
          <View style={styles.metaRow}>
            <Text style={styles.metaText} numberOfLines={1}>
              {connectionName}
            </Text>
            <Text style={styles.metaDot}>•</Text>
            <Text style={styles.metaText} numberOfLines={1}>
              {sessionId}
            </Text>
            <Text style={styles.metaDot}>•</Text>
            <View
              style={[
                styles.statusDot,
                { backgroundColor: backend ? theme.success : theme.textMuted },
              ]}
            />
            <Text style={styles.metaText} numberOfLines={1}>
              {backend ? 'Online' : 'Offline'}
            </Text>
          </View>
          {subtitle ? (
            <Text style={styles.subtitle} numberOfLines={1}>
              {subtitle}
            </Text>
          ) : null}
        </View>

        <View style={styles.headerRight}>
          <ActionsMenuBar<ActionDefinition>
            title="Session actions"
            variant="dropdown"
	          isActive={isActive}
            renderIcon={({ name, size, color }) => <Icon name={name} size={size} color={color} />}
            baseActions={BUILTIN_SESSION_ACTIONS}
            pinned={pinnedSessionActionKeys}
            onChangePinned={(next) => setPinnedSessionActionKeys(next)}
            onAction={handleSessionAction}
            isActionDisabled={(key) => {
              if (!canRunHeaderActions) {
                return true;
              }
              if (key === 'reload') {
                return reloadInFlight || (chatState?.loading ?? false);
              }
              if (key === 'cancel') {
                return cancelInFlight || !chatState?.activeRequestId;
              }
              if (key === 'agentSwitch') {
                return openingAgentPicker || (agentsState?.loading ?? false);
              }
              if (key === 'settings') {
                const caps = backend.getCapabilities?.();
                if (caps && (!caps.sessionUiSchema || !caps.sessionConfigOverrides)) {
                  return true;
                }
                return false;
              }
              return false;
            }}
          />
        </View>
      </View>

      <View style={styles.body}>
        <View style={styles.statusRow}>
          <Text style={styles.hintSecondary}>Messages: {messagesCount}</Text>
          <Text style={styles.hintSecondary}>
            Streaming: {chatController?.isEventStreaming() ? 'on' : 'off'}
          </Text>
        </View>

        {chatState?.loading ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color={theme.textSecondary} />
            <Text style={styles.hintSecondary}>Loading…</Text>
          </View>
        ) : null}

        {loadError ? (
          <View style={styles.errorRow}>
            <Text style={styles.errorText} numberOfLines={2}>
              {loadError}
            </Text>
            <Pressable
              style={({ pressed }) => [styles.retryButton, pressed && styles.retryButtonPressed]}
              onPress={() => {
                attemptedInitialLoadRef.current = true;
                loadInitialMessages().catch(() => {
                  // errors are handled in `loadInitialMessages`
                });
              }}
            >
              <Text style={styles.retryButtonText}>Retry</Text>
            </Pressable>
          </View>
        ) : null}


	        <PinnedMessageActionsProvider value={pinnedMessageActionsContextValue}>
	          <PlaceholderFlatList
	            style={styles.transcript}
	            contentContainerStyle={styles.transcriptContent}
	            data={messages}
	            keyExtractor={(item) => String(item.index)}
	            getItemDependencies={(item) => {
	              const role = item.message.role || 'unknown';
	              const defaultModeForRole: 'markdown' | 'raw' =
	                role === 'assistant' ? 'markdown' : 'raw';
	              const renderMode =
	                messageViewModeByIndex[item.index] ?? defaultModeForRole;
	              const isEditing = item.index === editingIndex;
	              return [
	                renderMode,
	                footerElements,
	                isEditing,
	                isEditing ? editingInitialText : null,
	                isEditing ? editingText : null,
	              ];
	            }}
	            scrollEventThrottle={16}
	            renderItem={renderMessageItem}
	            ListEmptyComponent={
	              !chatState?.loading ? <Text style={styles.hintSecondary}>No messages.</Text> : null
	            }
	            ListFooterComponent={streamingFooter}
	          />
	        </PinnedMessageActionsProvider>

        <View style={styles.composerRow}>
          <View
            style={[
              styles.composerInputFrame,
              { height: composerHeight },
              !backend && styles.composerInputDisabled,
            ]}
          >
            <MacTextView
              ref={composerRef}
              style={styles.composerInput}
              placeholder={backend ? 'Type a message…' : 'Offline (read-only)'}
              placeholderTextColor={theme.textMuted}
              textColor={theme.text}
              fontSize={13}
              editable={backend != null && !sendInFlight}
              autoGrow
              minHeight={34}
              maxHeight={120}
              onHeightChange={handleComposerHeightChange}
              onChangeText={(text) => {
                composeTextRef.current = text;
                setComposeText(text);
              }}
              onSubmit={(text) => {
                handleSend(text).catch(() => {
                  // errors are handled in `handleSend`
                });
              }}
            />
          </View>
          <Pressable
            style={({ pressed }) => [
              styles.sendButton,
              (!canSend || !composeText.trim()) && styles.sendButtonDisabled,
              pressed && canSend && composeText.trim() && styles.sendButtonPressed,
            ]}
            disabled={!canSend || !composeText.trim()}
            onPress={() => {
              handleSend(composeTextRef.current).catch(() => {
                // errors are handled in `handleSend`
              });
            }}
          >
            <Text style={styles.sendButtonText}>{sendInFlight ? '…' : 'Send'}</Text>
          </Pressable>
        </View>
      </View>

      {Platform.OS !== 'macos' && messageLimitVisible && (
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
                Python-style range (start:end). Example: -{DEFAULT_HISTORY_WINDOW}: for last{' '}
                {DEFAULT_HISTORY_WINDOW} messages. Leave blank for all messages.
              </Text>
              <View style={styles.rangeRow}>
                <View style={styles.rangeInputContainer}>
                  <Text style={styles.rangeLabel}>Start</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={rangeStartText}
                    onChangeText={setRangeStartText}
                    placeholder={`e.g. -${DEFAULT_HISTORY_WINDOW}`}
                  />
                </View>
                <View style={styles.rangeInputContainer}>
                  <Text style={styles.rangeLabel}>End</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={rangeEndText}
                    onChangeText={setRangeEndText}
                    placeholder="optional"
                  />
                </View>
              </View>
              <View style={styles.modalButtonsRow}>
                <Pressable
                  style={({ pressed }) => [
                    styles.modalButton,
                    styles.modalButtonSecondary,
                    pressed && styles.modalButtonPressed,
                  ]}
                  onPress={() => setMessageLimitVisible(false)}
                >
                  <Text style={styles.modalButtonSecondaryText}>Cancel</Text>
                </Pressable>
                <Pressable
                  style={({ pressed }) => [
                    styles.modalButton,
                    styles.modalButtonPrimary,
                    pressed && styles.modalButtonPressed,
                  ]}
                  onPress={() => {
                    setMessageLimitVisible(false);
                    applyMessageLimitAndReload({ startText: rangeStartText, endText: rangeEndText }).catch(
                      () => {},
                    );
                  }}
                >
                  <Text style={styles.modalButtonPrimaryText}>Apply</Text>
                </Pressable>
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
    </View>
  );
});

function createStyles(theme: ReturnType<typeof useTheme>, styleVariant: TabStripStyle) {
  const codeLike = styleVariant === 'codeTabs' || styleVariant === 'underlineTabs';
  const radius = styleVariant === 'roundedPills' ? 12 : 10;
  const separatorWidth = 1;

  return StyleSheet.create({
    root: {
		  flex: 1,
      borderWidth: codeLike ? 0 : separatorWidth,
      borderColor: codeLike ? 'transparent' : theme.border,
      borderRadius: codeLike ? 0 : radius,
      backgroundColor: theme.surface,
      overflow: codeLike ? 'visible' : 'hidden',
    },
    header: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
      gap: 10,
      backgroundColor: theme.surface,
    },
    headerLeft: {
      flex: 1,
      gap: 4,
    },
    headerRight: {
      paddingTop: Platform.OS === 'macos' ? 2 : 0,
    },
    title: {
      fontSize: 14,
      fontWeight: '700',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    metaRow: {
      flexDirection: 'row',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: 6,
    },
    metaText: {
      fontSize: 11,
      color: theme.textMuted,
      fontWeight: '600',
    },
    metaDot: {
      fontSize: 11,
      color: theme.textMuted,
      marginTop: -1,
    },
    statusDot: {
      width: 7,
      height: 7,
      borderRadius: 999,
      marginTop: 1,
    },
    modalOverlay: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      padding: 20,
      backgroundColor: 'rgba(0,0,0,0.4)',
    },
    modalContent: {
      width: 360,
      maxWidth: '100%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: theme.border,
      padding: 16,
      gap: 10,
    },
    modalTitle: {
      fontSize: 16,
      fontWeight: '800',
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    rangeRow: {
      flexDirection: 'row',
      gap: 12,
    },
    rangeInputContainer: {
      flex: 1,
      gap: 6,
    },
    rangeLabel: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.textSecondary,
    },
    modalInput: {
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      fontSize: 13,
    },
    modalButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 10,
      marginTop: 2,
    },
    modalButton: {
      borderRadius: 10,
      paddingVertical: 10,
      paddingHorizontal: 14,
      borderWidth: 1,
    },
    modalButtonSecondary: {
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
    },
    modalButtonPrimary: {
      borderColor: theme.primary,
      backgroundColor: theme.primary,
    },
    modalButtonPressed: {
      opacity: 0.85,
    },
    modalButtonSecondaryText: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    modalButtonPrimaryText: {
      fontSize: 13,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    modalHelperText: {
      fontSize: 11,
      color: theme.textMuted,
    },
    body: {
      flex: 1,
      padding: 12,
      gap: 10,
    },
    statusRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: 12,
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    errorRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderRadius: 10,
      backgroundColor: 'rgba(255, 0, 0, 0.08)',
      borderWidth: separatorWidth,
      borderColor: theme.border,
    },
    errorText: {
      flex: 1,
      fontSize: 12,
      color: theme.text,
    },
    retryButton: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    retryButtonPressed: {
      opacity: 0.8,
    },
    retryButtonText: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.primary,
    },
    transcript: {
      flex: 1,
    },
    transcriptContent: {
      paddingBottom: 12,
    },
    composerRow: {
      flexDirection: 'row',
      alignItems: 'flex-end',
      gap: 8,
      paddingTop: 10,
      borderTopWidth: separatorWidth,
      borderTopColor: theme.border,
    },
    composerInputFrame: {
      flex: 1,
      minHeight: 34,
      borderRadius: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    composerInput: {
      flex: 1,
    },
    composerInputDisabled: {
      opacity: 0.7,
    },
    sendButton: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    sendButtonPressed: {
      opacity: 0.85,
    },
    sendButtonDisabled: {
      opacity: 0.5,
    },
    sendButtonText: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.primary,
    },
    messageRow: {
      borderWidth: separatorWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      gap: 6,
    },
    messageRowAssistant: {
      backgroundColor: 'rgba(120, 120, 120, 0.12)',
    },
    messageMeta: {
      fontSize: 11,
      fontWeight: '600',
      color: theme.textSecondary,
    },
    messageText: {
      fontSize: 13,
      lineHeight: 18,
      color: theme.text,
    },
    hint: {
      fontSize: 13,
      color: theme.text,
    },
    hintSecondary: {
      fontSize: 12,
      color: theme.textSecondary,
    },
  });
}
