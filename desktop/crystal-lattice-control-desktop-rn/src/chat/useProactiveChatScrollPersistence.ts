import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type RefObject,
} from 'react';
import type {
  LayoutChangeEvent,
  NativeScrollEvent,
  NativeSyntheticEvent,
} from 'react-native';

import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';

import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';
import {
  createChatMessageViewportScrollAnchor,
  createChatScrollAnchor,
  isChatMessageViewportScrollAnchor,
  isChatScrollAnchor,
  PINNED_TO_BOTTOM_THRESHOLD_PX,
  type ChatMessageViewportScrollAnchor,
  type ChatScrollAnchor,
} from './chatScroll';

type UpdateMessagesCache = (params: {
  connectionId: string;
  sessionId: string;
  messages: IndexedMessage[];
  scrollAnchor?: unknown;
}) => void;

type ScrollEdge = 'top' | 'bottom';

type ActiveEdgeScroll = {
  edge: ScrollEdge;
  runAttempt: (reason: string) => void;
};

function scrollToOffsetY(
  target: any,
  offsetY: number,
  context?: {
    debugEnabled?: boolean;
    reason?: string;
    connectionId?: string;
    sessionId?: string;
  },
) {
  if (!target) {
    return;
  }
  const resolved = Math.max(0, Math.round(offsetY));
  if (context?.debugEnabled) {
    console.log('[scrollPersist] scrollToOffsetY', {
      connectionId: context.connectionId,
      sessionId: context.sessionId,
      reason: context.reason,
      requestedOffsetY: offsetY,
      resolvedOffsetY: resolved,
      hasScrollToOffset: typeof target.scrollToOffset === 'function',
      hasScrollTo: typeof target.scrollTo === 'function',
      hasScrollToEnd: typeof target.scrollToEnd === 'function',
    });
  }
  if (typeof target.scrollToOffset === 'function') {
    target.scrollToOffset({ offset: resolved, animated: false });
    return;
  }
  if (typeof target.scrollTo === 'function') {
    target.scrollTo({ y: resolved, animated: false });
    return;
  }
  if (typeof target.scrollToEnd === 'function') {
    target.scrollToEnd({ animated: false });
  }
}

function readScrollMetricsFromEvent(event: NativeSyntheticEvent<NativeScrollEvent>): {
  offsetY: number | null;
  contentHeight: number | null;
  viewportHeight: number | null;
} {
  const nativeEvent = event.nativeEvent;
  const offsetY = Number(nativeEvent?.contentOffset?.y ?? NaN);
  const contentHeight = Number(nativeEvent?.contentSize?.height ?? NaN);
  const viewportHeight = Number(nativeEvent?.layoutMeasurement?.height ?? NaN);
  return {
    offsetY: Number.isFinite(offsetY) ? offsetY : null,
    contentHeight: Number.isFinite(contentHeight) ? contentHeight : null,
    viewportHeight: Number.isFinite(viewportHeight) ? viewportHeight : null,
  };
}

