import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  ActionsMenuBar,
  useTheme,
  type ActionDefinition,
  type ActionKey,
} from '@crystal-lattice/frontend-rn-components';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';
import {
  useAgentsController,
  useChatController,
  useHydrateControllerFromCache,
  usePersistentPinnedActions,
} from '@crystal-lattice/frontend-sdk-react';

import type { MessagesCacheEntry } from '../cache/types';
import type { TabStripStyle } from '../tabs/tabStripStyle';
import { asyncStorageKeyValueStore } from '../storage/asyncStorageKeyValueStore';
import { DesktopWindowManager } from '../windows/desktopWindowManager';
import { setActiveSessionSettingsWindow } from '../windows/sessionSettingsCoordinator';
import DesktopMessageBubble from './DesktopMessageBubble';

const DEFAULT_HISTORY_WINDOW = 50;
const PINNED_SESSION_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_chat_session_actions_v1';

type ChatSessionActionKey = 'reload' | 'cancel' | 'agentSwitch' | 'settings';

const BUILTIN_SESSION_ACTIONS: ActionDefinition[] = [
  { key: 'reload', label: 'Reload', iconName: 'refresh-ccw' },
  { key: 'cancel', label: 'Cancel', iconName: 'x-circle' },
  { key: 'agentSwitch', label: 'Switch agent', iconName: 'user' },
  { key: 'settings', label: 'Settings…', iconName: 'sliders' },
];

const DEFAULT_PINNED_SESSION_ACTION_KEYS: ActionKey[] = ['reload', 'cancel'];

export interface ChatPaneProps {
  visible: boolean;
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

export function ChatPane({
  visible,
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
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, styleVariant), [theme, styleVariant]);

  const [renderMarkdown] = useState(true);

  const [loadError, setLoadError] = useState<string | null>(null);
  const [composeText, setComposeText] = useState('');
  const [sendInFlight, setSendInFlight] = useState(false);
  const [reloadInFlight, setReloadInFlight] = useState(false);
  const [cancelInFlight, setCancelInFlight] = useState(false);
  const [openingAgentPicker, setOpeningAgentPicker] = useState(false);
  const inputRef = useRef<TextInput>(null);
  const attemptedInitialLoadRef = useRef(false);
  const pendingPersistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastPersistKeyRef = useRef<string | null>(null);

  const [debugEvents, setDebugEvents] = useState<string[]>([]);
  const debugEnabled = __DEV__;
  const pushDebug = useCallback(
    (label: string) => {
      if (!debugEnabled) {
        return;
      }
      const line = `${new Date().toISOString().slice(11, 23)} ${label}`;
      setDebugEvents((prev) => {
        const next = [...prev, line];
        return next.length > 10 ? next.slice(next.length - 10) : next;
      });
      console.log(`[ChatPane ${connectionId}:${sessionId}] ${label}`);
    },
    [connectionId, debugEnabled, sessionId],
  );

  const logComposerFocusState = useCallback(
    (prefix: string) => {
      if (!debugEnabled) {
        return;
      }

      try {
        const current = TextInput.State.currentlyFocusedInput();
        const currentIsComposer = current != null && current === (inputRef.current as any);
        const composerIsFocused = inputRef.current?.isFocused?.() ?? false;
        pushDebug(
          `${prefix} composerIsFocused=${composerIsFocused} currentIsComposer=${currentIsComposer} hasCurrent=${current != null}`,
        );
      } catch {
        pushDebug(`${prefix} focusState=error`);
      }
    },
    [debugEnabled, pushDebug],
  );

  const { controller: chatController, state: chatState } = useChatController({
    backend,
    sessionId,
    initialMessages: cachedEntry?.messages ?? [],
    initialEventsCursorId: cachedEntry?.cursorEventId ?? null,
    initialActiveRequestId: cachedEntry?.activeRequestId ?? null,
    eventsEnabled: visible && backend != null,
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

  const { controller: agentsController, state: agentsState } = useAgentsController({
    backend,
    cacheKey: connectionId,
    enabled: false,
  });

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

    chatController.setHistoryRange({ start: -DEFAULT_HISTORY_WINDOW });
  }, [chatController]);

  useEffect(() => {
    pushDebug('mount');
    return () => {
      pushDebug('unmount');
    };
  }, [pushDebug]);

