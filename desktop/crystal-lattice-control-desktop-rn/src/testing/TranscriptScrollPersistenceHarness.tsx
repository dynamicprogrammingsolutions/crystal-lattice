import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';

import {
  createChatMessageViewportScrollAnchor,
  createChatScrollAnchor,
} from '../chat/chatScroll';
import { useProactiveChatScrollPersistence } from '../chat/useProactiveChatScrollPersistence';
import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';
import { DependencyFlatList } from '../ui/DependencyFlatList';
import { PlaceholderFlatList } from '../ui/PlaceholderFlatList';
import { ProgressiveScrollList } from '../ui/ProgressiveScrollList';
import { DesktopWindowManager, desktopWindowEvents } from '../windows/desktopWindowManager';

type HarnessMessage = IndexedMessage;

type TranscriptListImplementation = 'scrollView' | 'flatList' | 'progressiveScroll';
type ProgressiveBackingList = 'scrollView' | 'flatList';

type HarnessProps = {
  scrollHarnessRunId?: string;
  transcriptScrollListImplementation?: string;
  progressiveScrollBackingList?: string;
  initialRestoreReady?: boolean;
};

const TOTAL_MESSAGES = 180;
const TARGET_MESSAGE_INDEX = 120;
const FAR_TARGET_MESSAGE_INDEX = 170;
const TARGET_MESSAGE_OFFSET = 40;
const TARGET_SCROLL_OFFSET = 420;
const HARNESS_CONTENT_FOLLOW_LEASE_MS = 700;
const HARNESS_NAVIGATION_MAX_MS = 15000;
const HARNESS_MAX_EDGE_CORRECTIONS = 60;
const HARNESS_ITEM_ANCHOR_TIMEOUT_MS = 15000;
const HARNESS_ITEM_ANCHOR_MAX_ATTEMPTS = 200;

function buildMessages(): HarnessMessage[] {
  return Array.from({ length: TOTAL_MESSAGES }, (_, index) => {
    const lines = 1 + (index % 6);
    return {
      index,
      message: {
        role: index % 2 === 0 ? 'assistant' : 'user',
        content: Array.from(
          { length: lines },
          () => `Transcript persistence harness message ${index}.`,
        ).join(' '),
      },
    };
  });
}

function normalizeImplementation(value: unknown): TranscriptListImplementation {
  return value === 'flatList' || value === 'progressiveScroll' ? value : 'scrollView';
}

function normalizeBackingList(value: unknown): ProgressiveBackingList {
  return value === 'flatList' ? 'flatList' : 'scrollView';
}

function scrollToOffset(target: any, offset: number) {
  if (!target) {
    return;
  }
  if (typeof target.scrollToOffset === 'function') {
    target.scrollToOffset({ offset, animated: false });
    return;
  }
  if (typeof target.scrollTo === 'function') {
    target.scrollTo({ y: offset, animated: false });
  }
}

function describeAnchor(anchor: any): Record<string, unknown> | null {
  if (!anchor || typeof anchor !== 'object') {
    return null;
  }
  if (anchor.kind === 'messageViewport') {
    return {
      kind: 'messageViewport',
      messageIndex: anchor.messageIndex,
      offsetFromViewportTop:
        typeof anchor.offsetFromViewportTop === 'number'
          ? Math.round(anchor.offsetFromViewportTop)
          : null,
      pinnedToBottom: anchor.pinnedToBottom,
      bottomGapPx: typeof anchor.bottomGapPx === 'number' ? Math.round(anchor.bottomGapPx) : null,
    };
  }
  return {
    kind: 'offset',
    bottomGapPx: typeof anchor.bottomGapPx === 'number' ? Math.round(anchor.bottomGapPx) : null,
    pinnedToBottom: anchor.pinnedToBottom,
  };
}