export function useProactiveChatScrollPersistence(params: {
  connectionId: string;
  sessionId: string;
  cachedScrollAnchor: unknown;
  getMessagesForCache: () => IndexedMessage[];
  onUpdateCache: UpdateMessagesCache;
  enabled?: boolean;
  persistDebounceMs?: number;
  persistThrottleMs?: number;
  bottomThresholdPx?: number;
  bottomConvergenceStableMs?: number;
  bottomConvergenceMaxMs?: number;
  bottomFollowWindowMs?: number;
  manualBottomFollowWindowMs?: number;
  initialBottomFollowWindowMs?: number;
  bottomLockEnabled?: boolean;
  messageAnchorBeforeCount?: number;
  messageAnchorAfterCount?: number;
  messageViewportAnchorsEnabled?: boolean;
  listEdgeMethodsEnabled?: boolean;
}): {
  listRef: RefObject<any>;
  onScroll: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollBeginDrag: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollEndDrag: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollEnd: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onLayout: (event: LayoutChangeEvent) => void;
  onContentSizeChange: (width: number, height: number) => void;
  requestPersist: (reason: string) => void;
  resetRestore: (reason: string) => void;
  scrollToTop: (animated?: boolean) => void;
  scrollToBottom: (animated?: boolean) => void;
  requestBottomFollow: (reason: string, options?: { windowMs?: number }) => void;
  canScrollToTop: boolean;
  canScrollToBottom: boolean;
  isNearBottom: boolean;
} {
  const {
    connectionId,
    sessionId,
    cachedScrollAnchor,
    getMessagesForCache,
    onUpdateCache,
    enabled = true,
    persistDebounceMs = 250,
    persistThrottleMs = 1000,
    bottomThresholdPx = PINNED_TO_BOTTOM_THRESHOLD_PX,
    bottomConvergenceStableMs = 200,
    bottomConvergenceMaxMs = 3000,
    bottomFollowWindowMs = 1000,
    manualBottomFollowWindowMs = 3000,
    initialBottomFollowWindowMs = 5000,
    bottomLockEnabled = false,
    messageAnchorBeforeCount = 40,
    messageAnchorAfterCount = 59,
    messageViewportAnchorsEnabled = false,
    listEdgeMethodsEnabled = false,
  } = params;

  const listRef = useRef<any>(null);
  const offsetYRef = useRef(0);
  const contentHeightRef = useRef<number | null>(null);
  const layoutHeightRef = useRef<number | null>(null);
  const isNearBottomRef = useRef(true);
  const pendingEdgeScrollFrameRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);
  const activeEdgeScrollRef = useRef<ActiveEdgeScroll | null>(null);
  const bottomFollowEnabledRef = useRef(false);
  const bottomFollowUntilMsRef = useRef(0);
  const programmaticScrollUntilRef = useRef(0);
  const scrollAffordanceStateRef = useRef({
    canScrollToTop: false,
    canScrollToBottom: false,
    isNearBottom: true,
  });
  const [scrollAffordanceState, setScrollAffordanceState] = useState({
    canScrollToTop: false,
    canScrollToBottom: false,
    isNearBottom: true,
  });

  const initialAnchorRef = useRef<ChatScrollAnchor | ChatMessageViewportScrollAnchor | null>(
    isChatScrollAnchor(cachedScrollAnchor)
      ? cachedScrollAnchor
      : messageViewportAnchorsEnabled && isChatMessageViewportScrollAnchor(cachedScrollAnchor)
        ? cachedScrollAnchor
        : null,
  );
  const hasRestoredRef = useRef(false);

  const persistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastPersistAtRef = useRef(0);
  const pendingReasonRef = useRef<string | null>(null);
  const lastScrollDiagnosticsAtRef = useRef(0);
  const lastNativeMetricsDiagnosticsAtRef = useRef(0);

  const debugEnabled =
    (globalThis as any).CLC_DEBUG_SCROLL_PERSIST === true ||
    (globalThis as any).CLC_DEBUG_SCROLL_PERSIST === 'true' ||
    (globalThis as any).CLC_DEBUG_FLATLIST_SCROLL === true ||
    (globalThis as any).CLC_DEBUG_FLATLIST_SCROLL === 'true';
  const bottomFollowDebugEnabled =
    debugEnabled ||
    (globalThis as any).CLC_DEBUG_FLATLIST_BOTTOM_FOLLOW === true ||
    (globalThis as any).CLC_DEBUG_FLATLIST_BOTTOM_FOLLOW === 'true';

  const logBottomFollow = useCallback(
    (event: string, details?: Record<string, unknown>) => {
      if (!bottomFollowDebugEnabled) {
        return;
      }
      const contentHeight = contentHeightRef.current;
      const layoutHeight = layoutHeightRef.current;
      const offsetY = offsetYRef.current;
      const maxOffsetY =
        contentHeight != null && layoutHeight != null
          ? Math.max(0, contentHeight - layoutHeight)
          : null;
      console.log('[flatListBottomFollow]', {
        connectionId,
        sessionId,
        event,
        offsetY,
        contentHeight,
        layoutHeight,
        maxOffsetY,
        bottomGapPx: maxOffsetY == null ? null : Math.max(0, maxOffsetY - offsetY),
        active: bottomFollowEnabledRef.current,
        untilMs: bottomFollowUntilMsRef.current,
        ...details,
      });
    },
    [bottomFollowDebugEnabled, connectionId, sessionId],
  );

  const updateDerivedScrollState = useCallback(() => {
    const contentHeight = contentHeightRef.current;
    const layoutHeight = layoutHeightRef.current;
    const offsetY = offsetYRef.current;
    const maxOffsetY =
      contentHeight != null && layoutHeight != null
        ? Math.max(0, contentHeight - layoutHeight)
        : 0;
    const bottomGapPx = Math.max(0, maxOffsetY - offsetY);
    const topGapPx = Math.max(0, offsetY);
    const threshold = Math.max(0, bottomThresholdPx);
    const isNearBottom = bottomGapPx <= threshold;
    isNearBottomRef.current = isNearBottom;

    const next = {
      canScrollToTop: topGapPx > threshold,
      canScrollToBottom: bottomGapPx > threshold,
      isNearBottom,
    };

    const current = scrollAffordanceStateRef.current;
    if (
      current.canScrollToTop === next.canScrollToTop &&
      current.canScrollToBottom === next.canScrollToBottom &&
      current.isNearBottom === next.isNearBottom
    ) {
      return;
    }
    scrollAffordanceStateRef.current = next;
    setScrollAffordanceState(next);
  }, [bottomThresholdPx]);

  const applyEventMetrics = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const metrics = readScrollMetricsFromEvent(event);
      if (metrics.offsetY != null) {
        offsetYRef.current = metrics.offsetY;
      }
      if (metrics.contentHeight != null) {
        contentHeightRef.current = metrics.contentHeight;
      }
      if (metrics.viewportHeight != null) {
        layoutHeightRef.current = metrics.viewportHeight;
      }
      updateDerivedScrollState();
    },
    [updateDerivedScrollState],
  );

  const cancelActiveEdgeScroll = useCallback(() => {
    if (pendingEdgeScrollFrameRef.current != null) {
      cancelAnimationFrame(pendingEdgeScrollFrameRef.current);
      pendingEdgeScrollFrameRef.current = null;
    }
    activeEdgeScrollRef.current = null;
  }, []);

  const scrollToEdge = useCallback(
    (
      edge: ScrollEdge,
      animated = true,
      options?: {
        followWindowMs?: number;
      },
    ) => {
      const target = listRef.current;
      if (!target) {
        return;
      }
      cancelActiveEdgeScroll();
      const now = Date.now();
      const followWindowMs = Math.max(0, Math.round(options?.followWindowMs ?? 0));

      if (listEdgeMethodsEnabled && edge === 'top' && typeof target.scrollToTop === 'function') {
        bottomFollowEnabledRef.current = false;
        bottomFollowUntilMsRef.current = 0;
        target.scrollToTop({ animated });
        programmaticScrollUntilRef.current = Date.now() + 250;
        return;
      }
      if (
        listEdgeMethodsEnabled &&
        edge === 'bottom' &&
        typeof target.scrollToBottom === 'function'
      ) {
        bottomFollowEnabledRef.current = true;
        bottomFollowUntilMsRef.current = followWindowMs > 0 ? now + followWindowMs : 0;
        target.scrollToBottom({ animated });
        programmaticScrollUntilRef.current = Date.now() + 250;
        return;
      }

      const scrollOnce = (nextAnimated: boolean) => {
        const contentHeight = contentHeightRef.current;
        const layoutHeight = layoutHeightRef.current;
        const maxOffsetY =
          contentHeight != null && layoutHeight != null
            ? Math.max(0, contentHeight - layoutHeight)
            : 0;
        const targetOffsetY = edge === 'bottom' ? maxOffsetY : 0;

        if (typeof target.scrollToOffset === 'function') {
          target.scrollToOffset({ offset: targetOffsetY, animated: nextAnimated });
        } else if (typeof target.scrollTo === 'function') {
          target.scrollTo({ y: targetOffsetY, animated: nextAnimated });
        } else if (edge === 'bottom' && typeof target.scrollToEnd === 'function') {
          target.scrollToEnd({ animated: nextAnimated });
        }

        programmaticScrollUntilRef.current = Date.now() + 250;
        offsetYRef.current = targetOffsetY;
        updateDerivedScrollState();
      };

      scrollOnce(animated);

      const threshold = Math.max(0, bottomThresholdPx);
      const stableMs = Math.max(0, Math.round(bottomConvergenceStableMs));
      const maxMs = Math.max(
        stableMs + 1,
        Math.round(bottomConvergenceMaxMs),
        followWindowMs,
      );
      const startedAt = Date.now();
      let stableSince: number | null = null;
      let stableTargetOffsetY: number | null = null;

      if (edge === 'bottom') {
        bottomFollowEnabledRef.current = true;
        bottomFollowUntilMsRef.current = followWindowMs > 0 ? startedAt + followWindowMs : 0;
      } else {
        bottomFollowEnabledRef.current = false;
        bottomFollowUntilMsRef.current = 0;
      }

      const stopActiveScroll = () => {
        if (activeEdgeScrollRef.current?.runAttempt === runAttempt) {
          activeEdgeScrollRef.current = null;
        }
      };

      const scheduleAttempt = () => {
        if (pendingEdgeScrollFrameRef.current != null) {
          return;
        }
        pendingEdgeScrollFrameRef.current = requestAnimationFrame(() => {
          pendingEdgeScrollFrameRef.current = null;
          runAttempt('frame');
        });
      };

      const runAttempt = (_reason: string) => {
        pendingEdgeScrollFrameRef.current = null;
        getMacScrollViewMetrics(listRef.current)
          .then((metrics) => {
            if (!metrics) {
              stopActiveScroll();
              return;
            }
            const now = Date.now();
            if (
              edge === 'bottom' &&
              bottomFollowUntilMsRef.current > 0 &&
              now > bottomFollowUntilMsRef.current
            ) {
              bottomFollowEnabledRef.current = false;
              bottomFollowUntilMsRef.current = 0;
              logBottomFollow('stopExpired', { reason: _reason });
              stopActiveScroll();
              return;
            }
            offsetYRef.current = metrics.offsetY;
            contentHeightRef.current = metrics.contentHeight;
            layoutHeightRef.current = metrics.viewportHeight;
            updateDerivedScrollState();

            const maxY = Math.max(0, metrics.contentHeight - metrics.viewportHeight);
            const edgeGapPx =
              edge === 'bottom'
                ? Math.max(0, maxY - metrics.offsetY)
                : Math.max(0, metrics.offsetY);
            if (edgeGapPx <= threshold) {
              const targetOffsetY = edge === 'bottom' ? maxY : 0;
              if (
                stableSince == null ||
                stableTargetOffsetY == null ||
                Math.abs(stableTargetOffsetY - targetOffsetY) > threshold
              ) {
                stableSince = now;
                stableTargetOffsetY = targetOffsetY;
                scheduleAttempt();
                return;
              }
              if (now - stableSince >= stableMs) {
                stopActiveScroll();
                return;
              }
              scheduleAttempt();
              return;
            }

            stableSince = null;
            stableTargetOffsetY = null;
            if (now - startedAt >= maxMs) {
              stopActiveScroll();
              return;
            }
            scrollOnce(false);
            scheduleAttempt();
          })
          .catch(() => {});
      };

      activeEdgeScrollRef.current = { edge, runAttempt };
      scheduleAttempt();
    },
    [
      bottomConvergenceMaxMs,
      bottomConvergenceStableMs,
      bottomThresholdPx,
      cancelActiveEdgeScroll,
      listEdgeMethodsEnabled,
      logBottomFollow,
      updateDerivedScrollState,
    ],
  );

  const scrollToTop = useCallback(
    (animated = true) => {
      scrollToEdge('top', animated);
    },
    [scrollToEdge],
  );

  const scrollToBottom = useCallback(
    (animated = true) => {
      scrollToEdge('bottom', animated, { followWindowMs: manualBottomFollowWindowMs });
    },
    [manualBottomFollowWindowMs, scrollToEdge],
  );

  const continueActiveEdgeScroll = useCallback(
    (reason: string) => {
      const now = Date.now();
      const active = activeEdgeScrollRef.current;
      if (!active) {
        if (bottomFollowEnabledRef.current && bottomFollowUntilMsRef.current > 0) {
          const remainingMs = bottomFollowUntilMsRef.current - now;
          if (remainingMs > 0) {
            logBottomFollow('restartWithinWindow', { reason, remainingMs });
            scrollToEdge('bottom', false, { followWindowMs: remainingMs });
            return;
          }
          bottomFollowEnabledRef.current = false;
          bottomFollowUntilMsRef.current = 0;
          logBottomFollow('continueExpired', { reason });
        }
        return;
      }
      if (
        active.edge === 'bottom' &&
        bottomFollowUntilMsRef.current > 0 &&
        now > bottomFollowUntilMsRef.current
      ) {
        bottomFollowEnabledRef.current = false;
        bottomFollowUntilMsRef.current = 0;
        logBottomFollow('continueExpired', { reason });
        cancelActiveEdgeScroll();
        return;
      }
      active.runAttempt(reason);
    },
    [cancelActiveEdgeScroll, logBottomFollow, scrollToEdge],
  );

  const requestBottomFollow = useCallback(
    (reason: string, options?: { windowMs?: number }) => {
      if (!bottomLockEnabled || !enabled || !hasRestoredRef.current) {
        logBottomFollow('ignoredDisabled', { reason });
        return;
      }
      if (!isNearBottomRef.current) {
        logBottomFollow('ignoredNotNearBottom', { reason });
        return;
      }
      const windowMs = Math.max(
        0,
        Math.round(options?.windowMs ?? bottomFollowWindowMs),
      );
      if (windowMs <= 0) {
        return;
      }
      bottomFollowEnabledRef.current = true;
      bottomFollowUntilMsRef.current = Date.now() + windowMs;
      logBottomFollow('start', { reason, windowMs });
      scrollToEdge('bottom', false, { followWindowMs: windowMs });
    },
    [bottomFollowWindowMs, bottomLockEnabled, enabled, logBottomFollow, scrollToEdge],
  );

  const handlePossibleManualScroll = useCallback(() => {
    if (Date.now() <= programmaticScrollUntilRef.current) {
      return;
    }
    if (activeEdgeScrollRef.current) {
      cancelActiveEdgeScroll();
    }
    if (!isNearBottomRef.current) {
      logBottomFollow('stopManualScroll');
    }
    bottomFollowEnabledRef.current = false;
    bottomFollowUntilMsRef.current = 0;
  }, [cancelActiveEdgeScroll, logBottomFollow]);

  const logScrollDiagnostics = useCallback(
    (kind: string, event?: NativeSyntheticEvent<NativeScrollEvent>) => {
      if (!debugEnabled) {
        return;
      }
      const now = Date.now();
      if (now - lastScrollDiagnosticsAtRef.current < 250) {
        return;
      }
      lastScrollDiagnosticsAtRef.current = now;

      const nativeEvent = event?.nativeEvent;
      const contentOffsetY = Number(nativeEvent?.contentOffset?.y ?? NaN);
      const eventContentHeight = Number(nativeEvent?.contentSize?.height ?? NaN);
      const eventViewportHeight = Number(nativeEvent?.layoutMeasurement?.height ?? NaN);
      const eventMaxOffsetY =
        Number.isFinite(eventContentHeight) && Number.isFinite(eventViewportHeight)
          ? Math.max(0, eventContentHeight - eventViewportHeight)
          : null;

      console.log('[flatListScroll] event', {
        connectionId,
        sessionId,
        kind,
        messageCount: getMessagesForCache().length,
        contentOffsetY: Number.isFinite(contentOffsetY) ? contentOffsetY : null,
        eventContentHeight: Number.isFinite(eventContentHeight) ? eventContentHeight : null,
        eventViewportHeight: Number.isFinite(eventViewportHeight) ? eventViewportHeight : null,
        eventMaxOffsetY,
        cachedContentHeight: contentHeightRef.current,
        cachedLayoutHeight: layoutHeightRef.current,
      });

      if (now - lastNativeMetricsDiagnosticsAtRef.current < 1000) {
        return;
      }
      lastNativeMetricsDiagnosticsAtRef.current = now;
      getMacScrollViewMetrics(listRef.current)
        .then((metrics) => {
          if (!metrics) {
            console.log('[flatListScroll] nativeMetrics(skip:noMetrics)', {
              connectionId,
              sessionId,
              kind,
            });
            return;
          }
          console.log('[flatListScroll] nativeMetrics', {
            connectionId,
            sessionId,
            kind,
            messageCount: getMessagesForCache().length,
            metrics,
            nativeMaxOffsetY: Math.max(0, metrics.contentHeight - metrics.viewportHeight),
            nativeBottomGapPx: Math.max(
              0,
              metrics.contentHeight - metrics.viewportHeight - metrics.offsetY,
            ),
          });
        })
        .catch(() => {});
    },
    [connectionId, debugEnabled, getMessagesForCache, sessionId],
  );

  const maybeRestoreScroll = useCallback(() => {
    if (!enabled) {
      return;
    }
    if (hasRestoredRef.current) {
      return;
    }
    const contentHeight = contentHeightRef.current;
    const layoutHeight = layoutHeightRef.current;
    if (contentHeight == null || layoutHeight == null) {
      return;
    }
    if (!Number.isFinite(contentHeight) || !Number.isFinite(layoutHeight) || layoutHeight <= 0) {
      return;
    }

    const anchor = initialAnchorRef.current;
    if (!anchor) {
      logBottomFollow('initialNoAnchorBottom', {
        windowMs: initialBottomFollowWindowMs,
      });
      scrollToEdge('bottom', false, {
        followWindowMs: initialBottomFollowWindowMs,
      });
      hasRestoredRef.current = true;
      return;
    }

    const target = listRef.current;
    if (!target) {
      return;
    }

    if (messageViewportAnchorsEnabled && isChatMessageViewportScrollAnchor(anchor)) {
      if (anchor.pinnedToBottom && typeof target.scrollToEnd === 'function') {
        target.scrollToEnd({ animated: false });
        hasRestoredRef.current = true;
        return;
      }
      if (typeof target.scrollToItemAnchor === 'function') {
        target.scrollToItemAnchor({
          key: `msg-${anchor.messageIndex}`,
          offsetFromViewportTop: anchor.offsetFromViewportTop,
          beforeCount: messageAnchorBeforeCount,
          afterCount: messageAnchorAfterCount,
          animated: false,
        });
        hasRestoredRef.current = true;
        return;
      }
      hasRestoredRef.current = true;
      return;
    }

    const maxOffsetY = Math.max(0, contentHeight - layoutHeight);
    const targetOffsetY = anchor.pinnedToBottom
      ? maxOffsetY
      : Math.max(0, maxOffsetY - anchor.bottomGapPx);

    if (debugEnabled) {
      console.log('[scrollPersist] restore(pull)', {
        connectionId,
        sessionId,
        contentHeight,
        layoutHeight,
        maxOffsetY,
        anchor,
        targetOffsetY,
      });
    }

    scrollToOffsetY(target, targetOffsetY, {
      debugEnabled,
      reason: 'restore',
      connectionId,
      sessionId,
    });
    offsetYRef.current = targetOffsetY;
    updateDerivedScrollState();
    hasRestoredRef.current = true;
  }, [
    connectionId,
    debugEnabled,
    enabled,
    initialBottomFollowWindowMs,
    logBottomFollow,
    messageAnchorAfterCount,
    messageAnchorBeforeCount,
    messageViewportAnchorsEnabled,
    sessionId,
    scrollToEdge,
    updateDerivedScrollState,
  ]);

  const persistNow = useCallback(
    async (
      reason: string,
      options?: {
        force?: boolean;
      },
    ) => {
      if (!enabled) {
        return;
      }
      const now = Date.now();
      if (!options?.force && now - lastPersistAtRef.current < persistThrottleMs) {
        return;
      }
      lastPersistAtRef.current = now;

      const metrics = await getMacScrollViewMetrics(listRef.current);
      if (!metrics) {
        if (debugEnabled) {
          console.log('[scrollPersist] persist(skip:noMetrics)', { connectionId, sessionId, reason });
        }
        return;
      }

      const maxOffsetY = Math.max(0, metrics.contentHeight - metrics.viewportHeight);
      const bottomGapPx = Math.max(0, maxOffsetY - metrics.offsetY);
      const pinnedToBottom = bottomGapPx <= bottomThresholdPx;
      let anchor: ChatScrollAnchor | ChatMessageViewportScrollAnchor =
        createChatScrollAnchor({ bottomGapPx, pinnedToBottom });

      if (messageViewportAnchorsEnabled) {
        const visibleAnchor =
          typeof (listRef.current as any)?.getVisibleAnchor === 'function'
            ? await (listRef.current as any).getVisibleAnchor()
            : null;
        const visibleKey =
          typeof visibleAnchor?.key === 'string' ? visibleAnchor.key : null;
        const match = visibleKey ? /^msg-(\-?\d+)$/.exec(visibleKey) : null;
        if (match) {
          const messageIndex = Number(match[1]);
          const offsetFromViewportTop = Number(visibleAnchor.offsetFromViewportTop ?? NaN);
          if (Number.isFinite(messageIndex) && Number.isFinite(offsetFromViewportTop)) {
            anchor = createChatMessageViewportScrollAnchor({
              messageIndex,
              offsetFromViewportTop,
              pinnedToBottom,
            });
          }
        }
      }

      if (debugEnabled) {
        console.log('[scrollPersist] persist(pull)', {
          connectionId,
          sessionId,
          reason,
          metrics,
          anchor,
        });
      }

      onUpdateCache({
        connectionId,
        sessionId,
        messages: getMessagesForCache(),
        scrollAnchor: anchor,
      });
    },
    [
      connectionId,
      debugEnabled,
      enabled,
      getMessagesForCache,
      bottomThresholdPx,
      messageViewportAnchorsEnabled,
      onUpdateCache,
      persistThrottleMs,
      sessionId,
    ],
  );

  const requestPersist = useCallback(
    (reason: string) => {
      if (!enabled) {
        return;
      }
      pendingReasonRef.current = reason;
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
      }
      persistTimerRef.current = setTimeout(() => {
        const nextReason = pendingReasonRef.current ?? 'unknown';
        pendingReasonRef.current = null;
        persistTimerRef.current = null;
        persistNow(nextReason).catch(() => {});
      }, persistDebounceMs);
    },
    [enabled, persistDebounceMs, persistNow],
  );

  const resetRestore = useCallback(
    (reason: string) => {
      if (debugEnabled) {
        console.log('[scrollPersist] restore(reset)', { connectionId, sessionId, reason });
      }
      hasRestoredRef.current = false;
      maybeRestoreScroll();
    },
    [connectionId, debugEnabled, maybeRestoreScroll, sessionId],
  );

  useEffect(() => {
    initialAnchorRef.current = isChatScrollAnchor(cachedScrollAnchor)
      ? cachedScrollAnchor
      : messageViewportAnchorsEnabled && isChatMessageViewportScrollAnchor(cachedScrollAnchor)
        ? cachedScrollAnchor
        : null;
    maybeRestoreScroll();
  }, [cachedScrollAnchor, maybeRestoreScroll, messageViewportAnchorsEnabled]);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    // On first mount, treat as "previously inactive" so cached scroll anchor
    // restores even if the tab starts active.
    resetRestore('mount');
  }, [enabled, resetRestore]);

  useEffect(() => {
    if (enabled) {
      return;
    }
    if (persistTimerRef.current) {
      clearTimeout(persistTimerRef.current);
      persistTimerRef.current = null;
    }
  }, [enabled]);

  useEffect(() => {
    return () => {
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
        persistTimerRef.current = null;
      }
      cancelActiveEdgeScroll();
      persistNow('unmount', { force: true }).catch(() => {});
    };
  }, [cancelActiveEdgeScroll, persistNow]);

  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? NaN);
      if (Number.isFinite(height)) {
        layoutHeightRef.current = height;
      }
      updateDerivedScrollState();
      continueActiveEdgeScroll('layout');
      if (debugEnabled) {
        console.log('[flatListScroll] layout', {
          connectionId,
          sessionId,
          height: Number.isFinite(height) ? height : null,
          messageCount: getMessagesForCache().length,
        });
      }
      maybeRestoreScroll();
    },
    [
      connectionId,
      continueActiveEdgeScroll,
      debugEnabled,
      getMessagesForCache,
      maybeRestoreScroll,
      sessionId,
      updateDerivedScrollState,
    ],
  );

  const onContentSizeChange = useCallback(
    (_width: number, height: number) => {
      const resolved = Number(height ?? NaN);
      if (Number.isFinite(resolved)) {
        contentHeightRef.current = resolved;
      }
      updateDerivedScrollState();
      continueActiveEdgeScroll('contentSizeChange');
      if (debugEnabled) {
        const layoutHeight = layoutHeightRef.current;
        console.log('[flatListScroll] contentSizeChange', {
          connectionId,
          sessionId,
          width: _width,
          height: Number.isFinite(resolved) ? resolved : null,
          layoutHeight,
          maxOffsetY:
            Number.isFinite(resolved) && layoutHeight != null
              ? Math.max(0, resolved - layoutHeight)
              : null,
          messageCount: getMessagesForCache().length,
        });
      }
      maybeRestoreScroll();
    },
    [
      connectionId,
      continueActiveEdgeScroll,
      debugEnabled,
      getMessagesForCache,
      maybeRestoreScroll,
      sessionId,
      updateDerivedScrollState,
    ],
  );

  const onScroll = useCallback((event: NativeSyntheticEvent<NativeScrollEvent>) => {
    // Persistence still uses native pull-based metrics, but scroll events are
    // useful for lightweight affordance state.
    applyEventMetrics(event);
    handlePossibleManualScroll();
    continueActiveEdgeScroll('scroll');
    logScrollDiagnostics('scroll', event);
  }, [
    applyEventMetrics,
    continueActiveEdgeScroll,
    handlePossibleManualScroll,
    logScrollDiagnostics,
  ]);

  const onScrollBeginDrag = useCallback((event: NativeSyntheticEvent<NativeScrollEvent>) => {
    applyEventMetrics(event);
    bottomFollowEnabledRef.current = false;
    bottomFollowUntilMsRef.current = 0;
    cancelActiveEdgeScroll();
    logBottomFollow('stopBeginDrag');
    logScrollDiagnostics('scrollBeginDrag', event);
	  }, [applyEventMetrics, cancelActiveEdgeScroll, logBottomFollow, logScrollDiagnostics]);

  const onScrollEndDrag = useCallback((event: NativeSyntheticEvent<NativeScrollEvent>) => {
    applyEventMetrics(event);
    continueActiveEdgeScroll('scrollEndDrag');
    logScrollDiagnostics('scrollEndDrag', event);
    // If end-drag events are delivered, opportunistically persist.
    requestPersist('scrollEndDrag');
  }, [applyEventMetrics, continueActiveEdgeScroll, logScrollDiagnostics, requestPersist]);

  const onMomentumScrollEnd = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      applyEventMetrics(event);
      continueActiveEdgeScroll('momentumScrollEnd');
      logScrollDiagnostics('momentumScrollEnd', event);
      requestPersist('scrollMomentumEnd');
    },
    [applyEventMetrics, continueActiveEdgeScroll, logScrollDiagnostics, requestPersist],
  );

  const result = useMemo(() => {
    return {
      listRef,
      onScroll,
      onScrollBeginDrag,
      onScrollEndDrag,
      onMomentumScrollEnd,
      onLayout,
      onContentSizeChange,
      requestPersist,
      resetRestore,
      scrollToTop,
      scrollToBottom,
      requestBottomFollow,
      canScrollToTop: scrollAffordanceState.canScrollToTop,
      canScrollToBottom: scrollAffordanceState.canScrollToBottom,
      isNearBottom: scrollAffordanceState.isNearBottom,
    };
  }, [
    scrollAffordanceState.canScrollToBottom,
    scrollAffordanceState.canScrollToTop,
    scrollAffordanceState.isNearBottom,
    onContentSizeChange,
    onLayout,
    onMomentumScrollEnd,
    onScroll,
    onScrollBeginDrag,
    onScrollEndDrag,
    requestPersist,
	    requestBottomFollow,
    resetRestore,
    scrollToBottom,
    scrollToTop,
  ]);

  return result;
}
