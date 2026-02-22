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

function scrollToOffsetY(target: any, offsetY: number) {
  if (!target) {
    return;
  }
  const resolved = Math.max(0, Math.round(offsetY));
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

export function usePersistedChatScrollAnchor(params: {
  connectionId: string;
  sessionId: string;
  cachedScrollAnchor: unknown;
  getMessagesForCache: () => IndexedMessage[];
  onUpdateCache: UpdateMessagesCache;
  debounceMs?: number;
  enabled?: boolean;
}): {
  listRef: RefObject<any>;
  onScroll: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollEndDrag: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollEnd: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onLayout: (event: LayoutChangeEvent) => void;
  onContentSizeChange: (width: number, height: number) => void;
} {
  const {
    connectionId,
    sessionId,
    cachedScrollAnchor,
    getMessagesForCache,
    onUpdateCache,
    debounceMs = 300,
    enabled = true,
  } = params;

  const listRef = useRef<any>(null);

  const contentHeightRef = useRef<number | null>(null);
  const layoutHeightRef = useRef<number | null>(null);

  const initialAnchorRef = useRef<ChatScrollAnchor | null>(
    isChatScrollAnchor(cachedScrollAnchor) ? cachedScrollAnchor : null,
  );
  const hasRestoredRef = useRef(false);

  const lastDebugAtRef = useRef(0);

  const debugEnabled =
    (globalThis as any).CLC_DEBUG_SCROLL_PERSIST === true ||
    (globalThis as any).CLC_DEBUG_SCROLL_PERSIST === 'true';

  const persistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const persistLatestRef = useRef<null | { connectionId: string; sessionId: string; anchor: ChatScrollAnchor }>(
    null,
  );

  const flushPersist = useCallback(() => {
    if (persistTimerRef.current) {
      clearTimeout(persistTimerRef.current);
      persistTimerRef.current = null;
    }
    const payload = persistLatestRef.current;
    if (!payload) {
      return;
    }
    persistLatestRef.current = null;

    if (debugEnabled) {
      console.log('[scrollPersist] persist(flush)', {
        connectionId: payload.connectionId,
        sessionId: payload.sessionId,
        anchor: payload.anchor,
      });
    }

    onUpdateCache({
      connectionId: payload.connectionId,
      sessionId: payload.sessionId,
      messages: getMessagesForCache(),
      scrollAnchor: payload.anchor,
    });
  }, [debugEnabled, getMessagesForCache, onUpdateCache]);

  const schedulePersist = useCallback(
    (anchor: ChatScrollAnchor) => {
      if (!enabled) {
        return;
      }

      if (debugEnabled) {
        console.log('[scrollPersist] persist(schedule)', {
          connectionId,
          sessionId,
          anchor,
        });
      }

      persistLatestRef.current = { connectionId, sessionId, anchor };
      if (persistTimerRef.current) {
        clearTimeout(persistTimerRef.current);
      }
      persistTimerRef.current = setTimeout(() => {
        flushPersist();
      }, debounceMs);
    },
    [connectionId, debugEnabled, debounceMs, enabled, flushPersist, sessionId],
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
    if (!Number.isFinite(contentHeight) || !Number.isFinite(layoutHeight)) {
      return;
    }
    if (layoutHeight <= 0) {
      return;
    }

    const anchor = initialAnchorRef.current;
    if (!anchor) {
      return;
    }

    const maxOffsetY = Math.max(0, contentHeight - layoutHeight);
    const targetOffsetY = anchor.pinnedToBottom
      ? maxOffsetY
      : Math.max(0, maxOffsetY - anchor.bottomGapPx);

    const target = listRef.current;
    if (!target) {
      return;
    }

    if (debugEnabled) {
      console.log('[scrollPersist] restore', {
        connectionId,
        sessionId,
        contentHeight,
        layoutHeight,
        maxOffsetY,
        anchor,
        targetOffsetY,
      });
    }

    scrollToOffsetY(target, targetOffsetY);
    hasRestoredRef.current = true;
  }, [connectionId, debugEnabled, enabled, sessionId]);

  useEffect(() => {
    initialAnchorRef.current = isChatScrollAnchor(cachedScrollAnchor)
      ? cachedScrollAnchor
      : null;
    maybeRestoreScroll();
  }, [cachedScrollAnchor, maybeRestoreScroll]);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    maybeRestoreScroll();
  }, [enabled, maybeRestoreScroll]);

  useEffect(() => {
    if (debugEnabled) {
      console.log('[scrollPersist] init', {
        connectionId,
        sessionId,
        cachedScrollAnchor,
      });
    }
  }, [cachedScrollAnchor, connectionId, debugEnabled, sessionId]);

  useEffect(() => {
    if (!debugEnabled) {
      return;
    }
    if (hasRestoredRef.current) {
      console.log('[scrollPersist] restored', { connectionId, sessionId });
    }
  }, [connectionId, debugEnabled, sessionId]);

  useEffect(() => {
    return () => {
      flushPersist();
    };
  }, [flushPersist]);

  useEffect(() => {
    if (enabled) {
      return;
    }
    flushPersist();
  }, [enabled, flushPersist]);

  const onLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? NaN);
      if (Number.isFinite(height)) {
        layoutHeightRef.current = height;
        if (debugEnabled) {
          console.log('[scrollPersist] layout', { connectionId, sessionId, height });
        }
      }
      maybeRestoreScroll();
    },
    [connectionId, debugEnabled, maybeRestoreScroll, sessionId],
  );

  const onContentSizeChange = useCallback(
    (_width: number, height: number) => {
      const resolved = Number(height ?? NaN);
      if (Number.isFinite(resolved)) {
        contentHeightRef.current = resolved;
        if (debugEnabled) {
          console.log('[scrollPersist] contentSize', {
            connectionId,
            sessionId,
            height: resolved,
          });
        }
      }
      maybeRestoreScroll();
    },
    [connectionId, debugEnabled, maybeRestoreScroll, sessionId],
  );

  const handleScrollEvent = useCallback(
    (kind: 'scroll' | 'endDrag' | 'momentumEnd', event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const native = event.nativeEvent;
      const offsetY = Number((native as any)?.contentOffset?.y ?? NaN);
      const contentHeight = Number((native as any)?.contentSize?.height ?? NaN);
      const layoutHeight = Number((native as any)?.layoutMeasurement?.height ?? NaN);

      const debugThrottleMs = 500;
      const now = Date.now();
      const shouldDebug = debugEnabled && now - lastDebugAtRef.current >= debugThrottleMs;
      if (shouldDebug) {
        lastDebugAtRef.current = now;
        const snapshot = {
          kind,
          connectionId,
          sessionId,
          hasContentOffset: (native as any)?.contentOffset != null,
          hasContentSize: (native as any)?.contentSize != null,
          hasLayoutMeasurement: (native as any)?.layoutMeasurement != null,
          contentOffset: (native as any)?.contentOffset,
          contentSize: (native as any)?.contentSize,
          layoutMeasurement: (native as any)?.layoutMeasurement,
        };
        console.log('[scrollPersist] onScroll(raw)', snapshot);
      }

      if (Number.isFinite(contentHeight)) {
        contentHeightRef.current = contentHeight;
      }
      if (Number.isFinite(layoutHeight)) {
        layoutHeightRef.current = layoutHeight;
      }
      if (!Number.isFinite(offsetY)) {
        return;
      }

      const resolvedContentHeight = contentHeightRef.current;
      const resolvedLayoutHeight = layoutHeightRef.current;
      if (resolvedContentHeight == null || resolvedLayoutHeight == null) {
        return;
      }

      const bottomGapPx = Math.max(
        0,
        resolvedContentHeight - resolvedLayoutHeight - offsetY,
      );
      const pinnedToBottom = bottomGapPx <= PINNED_TO_BOTTOM_THRESHOLD_PX;

      if (debugEnabled) {
        console.log('[scrollPersist] scroll(anchor)', {
          kind,
          connectionId,
          sessionId,
          offsetY,
          contentHeight: resolvedContentHeight,
          layoutHeight: resolvedLayoutHeight,
          bottomGapPx,
          pinnedToBottom,
        });
      }

      schedulePersist(
        createChatScrollAnchor({
          bottomGapPx,
          pinnedToBottom,
        }),
      );
    },
    [connectionId, debugEnabled, schedulePersist, sessionId],
  );

  const onScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      handleScrollEvent('scroll', event);
    },
    [handleScrollEvent],
  );

  const onScrollEndDrag = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      handleScrollEvent('endDrag', event);
    },
    [handleScrollEvent],
  );

  const onMomentumScrollEnd = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      handleScrollEvent('momentumEnd', event);
    },
    [handleScrollEvent],
  );

  const result = useMemo(() => {
    return {
      listRef,
      onScroll,
      onScrollEndDrag,
      onMomentumScrollEnd,
      onLayout,
      onContentSizeChange,
    };
  }, [onContentSizeChange, onLayout, onMomentumScrollEnd, onScroll, onScrollEndDrag]);

  return result;
}