export function TranscriptScrollPersistenceHarness({
  scrollHarnessRunId = '',
  transcriptScrollListImplementation = 'scrollView',
  progressiveScrollBackingList = 'scrollView',
  initialRestoreReady = true,
}: HarnessProps): React.JSX.Element {
  const implementation = normalizeImplementation(transcriptScrollListImplementation);
  const backingList = normalizeBackingList(progressiveScrollBackingList);
  const [messages, setMessages] = useState<HarnessMessage[]>(() => buildMessages());
  const [bottomContentRevision, setBottomContentRevision] = useState(0);
  const [geometryPulseHeight, setGeometryPulseHeight] = useState(0);
  const [cachedScrollAnchor, setCachedScrollAnchor] = useState<unknown>(null);
  const [restoreReady, setRestoreReady] = useState(initialRestoreReady);
  const [restoreVersion, setRestoreVersion] = useState(0);
  const [status, setStatus] = useState('ready');
  const savedAnchorRef = useRef<unknown>(null);
  const cachedScrollAnchorRef = useRef<unknown>(null);
  const restoreReadyRef = useRef(initialRestoreReady);
  const diagnosticsRef = useRef<Array<Record<string, unknown>>>([]);
  const diagnosticEventCountsRef = useRef<Record<string, number>>({});
  const contentFollowCorrectionCountRef = useRef(0);
  const contentFollowTerminalCountRef = useRef(0);
  const navigationCorrectionCountRef = useRef(0);
  const navigationTerminalCountRef = useRef(0);
  const listAnchorStartedDetailsRef = useRef<Record<string, unknown> | null>(null);
  const effectiveScrollConfigurationRef = useRef<Record<string, unknown> | null>(null);
  const feedbackPulseEnabledRef = useRef(false);
  const feedbackPulseCountRef = useRef(0);
  const lastCommandKeyRef = useRef<string | null>(null);
  const pendingResetReasonRef = useRef<string | null>(null);

  const recordDiagnostic = useCallback((entry: Record<string, unknown>) => {
    diagnosticsRef.current = [...diagnosticsRef.current.slice(-119), { at: Date.now(), ...entry }];
    const event = typeof entry.event === 'string' ? entry.event : 'unknown';
    diagnosticEventCountsRef.current[event] =
      (diagnosticEventCountsRef.current[event] ?? 0) + 1;
    const details =
      entry.details != null && typeof entry.details === 'object'
        ? (entry.details as Record<string, unknown>)
        : null;
    const purpose = details?.purpose;
    if (event === 'operationCorrection') {
      if (purpose === 'contentFollow') {
        contentFollowCorrectionCountRef.current += 1;
      } else if (purpose === 'navigation') {
        navigationCorrectionCountRef.current += 1;
      }
    }
    if (
      event === 'operationCompleted' ||
      event === 'operationExpired' ||
      event === 'operationCorrectionLimit' ||
      event === 'operationUnavailable' ||
      event === 'operationCancelled'
    ) {
      if (purpose === 'contentFollow') {
        contentFollowTerminalCountRef.current += 1;
      } else if (purpose === 'navigation') {
        navigationTerminalCountRef.current += 1;
      }
    }
    if (event === 'listAnchorStarted') {
      listAnchorStartedDetailsRef.current = details;
    }
  }, []);

  const resetDiagnostics = useCallback(() => {
    diagnosticsRef.current = [];
    diagnosticEventCountsRef.current = {};
    contentFollowCorrectionCountRef.current = 0;
    contentFollowTerminalCountRef.current = 0;
    navigationCorrectionCountRef.current = 0;
    navigationTerminalCountRef.current = 0;
    listAnchorStartedDetailsRef.current = null;
  }, []);

  useEffect(() => {
    cachedScrollAnchorRef.current = cachedScrollAnchor;
  }, [cachedScrollAnchor]);

  useEffect(() => {
    restoreReadyRef.current = restoreReady;
  }, [restoreReady]);

  const getMessagesForCache = useCallback(() => messages, [messages]);
  const handleUpdateCache = useCallback(
    ({ scrollAnchor }: { scrollAnchor?: unknown }) => {
      savedAnchorRef.current = scrollAnchor;
      recordDiagnostic({
        event: 'cacheUpdated',
        anchor: describeAnchor(scrollAnchor),
      });
    },
    [recordDiagnostic],
  );
  const handleDiagnosticEvent = useCallback(
    (event: { event: string; reason?: string; details?: Record<string, unknown> }) => {
      if (event.event === 'configuration') {
        effectiveScrollConfigurationRef.current = event.details ?? null;
      }
      recordDiagnostic({
        event: event.event,
        reason: event.reason ?? null,
        details: event.details ?? null,
      });
    },
    [recordDiagnostic],
  );

  const transcriptScroll = useProactiveChatScrollPersistence({
    connectionId: 'harness-connection',
    sessionId: 'harness-session',
    cachedScrollAnchor,
    getMessagesForCache,
    onUpdateCache: handleUpdateCache,
    enabled: true,
    restoreReady,
    bottomThresholdPx: 4,
    contentFollowEnabled: true,
    contentFollowLeaseMs: HARNESS_CONTENT_FOLLOW_LEASE_MS,
    manualBottomConvergenceMaxMs: HARNESS_NAVIGATION_MAX_MS,
    initialBottomConvergenceMaxMs: HARNESS_NAVIGATION_MAX_MS,
    bottomContentRevision,
    maxEdgeCorrections: HARNESS_MAX_EDGE_CORRECTIONS,
    messageViewportAnchorsEnabled:
      implementation === 'flatList' || implementation === 'progressiveScroll',
    listEdgeMethodsEnabled: implementation === 'progressiveScroll',
    onDiagnosticEvent: handleDiagnosticEvent,
  });

  useEffect(() => {
    const reason = pendingResetReasonRef.current;
    if (!reason) {
      return;
    }
    pendingResetReasonRef.current = null;
    transcriptScroll.resetRestore(reason);
  }, [cachedScrollAnchor, restoreReady, restoreVersion, transcriptScroll]);

  const waitForListSettled = useCallback(
    (callback: () => void, timeoutMs = 4000) => {
      const startedAt = Date.now();
      const poll = () => {
        const pending =
          typeof transcriptScroll.listRef.current?.hasPendingScrollAction === 'function' &&
          transcriptScroll.listRef.current.hasPendingScrollAction();
        if (!pending || Date.now() - startedAt > timeoutMs) {
          callback();
          return;
        }
        setTimeout(poll, 80);
      };
      setTimeout(poll, 80);
    },
    [transcriptScroll.listRef],
  );

  const recordHarnessState = useCallback(
    (command: string, statusOverride?: string, extra?: Record<string, unknown>) => {
      const list = transcriptScroll.listRef.current;
      const getVisibleAnchor = list?.getVisibleAnchor;
      const getItemViewportOffset = list?.getItemViewportOffset;
      Promise.all([
        getMacScrollViewMetrics(list),
        Promise.resolve(typeof getVisibleAnchor === 'function' ? getVisibleAnchor() : null),
        Promise.resolve(
          typeof getItemViewportOffset === 'function'
            ? getItemViewportOffset(`msg-${TARGET_MESSAGE_INDEX}`)
            : null,
        ),
        Promise.resolve(
          typeof getItemViewportOffset === 'function'
            ? getItemViewportOffset(`msg-${FAR_TARGET_MESSAGE_INDEX}`)
            : null,
        ),
      ])
        .then(([metrics, visibleAnchor, targetOffset, farTargetOffset]) => {
          const maxOffsetY =
            metrics != null ? Math.max(0, metrics.contentHeight - metrics.viewportHeight) : null;
          DesktopWindowManager?.recordProgressiveScrollHarnessState?.({
            command,
            runId: scrollHarnessRunId,
            status: statusOverride ?? status,
            implementation,
            backingList,
            restoreReady: restoreReadyRef.current,
            targetMessageIndex: TARGET_MESSAGE_INDEX,
            targetMessageRequestedOffsetFromViewportTop: TARGET_MESSAGE_OFFSET,
            targetMessageActualOffsetFromViewportTop:
              typeof targetOffset === 'number' ? Math.round(targetOffset) : null,
            farTargetMessageIndex: FAR_TARGET_MESSAGE_INDEX,
            farTargetMessageRequestedOffsetFromViewportTop: TARGET_MESSAGE_OFFSET,
            farTargetMessageActualOffsetFromViewportTop:
              typeof farTargetOffset === 'number' ? Math.round(farTargetOffset) : null,
            targetScrollOffsetY: TARGET_SCROLL_OFFSET,
            offsetY: metrics ? Math.round(metrics.offsetY) : null,
            viewportHeight: metrics ? Math.round(metrics.viewportHeight) : null,
            contentHeight: metrics ? Math.round(metrics.contentHeight) : null,
            maxOffsetY: maxOffsetY == null ? null : Math.round(maxOffsetY),
            bottomGapPx:
              metrics && maxOffsetY != null
                ? Math.round(Math.max(0, maxOffsetY - metrics.offsetY))
                : null,
            bottomContentRevision,
            geometryPulseHeight,
            feedbackPulseCount: feedbackPulseCountRef.current,
            diagnosticEventCounts: diagnosticEventCountsRef.current,
            contentFollowCorrectionCount: contentFollowCorrectionCountRef.current,
            contentFollowTerminalCount: contentFollowTerminalCountRef.current,
            navigationCorrectionCount: navigationCorrectionCountRef.current,
            navigationTerminalCount: navigationTerminalCountRef.current,
            effectiveScrollConfiguration: effectiveScrollConfigurationRef.current,
            listAnchorStartedDetails: listAnchorStartedDetailsRef.current,
            savedAnchor: describeAnchor(savedAnchorRef.current),
            cachedAnchor: describeAnchor(cachedScrollAnchorRef.current),
            visibleAnchor: visibleAnchor
              ? {
                  key: visibleAnchor.key ?? null,
                  sourceIndex: visibleAnchor.sourceIndex ?? null,
                  offsetFromViewportTop:
                    typeof visibleAnchor.offsetFromViewportTop === 'number'
                      ? Math.round(visibleAnchor.offsetFromViewportTop)
                      : null,
                }
              : null,
            diagnostics: diagnosticsRef.current,
            ...extra,
          });
        })
        .catch(() => {
          DesktopWindowManager?.recordProgressiveScrollHarnessState?.({
            command,
            runId: scrollHarnessRunId,
            status: 'state error',
            implementation,
            backingList,
          });
        });
    },
    [
      backingList,
      bottomContentRevision,
      geometryPulseHeight,
      implementation,
      scrollHarnessRunId,
      status,
      transcriptScroll.listRef,
    ],
  );

  const applyAnchorAndRestore = useCallback(
    (anchor: unknown, reason: string) => {
      pendingResetReasonRef.current = restoreReadyRef.current ? reason : null;
      cachedScrollAnchorRef.current = anchor;
      restoreReadyRef.current = true;
      setCachedScrollAnchor(anchor);
      setRestoreReady(true);
      setRestoreVersion((current) => current + 1);
    },
    [],
  );

  const persistAndRecord = useCallback(
    (command: string, statusText: string, delayMs = 300) => {
      transcriptScroll.requestPersist(command, { force: true, immediate: true });
      setTimeout(() => {
        waitForListSettled(() => recordHarnessState(command, statusText));
      }, delayMs);
    },
    [recordHarnessState, transcriptScroll, waitForListSettled],
  );

  const waitForNavigationSettled = useCallback(
    (callback: () => void, timeoutMs = HARNESS_NAVIGATION_MAX_MS + 1500) => {
      const startedAt = Date.now();
      const poll = () => {
        const settled = diagnosticsRef.current.some((entry) => {
          if (
            entry.event !== 'operationCompleted' &&
            entry.event !== 'operationExpired' &&
            entry.event !== 'operationCorrectionLimit' &&
            entry.event !== 'operationUnavailable' &&
            entry.event !== 'operationCancelled'
          ) {
            return false;
          }
          const details = entry.details;
          return (
            details != null &&
            typeof details === 'object' &&
            (details as Record<string, unknown>).purpose === 'navigation'
          );
        });
        if (settled || Date.now() - startedAt >= timeoutMs) {
          callback();
          return;
        }
        setTimeout(poll, 80);
      };
      setTimeout(poll, 80);
    },
    [],
  );

  const executeCommand = useCallback(
    (command: string) => {
      setStatus(`command ${command}`);
      recordDiagnostic({ event: 'command', command });

      if (command === 'read') {
        recordHarnessState(command, 'command read');
        return;
      }

      if (command === 'navigationSeparation') {
        resetDiagnostics();
        feedbackPulseEnabledRef.current = false;
        feedbackPulseCountRef.current = 0;
        setGeometryPulseHeight(0);
        transcriptScroll.scrollToBottom(false);
        waitForNavigationSettled(() => {
          // This is an intentionally geometry-only change. It must not create
          // or renew a semantic content-follow lease.
          setGeometryPulseHeight(120);
          setTimeout(() => {
            recordHarnessState(command, 'command navigationSeparation');
          }, HARNESS_CONTENT_FOLLOW_LEASE_MS + 500);
        });
        return;
      }

      if (command === 'longDistanceBottom') {
        resetDiagnostics();
        feedbackPulseEnabledRef.current = false;
        feedbackPulseCountRef.current = 0;
        const allMessages = buildMessages();
        setMessages(allMessages.slice(0, 20));
        setTimeout(() => {
          resetDiagnostics();
          transcriptScroll.scrollToBottom(false);
          let nextCount = 40;
          const growTranscript = () => {
            setMessages(allMessages.slice(0, nextCount));
            if (nextCount < allMessages.length) {
              nextCount = Math.min(allMessages.length, nextCount + 20);
              setTimeout(growTranscript, 80);
            }
          };
          setTimeout(growTranscript, 40);
          waitForNavigationSettled(() => {
            recordHarnessState(command, 'command longDistanceBottom');
          });
        }, 250);
        return;
      }

      if (command === 'farMessageAnchor') {
        resetDiagnostics();
        transcriptScroll.scrollToTop(false);
        waitForNavigationSettled(() => {
          resetDiagnostics();
          transcriptScroll.listRef.current?.scrollToItemAnchor?.({
            key: `msg-${FAR_TARGET_MESSAGE_INDEX}`,
            sourceIndex: FAR_TARGET_MESSAGE_INDEX,
            offsetFromViewportTop: TARGET_MESSAGE_OFFSET,
            beforeCount: 40,
            afterCount: 9,
            animated: false,
          });
          waitForListSettled(
            () => recordHarnessState(command, 'command farMessageAnchor'),
            HARNESS_ITEM_ANCHOR_TIMEOUT_MS + 1500,
          );
        });
        return;
      }

      if (command === 'semanticContentFollow') {
        resetDiagnostics();
        feedbackPulseEnabledRef.current = false;
        feedbackPulseCountRef.current = 0;
        setGeometryPulseHeight(0);
        transcriptScroll.scrollToBottom(false);
        waitForNavigationSettled(() => {
          setMessages((current) => [
            ...current,
            {
              index: current.length,
              message: {
                role: 'assistant',
                content:
                  'Semantic content-follow harness row. '.repeat(18),
              },
            },
          ]);
          setBottomContentRevision((current) => current + 1);
          setTimeout(() => {
            recordHarnessState(command, 'command semanticContentFollow');
          }, HARNESS_CONTENT_FOLLOW_LEASE_MS + 900);
        });
        return;
      }

      if (command === 'feedbackLoop') {
        resetDiagnostics();
        feedbackPulseEnabledRef.current = true;
        feedbackPulseCountRef.current = 0;
        setGeometryPulseHeight(0);
        transcriptScroll.scrollToBottom(false);
        waitForNavigationSettled(() => {
          setMessages((current) => [
            ...current,
            {
              index: current.length,
              message: {
                role: 'assistant',
                content:
                  'Feedback-loop harness row. '.repeat(24),
              },
            },
          ]);
          setBottomContentRevision((current) => current + 1);
          setTimeout(() => {
            feedbackPulseEnabledRef.current = false;
            recordHarnessState(command, 'command feedbackLoop');
          }, HARNESS_CONTENT_FOLLOW_LEASE_MS + 1200);
        });
        return;
      }

      if (command === 'offsetRoundTrip') {
        scrollToOffset(transcriptScroll.listRef.current, TARGET_SCROLL_OFFSET);
        setTimeout(() => {
          transcriptScroll.requestPersist('offsetRoundTripSave', {
            force: true,
            immediate: true,
          });
          setTimeout(() => {
            const saved = savedAnchorRef.current;
            scrollToOffset(transcriptScroll.listRef.current, 0);
            setTimeout(() => {
              applyAnchorAndRestore(saved, 'offsetRoundTripRestore');
              setTimeout(() => {
                waitForListSettled(() =>
                  recordHarnessState(command, 'command offsetRoundTrip'),
                );
              }, 400);
            }, 180);
          }, 350);
        }, 250);
        return;
      }

      if (command === 'messageAnchorSave') {
        transcriptScroll.listRef.current?.scrollToItemAnchor?.({
          key: `msg-${TARGET_MESSAGE_INDEX}`,
          sourceIndex: TARGET_MESSAGE_INDEX,
          offsetFromViewportTop: TARGET_MESSAGE_OFFSET,
          beforeCount: 40,
          afterCount: 59,
          animated: false,
        });
        waitForListSettled(() => persistAndRecord(command, 'command messageAnchorSave'));
        return;
      }

      if (command === 'messageAnchorRestore') {
        applyAnchorAndRestore(
          createChatMessageViewportScrollAnchor({
            messageIndex: TARGET_MESSAGE_INDEX,
            offsetFromViewportTop: TARGET_MESSAGE_OFFSET,
            pinnedToBottom: false,
          }),
          'messageAnchorRestore',
        );
        setTimeout(() => {
          waitForListSettled(() => recordHarnessState(command, 'command messageAnchorRestore'));
        }, 500);
        return;
      }

      if (command === 'messageAnchorRoundTrip') {
        transcriptScroll.listRef.current?.scrollToItemAnchor?.({
          key: `msg-${TARGET_MESSAGE_INDEX}`,
          sourceIndex: TARGET_MESSAGE_INDEX,
          offsetFromViewportTop: TARGET_MESSAGE_OFFSET,
          beforeCount: 40,
          afterCount: 59,
          animated: false,
        });
        waitForListSettled(() => {
          transcriptScroll.requestPersist('messageAnchorRoundTripSave', {
            force: true,
            immediate: true,
          });
          setTimeout(() => {
            const saved = savedAnchorRef.current;
            scrollToOffset(transcriptScroll.listRef.current, 0);
            setTimeout(() => {
              applyAnchorAndRestore(saved, 'messageAnchorRoundTripRestore');
              setTimeout(() => {
                waitForListSettled(() =>
                  recordHarnessState(command, 'command messageAnchorRoundTrip'),
                );
              }, 500);
            }, 180);
          }, 350);
        });
        return;
      }

      if (command === 'releaseDelayedMessageAnchor') {
        applyAnchorAndRestore(
          createChatMessageViewportScrollAnchor({
            messageIndex: TARGET_MESSAGE_INDEX,
            offsetFromViewportTop: TARGET_MESSAGE_OFFSET,
            pinnedToBottom: false,
          }),
          'releaseDelayedMessageAnchor',
        );
        setTimeout(() => {
          waitForListSettled(() =>
            recordHarnessState(command, 'command releaseDelayedMessageAnchor'),
          );
        }, 500);
        return;
      }

      if (command === 'releaseDelayedOffsetAnchor') {
        applyAnchorAndRestore(
          createChatScrollAnchor({
            bottomGapPx: 240,
            pinnedToBottom: false,
          }),
          'releaseDelayedOffsetAnchor',
        );
        setTimeout(() => {
          waitForListSettled(() =>
            recordHarnessState(command, 'command releaseDelayedOffsetAnchor', {
              requestedBottomGapPx: 240,
            }),
          );
        }, 500);
        return;
      }

      if (command === 'restoreOffsetAnchor') {
        const anchor = createChatScrollAnchor({
          bottomGapPx: 240,
          pinnedToBottom: false,
        });
        applyAnchorAndRestore(anchor, 'restoreOffsetAnchor');
        setTimeout(() => {
          waitForListSettled(() => recordHarnessState(command, 'command restoreOffsetAnchor'));
        }, 400);
      }
    },
    [
      applyAnchorAndRestore,
      persistAndRecord,
      recordDiagnostic,
      recordHarnessState,
      resetDiagnostics,
      transcriptScroll,
      waitForListSettled,
      waitForNavigationSettled,
    ],
  );

  const handleContentSizeChange = useCallback(
    (width: number, height: number) => {
      transcriptScroll.onContentSizeChange(width, height);
      if (!feedbackPulseEnabledRef.current || feedbackPulseCountRef.current >= 6) {
        return;
      }
      feedbackPulseCountRef.current += 1;
      const nextHeight = feedbackPulseCountRef.current % 2 === 0 ? 24 : 96;
      setTimeout(() => {
        if (feedbackPulseEnabledRef.current) {
          setGeometryPulseHeight(nextHeight);
        }
      }, 40);
    },
    [transcriptScroll],
  );

  useEffect(() => {
    const subscription = desktopWindowEvents?.addListener(
      'progressiveScrollHarnessCommand',
      (event: { command?: string; postedAtMs?: unknown; runId?: unknown }) => {
        const command = event?.command;
        if (typeof command !== 'string') {
          return;
        }
        if (typeof event?.runId === 'string' && event.runId !== scrollHarnessRunId) {
          return;
        }
        const commandKey = `${command}:${String(event?.postedAtMs ?? '')}`;
        if (lastCommandKeyRef.current === commandKey) {
          return;
        }
        lastCommandKeyRef.current = commandKey;
        executeCommand(command);
      },
    );
    const interval = setInterval(() => {
      DesktopWindowManager?.readProgressiveScrollHarnessCommand?.()
        .then((payload) => {
          const command = payload?.command;
          const postedAtMs = payload?.postedAtMs;
          if (typeof command !== 'string') {
            return;
          }
          if (
            typeof payload?.runId === 'string' &&
            payload.runId !== scrollHarnessRunId
          ) {
            return;
          }
          const commandKey = `${command}:${String(postedAtMs ?? '')}`;
          if (lastCommandKeyRef.current === commandKey) {
            return;
          }
          lastCommandKeyRef.current = commandKey;
          executeCommand(command);
        })
        .catch(() => {});
    }, 250);
    return () => {
      subscription?.remove();
      clearInterval(interval);
    };
  }, [executeCommand, scrollHarnessRunId]);

  const renderItem = useCallback(
    ({ item }: { item: HarnessMessage; index: number }) => (
      <View
        testID={`transcript-scroll-message-${item.index}`}
        accessible
        accessibilityLabel={`Message ${item.index}`}
        style={styles.row}
      >
        <Text style={styles.rowTitle}>Message {item.index}</Text>
        <Text style={styles.rowDetail}>{String(item.message.content ?? '')}</Text>
      </View>
    ),
    [],
  );

  const listProps = {
    testID: 'transcript-scroll-persistence-list',
    listRef: transcriptScroll.listRef,
    style: styles.list,
    contentContainerStyle: styles.listContent,
    data: messages,
    keyExtractor: (item: HarnessMessage) => `msg-${item.index}`,
    scrollEventThrottle: 16,
    onLayout: transcriptScroll.onLayout,
    onContentSizeChange: handleContentSizeChange,
    onScroll: transcriptScroll.onScroll,
    onScrollBeginDrag: transcriptScroll.onScrollBeginDrag,
    onScrollEndDrag: transcriptScroll.onScrollEndDrag,
    onMomentumScrollBegin: transcriptScroll.onMomentumScrollBegin,
    onMomentumScrollEnd: transcriptScroll.onMomentumScrollEnd,
    itemAnchorTimeoutMs: HARNESS_ITEM_ANCHOR_TIMEOUT_MS,
    itemAnchorMaxAttempts: HARNESS_ITEM_ANCHOR_MAX_ATTEMPTS,
    onScrollActionDiagnostic: transcriptScroll.onListScrollDiagnostic,
    renderItem,
    ListFooterComponent:
      geometryPulseHeight > 0 ? (
        <View
          testID="transcript-scroll-geometry-pulse"
          style={{ height: geometryPulseHeight }}
        />
      ) : null,
  };

  return (
    <View style={styles.root}>
      <View style={styles.toolbar}>
        <Text style={styles.title}>Transcript Scroll Persistence Harness</Text>
        <Pressable style={styles.button} onPress={() => executeCommand('read')}>
          <Text style={styles.buttonText}>Read</Text>
        </Pressable>
      </View>
      <Text style={styles.status}>
        {status} | {implementation}
        {implementation === 'progressiveScroll' ? `/${backingList}` : ''}
      </Text>
      {implementation === 'flatList' ? (
        <DependencyFlatList {...listProps} inverted />
      ) : implementation === 'progressiveScroll' ? (
        <ProgressiveScrollList
          {...listProps}
          initialWindowSize={50}
          pageSize={50}
          maxWindowSize={100}
          prebuildRows
          autoLoadEdges={false}
          backingList={backingList}
          defaultAnchorBeforeCount={40}
          defaultAnchorAfterCount={59}
          edgeScrollEpsilonPx={20}
        />
      ) : (
        <PlaceholderFlatList {...listProps} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  toolbar: {
    minHeight: 48,
    paddingHorizontal: 12,
    gap: 8,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#D9D9D9',
  },
  title: {
    flex: 1,
    fontSize: 15,
    fontWeight: '700',
    color: '#1F1F1F',
  },
  button: {
    minHeight: 30,
    paddingHorizontal: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#C8C8C8',
    justifyContent: 'center',
    backgroundColor: '#F5F5F5',
  },
  buttonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#333333',
  },
  status: {
    minHeight: 24,
    paddingHorizontal: 12,
    paddingVertical: 4,
    fontSize: 12,
    color: '#555555',
    borderBottomWidth: 1,
    borderBottomColor: '#ECECEC',
  },
  list: {
    maxHeight: 460,
    minHeight: 460,
  },
  listContent: {
    padding: 12,
    gap: 8,
  },
  row: {
    padding: 12,
    borderWidth: 1,
    borderColor: '#D6D6D6',
    backgroundColor: '#FAFAFA',
  },
  rowTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1F1F1F',
    marginBottom: 4,
  },
  rowDetail: {
    fontSize: 12,
    lineHeight: 17,
    color: '#333333',
  },
});