import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';
import { useChatController, useHydrateControllerFromCache } from '@crystal-lattice/frontend-sdk-react';

import type { MessagesCacheEntry } from '../cache/types';
import type { TabStripStyle } from '../tabs/tabStripStyle';

const DEFAULT_HISTORY_WINDOW = 50;

export interface ChatPaneProps {
  visible: boolean;
  connectionId: string;
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

  const [loadError, setLoadError] = useState<string | null>(null);
  const [composeText, setComposeText] = useState('');
  const [sendInFlight, setSendInFlight] = useState(false);
  const inputRef = useRef<TextInput>(null);
  const lastShiftEnterAtRef = useRef<number | null>(null);
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
  const streamingRowText = chatState?.streamingRow?.content ?? null;

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

  return (
    <View style={[styles.root, visible ? styles.visible : styles.hidden]}>
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>
        {subtitle ? (
          <Text style={styles.subtitle} numberOfLines={1}>
            {subtitle}
          </Text>
        ) : null}
      </View>

      <View style={styles.body}>
        <View style={styles.statusRow}>
          <Text style={styles.hintSecondary}>
            {backend ? 'Online' : 'Offline'} • Messages: {messagesCount}
          </Text>
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

        <ScrollView style={styles.transcript} contentContainerStyle={styles.transcriptContent}>
          {messages.length === 0 && !chatState?.loading ? (
            <Text style={styles.hintSecondary}>No messages.</Text>
          ) : null}
          {messages.map((msg) => (
            <MessageRow key={msg.index} message={msg} theme={theme} />
          ))}
          {streamingRowText ? (
            <View style={[styles.messageRow, styles.messageRowAssistant]}>
              <Text style={styles.messageMeta} numberOfLines={1}>
                assistant • streaming
              </Text>
              <Text style={styles.messageText}>{streamingRowText}</Text>
            </View>
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

function MessageRow({
  message,
  theme,
}: {
  message: IndexedMessage;
  theme: ReturnType<typeof useTheme>;
}): React.JSX.Element {
  const role = message.message.role;
  const content = message.message.content;

  const roleStyle =
    role === 'assistant'
      ? stylesLocal.messageRowAssistant
      : role === 'user'
        ? stylesLocal.messageRowUser
        : stylesLocal.messageRowOther;

  return (
    <View style={[stylesLocal.messageRow, roleStyle, { borderColor: theme.border }]}>
      <Text style={[stylesLocal.messageMeta, { color: theme.textSecondary }]} numberOfLines={1}>
        {role} • #{message.index}
      </Text>
      <Text style={[stylesLocal.messageText, { color: theme.text }]}>{content}</Text>
    </View>
  );
}

const stylesLocal = StyleSheet.create({
  messageRow: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
    gap: 6,
  },
  messageRowUser: {
    backgroundColor: 'rgba(60, 130, 255, 0.10)',
  },
  messageRowAssistant: {
    backgroundColor: 'rgba(120, 120, 120, 0.12)',
  },
  messageRowOther: {
    backgroundColor: 'rgba(120, 120, 120, 0.08)',
  },
  messageMeta: {
    fontSize: 11,
    fontWeight: '600',
  },
  messageText: {
    fontSize: 13,
    lineHeight: 18,
  },
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
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
      gap: 2,
      backgroundColor: theme.surface,
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
