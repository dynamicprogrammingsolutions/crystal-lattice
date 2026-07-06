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
  createChatScrollAnchor,
  isChatScrollAnchor,
  PINNED_TO_BOTTOM_THRESHOLD_PX,
  type ChatScrollAnchor,
} from './chatScroll';

type UpdateMessagesCache = (params: {
  connectionId: string;
  sessionId: string;
  messages: IndexedMessage[];
  scrollAnchor?: unknown;
}) => void;

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
  stickToBottomEnabled?: boolean;
  stickToBottomThresholdPx?: number;
}): {
  listRef: RefObject<any>;
  onScroll: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollEndDrag: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollEnd: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onLayout: (event: LayoutChangeEvent) => void;
  onContentSizeChange: (width: number, height: number) => void;
  requestPersist: (reason: string) => void;
  resetRestore: (reason: string) => void;
  scrollToTop: (animated?: boolean) => void;
  scrollToBottom: (animated?: boolean) => void;
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
    stickToBottomEnabled = false,
    stickToBottomThresholdPx = PINNED_TO_BOTTOM_THRESHOLD_PX,
  } = params;

  const listRef = useRef<any>(null);
  const offsetYRef = useRef(0);
  const contentHeightRef = useRef<number | null>(null);
  const layoutHeightRef = useRef<number | null>(null);
  const isNearBottomRef = useRef(true);
  const pendingStickToBottomFrameRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);
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

  const initialAnchorRef = useRef<ChatScrollAnchor | null>(
    isChatScrollAnchor(cachedScrollAnchor) ? cachedScrollAnchor : null,
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

  const updateDerivedScrollState = useCallback(() => {
    const contentHeight = contentHeightRef.current;
    const layoutHeight = layoutHeightRef.current;
    const offsetY = offsetYRef.current;
    const maxOffsetY =
      contentHeight != null && layoutHeight != null
        ? Math.max(0, contentHeight - layoutHeight)
        : 0;
    const bottomGapPx = Math.max(0, maxOffsetY - offsetY);
    const threshold = Math.max(0, stickToBottomThresholdPx);
    const isNearBottom = bottomGapPx <= threshold;
    isNearBottomRef.current = isNearBottom;

    const next = {
      canScrollToTop: offsetY > threshold,
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
  }, [stickToBottomThresholdPx]);

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

  const scrollToTop = useCallback(
    (animated = true) => {
      const target = listRef.current;
      if (!target) {
        return;
      }
      if (typeof target.scrollToOffset === 'function') {
        target.scrollToOffset({ offset: 0, animated });
      } else if (typeof target.scrollTo === 'function') {
        target.scrollTo({ y: 0, animated });
      }
      offsetYRef.current = 0;
      updateDerivedScrollState();
    },
    [updateDerivedScrollState],
  );

  const scrollToBottom = useCallback(
    (animated = true) => {
      const target = listRef.current;
      if (!target) {
        return;
      }
      const contentHeight = contentHeightRef.current;
      const layoutHeight = layoutHeightRef.current;
      const maxOffsetY =
        contentHeight != null && layoutHeight != null
          ? Math.max(0, contentHeight - layoutHeight)
          : 0;
      if (typeof target.scrollToOffset === 'function') {
        target.scrollToOffset({ offset: maxOffsetY, animated });
      } else if (typeof target.scrollToEnd === 'function') {
        target.scrollToEnd({ animated });
      } else if (typeof target.scrollTo === 'function') {
        target.scrollTo({ y: maxOffsetY, animated });
      }
      offsetYRef.current = maxOffsetY;
      updateDerivedScrollState();
    },
    [updateDerivedScrollState],
  );

  const requestStickToBottom = useCallback(() => {
    if (!stickToBottomEnabled || !enabled || !hasRestoredRef.current) {
      return;
    }
    if (!isNearBottomRef.current) {
      return;
    }
    if (pendingStickToBottomFrameRef.current != null) {
      cancelAnimationFrame(pendingStickToBottomFrameRef.current);
    }
    pendingStickToBottomFrameRef.current = requestAnimationFrame(() => {
      pendingStickToBottomFrameRef.current = null;
      scrollToBottom(false);
    });
  }, [enabled, scrollToBottom, stickToBottomEnabled]);

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
      hasRestoredRef.current = true;
      return;
    }

    const target = listRef.current;
    if (!target) {
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
  }, [connectionId, debugEnabled, enabled, sessionId, updateDerivedScrollState]);

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

      const bottomGapPx = Math.max(0, metrics.contentHeight - metrics.viewportHeight - metrics.offsetY);
      const pinnedToBottom = bottomGapPx <= PINNED_TO_BOTTOM_THRESHOLD_PX;
      const anchor = createChatScrollAnchor({ bottomGapPx, pinnedToBottom });

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
    initialAnchorRef.current = isChatScrollAnchor(cachedScrollAnchor) ? cachedScrollAnchor : null;
    maybeRestoreScroll();
  }, [cachedScrollAnchor, maybeRestoreScroll]);

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
      if (pendingStickToBottomFrameRef.current != null) {
        cancelAnimationFrame(pendingStickToBottomFrameRef.current);
        pendingStickToBottomFrameRef.current = null;
      }
      persistNow('unmount', { force: true }).catch(() => {});
    };
  }, [persistNow]);

  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? NaN);
      if (Number.isFinite(height)) {
        layoutHeightRef.current = height;
      }
      updateDerivedScrollState();
      if (debugEnabled) {
        console.log('[flatListScroll] layout', {
          connectionId,
          sessionId,
          height: Number.isFinite(height) ? height : null,
          messageCount: getMessagesForCache().length,
        });
      }
      maybeRestoreScroll();
      requestStickToBottom();
    },
    [
      connectionId,
      debugEnabled,
      getMessagesForCache,
      maybeRestoreScroll,
      requestStickToBottom,
      sessionId,
      updateDerivedScrollState,
    ],
  );

  const onContentSizeChange = useCallback(
    (_width: number, height: number) => {
      const wasNearBottom = isNearBottomRef.current;
      const resolved = Number(height ?? NaN);
      if (Number.isFinite(resolved)) {
        contentHeightRef.current = resolved;
      }
      isNearBottomRef.current = wasNearBottom;
      updateDerivedScrollState();
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
      if (wasNearBottom) {
        isNearBottomRef.current = true;
        requestStickToBottom();
      }
    },
    [
      connectionId,
      debugEnabled,
      getMessagesForCache,
      maybeRestoreScroll,
      requestStickToBottom,
      sessionId,
      updateDerivedScrollState,
    ],
  );

  const onScroll = useCallback((event: NativeSyntheticEvent<NativeScrollEvent>) => {
    // Persistence still uses native pull-based metrics, but scroll events are
    // useful for lightweight affordance/sticky-bottom state.
    applyEventMetrics(event);
    logScrollDiagnostics('scroll', event);
  }, [applyEventMetrics, logScrollDiagnostics]);

  const onScrollEndDrag = useCallback((event: NativeSyntheticEvent<NativeScrollEvent>) => {
    applyEventMetrics(event);
    logScrollDiagnostics('scrollEndDrag', event);
    // If end-drag events are delivered, opportunistically persist.
    requestPersist('scrollEndDrag');
  }, [applyEventMetrics, logScrollDiagnostics, requestPersist]);

  const onMomentumScrollEnd = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      applyEventMetrics(event);
      logScrollDiagnostics('momentumScrollEnd', event);
      requestPersist('scrollMomentumEnd');
    },
    [applyEventMetrics, logScrollDiagnostics, requestPersist],
  );

  const result = useMemo(() => {
    return {
      listRef,
      onScroll,
      onScrollEndDrag,
      onMomentumScrollEnd,
      onLayout,
      onContentSizeChange,
      requestPersist,
      resetRestore,
      scrollToTop,
      scrollToBottom,
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
    onScrollEndDrag,
    requestPersist,
    resetRestore,
    scrollToBottom,
    scrollToTop,
  ]);

  return result;
}
