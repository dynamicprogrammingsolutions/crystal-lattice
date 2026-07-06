import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
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

export function useProactiveChatScrollPersistence(params: {
  connectionId: string;
  sessionId: string;
  cachedScrollAnchor: unknown;
  getMessagesForCache: () => IndexedMessage[];
  onUpdateCache: UpdateMessagesCache;
  enabled?: boolean;
  persistDebounceMs?: number;
  persistThrottleMs?: number;
}): {
  listRef: RefObject<any>;
  onScroll: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollEndDrag: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollEnd: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onLayout: (event: LayoutChangeEvent) => void;
  onContentSizeChange: (width: number, height: number) => void;
  requestPersist: (reason: string) => void;
  resetRestore: (reason: string) => void;
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
  } = params;

  const listRef = useRef<any>(null);
  const contentHeightRef = useRef<number | null>(null);
  const layoutHeightRef = useRef<number | null>(null);

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
    ((globalThis as any).CLC_DEBUG_FLATLIST_SCROLL !== false &&
      (globalThis as any).CLC_DEBUG_FLATLIST_SCROLL !== 'false');

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
    hasRestoredRef.current = true;
  }, [connectionId, debugEnabled, enabled, sessionId]);

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
      persistNow('unmount', { force: true }).catch(() => {});
    };
  }, [persistNow]);

  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? NaN);
      if (Number.isFinite(height)) {
        layoutHeightRef.current = height;
      }
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
    [connectionId, debugEnabled, getMessagesForCache, maybeRestoreScroll, sessionId],
  );

  const onContentSizeChange = useCallback(
    (_width: number, height: number) => {
      const resolved = Number(height ?? NaN);
      if (Number.isFinite(resolved)) {
        contentHeightRef.current = resolved;
      }
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
    [connectionId, debugEnabled, getMessagesForCache, maybeRestoreScroll, sessionId],
  );

  const onScroll = useCallback((event: NativeSyntheticEvent<NativeScrollEvent>) => {
    // Intentionally no-op. Scroll events are not reliably delivered on macOS
    // for this view. Persistence uses native pull-based metrics instead.
    logScrollDiagnostics('scroll', event);
  }, [logScrollDiagnostics]);

  const onScrollEndDrag = useCallback((event: NativeSyntheticEvent<NativeScrollEvent>) => {
    logScrollDiagnostics('scrollEndDrag', event);
    // If end-drag events are delivered, opportunistically persist.
    requestPersist('scrollEndDrag');
  }, [logScrollDiagnostics, requestPersist]);

  const onMomentumScrollEnd = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      logScrollDiagnostics('momentumScrollEnd', event);
      requestPersist('scrollMomentumEnd');
    },
    [logScrollDiagnostics, requestPersist],
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
    };
  }, [
    onContentSizeChange,
    onLayout,
    onMomentumScrollEnd,
    onScroll,
    onScrollEndDrag,
    requestPersist,
    resetRestore,
  ]);

  return result;
}