  useEffect(() => {
    if (!debugEnabled) {
      return;
    }

    let lastFocused = false;
    const timer = setInterval(() => {
      try {
        const focused = TextInput.State.currentlyFocusedInput();
        const isFocused = focused != null && focused === (inputRef.current as any);
        if (isFocused !== lastFocused) {
          lastFocused = isFocused;
          pushDebug(`poll composerFocused=${isFocused}`);
        }
      } catch {
        // ignore
      }
    }, 250);

    return () => {
      clearInterval(timer);
    };
  }, [debugEnabled, pushDebug]);

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
      await chatController.loadMessages({ start: -DEFAULT_HISTORY_WINDOW });
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to load messages.';
      setLoadError(message);
      Alert.alert('Failed to load messages', message);
    }
  }, [chatController]);

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
    if (!visible) {
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
  }, [chatController, chatState?.eventsCursorId, chatState?.loading, chatState?.messages, loadInitialMessages, visible]);

  const messages: IndexedMessage[] =
    chatState?.messages ?? cachedEntry?.messages ?? [];
  const streamingRow = chatState?.streamingRow ?? null;

  const messagesCount = messages.length;

  const canSend = backend != null && chatController != null && visible && !sendInFlight;

  const handleSend = useCallback(async () => {
    if (!canSend) {
      return;
    }

    const trimmed = composeText.trim();
    if (!trimmed) {
      return;
    }

    setSendInFlight(true);
    try {
      await chatController.appendMessage({ role: 'user', content: trimmed });
      setComposeText('');
      await chatController.send();
      inputRef.current?.focus();
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

  const canRunHeaderActions = backend != null && chatController != null && visible;

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
      await chatController.loadMessages({ start: -DEFAULT_HISTORY_WINDOW });
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
  }, [canRunHeaderActions, chatController, reloadInFlight]);

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
    [backend, connectionId, connectionName, handleCancel, handleReload, openAgentPickerForSwitch, sessionId],
  );

  return (
    <View style={[styles.root, visible ? styles.visible : styles.hidden]}>
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
            isActive={visible}
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
              onFocus={() => pushDebug('retry focus')}
              onBlur={() => pushDebug('retry blur')}
              onPress={() => {
                pushDebug('retry press');
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

        <ScrollView
          style={styles.transcript}
          contentContainerStyle={styles.transcriptContent}
          onFocus={() => pushDebug('transcript focus')}
          onBlur={() => pushDebug('transcript blur')}
        >
          {messages.length === 0 && !chatState?.loading ? (
            <Text style={styles.hintSecondary}>No messages.</Text>
          ) : null}
          {messages.map((msg) => (
            <DesktopMessageBubble
              key={msg.index}
              index={msg.index}
              message={msg.message}
              renderMode={renderMarkdown ? 'markdown' : 'raw'}
            />
          ))}
          {streamingRow && (streamingRow.content || streamingRow.reasoning) ? (
            <DesktopMessageBubble
              key="streaming"
              index={null}
              isStreaming
              message={{
                role: 'assistant',
                content: streamingRow.content,
                metadata: {
                  ...(streamingRow.metadata || {}),
                  reasoning: streamingRow.reasoning,
                },
              }}
              renderMode={renderMarkdown ? 'markdown' : 'raw'}
            />
          ) : null}
        </ScrollView>

        {debugEnabled ? (
          <View style={styles.debugBox}>
            <Text style={styles.debugTitle}>Focus debug</Text>
            {debugEvents.slice().reverse().map((line) => (
              <Text key={line} style={styles.debugLine}>
                {line}
              </Text>
            ))}
          </View>
        ) : null}

        <View style={styles.composerRow}>
          <TextInput
            ref={inputRef}
            style={[styles.composerInput, !backend && styles.composerInputDisabled]}
            value={composeText}
            placeholder={backend ? 'Type a message…' : 'Offline (read-only)'}
            placeholderTextColor={theme.textMuted}
            onChangeText={setComposeText}
            editable={backend != null && !sendInFlight}
            autoCorrect={false}
            spellCheck={false}
            multiline
            submitBehavior="newline"
            onFocus={() => {
              pushDebug('composer focus');
              logComposerFocusState('composer focus');
            }}
            onBlur={() => {
              pushDebug('composer blur');
              logComposerFocusState('composer blur');
              setTimeout(() => {
                logComposerFocusState('composer blur +50ms');
              }, 50);
            }}
            onKeyPress={(event) => {
              const key = (event.nativeEvent as any)?.key;
              const shiftKey = (event.nativeEvent as any)?.shiftKey === true;
              const ctrlKey = (event.nativeEvent as any)?.ctrlKey === true;
              const metaKey = (event.nativeEvent as any)?.metaKey === true;
              const altKey = (event.nativeEvent as any)?.altKey === true;
              pushDebug(
                `composer key=${JSON.stringify(key)} shift=${shiftKey} ctrl=${ctrlKey} alt=${altKey} meta=${metaKey}`,
              );

              setTimeout(() => {
                logComposerFocusState(`after key=${JSON.stringify(key)} +0ms`);
              }, 0);
              setTimeout(() => {
                logComposerFocusState(`after key=${JSON.stringify(key)} +50ms`);
              }, 50);

              if (key !== 'Enter') {
                return;
              }

              if (shiftKey) {
                return;
              }

              (event as any)?.preventDefault?.();
              (event as any)?.stopPropagation?.();

              handleSend().catch(() => {
                // errors are handled in `handleSend`
              });
            }}
          />
          <Pressable
            style={({ pressed }) => [
              styles.sendButton,
              (!canSend || !composeText.trim()) && styles.sendButtonDisabled,
              pressed && canSend && composeText.trim() && styles.sendButtonPressed,
            ]}
            disabled={!canSend || !composeText.trim()}
            onFocus={() => pushDebug('send focus')}
            onBlur={() => pushDebug('send blur')}
            onPress={() => {
              pushDebug('send press');
              handleSend().catch(() => {
                // errors are handled in `handleSend`
              });
            }}
          >
            <Text style={styles.sendButtonText}>{sendInFlight ? '…' : 'Send'}</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

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
    visible: {
      display: 'flex',
    },
    hidden: {
      display: 'none',
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
      gap: 10,
      paddingBottom: 12,
    },
    debugBox: {
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderRadius: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      gap: 4,
    },
    debugTitle: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.textSecondary,
    },
    debugLine: {
      fontSize: 11,
      color: theme.textMuted,
    },
    composerRow: {
      flexDirection: 'row',
      alignItems: 'flex-end',
      gap: 8,
      paddingTop: 10,
      borderTopWidth: separatorWidth,
      borderTopColor: theme.border,
    },
    composerInput: {
      flex: 1,
      minHeight: 34,
      maxHeight: 120,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderRadius: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      color: theme.text,
      fontSize: 13,
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
