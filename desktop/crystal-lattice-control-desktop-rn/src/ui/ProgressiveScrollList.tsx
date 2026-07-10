import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type {
  LayoutChangeEvent,
  NativeScrollEvent,
  NativeSyntheticEvent,
  StyleProp,
  ViewStyle,
} from 'react-native';
import { FlatList, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';
import type { ListRenderItemInfo, PlaceholderFlatListProps } from './PlaceholderFlatList';

type ProgressiveScrollListProps<TItem> = PlaceholderFlatListProps<TItem> & {
  backingList?: 'scrollView' | 'flatList';
  growOnly?: boolean;
  initialWindowSize?: number;
  pageSize?: number;
  maxWindowSize?: number;
  autoLoadEdges?: boolean;
  edgeThresholdPx?: number;
  prebuildRows?: boolean;
  defaultAnchorBeforeCount?: number;
  defaultAnchorAfterCount?: number;
  scrollActionTimeoutMs?: number;
  edgeScrollEpsilonPx?: number;
  edgeScrollStableMs?: number;
  debugLogEnabled?: boolean;
};

type RowCacheEntry<TItem> = {
  item: TItem;
  deps: ReadonlyArray<unknown> | null;
  element: React.ReactElement | null;
};

type RowLayout = {
  y: number;
  height: number;
  sourceIndex: number;
};

type RenderedEntry<TItem> = {
  key: string;
  row: React.ReactElement | null;
  sourceIndex: number;
};

type VisibleAnchor = {
  key: string;
  sourceIndex: number;
  offsetFromViewportTop: number;
};

type ItemAnchorRequest = {
  key?: string;
  sourceIndex?: number;
  offsetFromViewportTop: number;
  beforeCount?: number;
  afterCount?: number;
  animated?: boolean;
};

type PendingScrollAction =
  | {
      kind: 'itemAnchor';
      request: Required<Pick<ItemAnchorRequest, 'offsetFromViewportTop'>> &
        Omit<ItemAnchorRequest, 'offsetFromViewportTop'>;
      window?: { start: number; end: number };
      startedAtMs: number;
      checking?: boolean;
      usedIndexScroll?: boolean;
      settleFrames?: number;
      windowSettleFrames?: number;
      windowSettled?: boolean;
      loadingEdge?: 'top' | 'bottom';
    }
  | {
      kind: 'edge';
      edge: 'top' | 'bottom';
      window?: { start: number; end: number };
      animated: boolean;
      startedAtMs: number;
      checking?: boolean;
      stableSinceMs?: number;
      lastMaxOffsetY?: number;
      usedScroll?: boolean;
      loadingEdge?: 'top' | 'bottom';
    };

function shallowArrayEqual(
  a: ReadonlyArray<unknown> | null,
  b: ReadonlyArray<unknown> | null,
): boolean {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) {
    if (!Object.is(a[i], b[i])) return false;
  }
  return true;
}

function renderMaybeComponent(value: unknown): React.ReactElement | null {
  if (value == null) {
    return null;
  }
  if (React.isValidElement(value)) {
    return value;
  }
  if (typeof value === 'function') {
    const Component = value as React.ComponentType<any>;
    return <Component />;
  }
  return null;
}

function getWindowForEnd(length: number, size: number): { start: number; end: number } {
  const end = length;
  return { start: Math.max(0, end - size), end };
}

function getWindowForStart(length: number, size: number): { start: number; end: number } {
  return { start: 0, end: Math.min(length, size) };
}

function getWindowAroundIndex(
  index: number,
  length: number,
  beforeCount: number,
  afterCount: number,
  maxWindowSize: number,
): { start: number; end: number } {
  if (length <= 0) {
    return { start: 0, end: 0 };
  }
  const target = Math.max(0, Math.min(length - 1, index));
  let start = Math.max(0, target - Math.max(0, beforeCount));
  let end = Math.min(length, target + Math.max(0, afterCount) + 1);
  if (end - start > maxWindowSize) {
    end = Math.min(length, start + maxWindowSize);
  }
  if (target >= end) {
    end = Math.min(length, target + 1);
    start = Math.max(0, end - maxWindowSize);
  }
  if (end - start > maxWindowSize) {
    start = Math.max(0, end - maxWindowSize);
  }
  return { start, end };
}

function clampWindow(
  start: number,
  end: number,
  length: number,
  maxWindowSize: number,
): { start: number; end: number } {
  const resolvedEnd = Math.max(0, Math.min(length, end));
  const resolvedStart = Math.max(0, Math.min(start, resolvedEnd));
  if (resolvedEnd - resolvedStart <= maxWindowSize) {
    return { start: resolvedStart, end: resolvedEnd };
  }
  return { start: Math.max(0, resolvedEnd - maxWindowSize), end: resolvedEnd };
}

function clampWindowBounds(start: number, end: number, length: number): { start: number; end: number } {
  const resolvedEnd = Math.max(0, Math.min(length, end));
  const resolvedStart = Math.max(0, Math.min(start, resolvedEnd));
  return { start: resolvedStart, end: resolvedEnd };
}

const ITEM_ANCHOR_EPSILON_PX = 4;
const DEFAULT_EDGE_SCROLL_EPSILON_PX = 4;
const DEFAULT_EDGE_SCROLL_STABLE_MS = 200;

export function ProgressiveScrollList<TItem>(
  props: ProgressiveScrollListProps<TItem>,
): React.JSX.Element {
  const {
    data,
    renderItem,
    keyExtractor,
    getItemDependencies,
    listRef,
    style,
    contentContainerStyle,
    testID,
    ListHeaderComponent,
    ListFooterComponent,
    ListEmptyComponent,
    ItemSeparatorComponent,
    extraData,
    scrollEventThrottle,
    onLayout,
    onContentSizeChange,
    onScroll,
    onScrollBeginDrag,
    onScrollEndDrag,
    onMomentumScrollEnd,
    scrollEnabled,
    showsVerticalScrollIndicator,
    backingList = 'scrollView',
    growOnly = false,
    initialWindowSize = 50,
    pageSize = 50,
    maxWindowSize = 100,
    autoLoadEdges = false,
    edgeThresholdPx = 240,
    prebuildRows = true,
    defaultAnchorBeforeCount = 40,
    defaultAnchorAfterCount = 59,
    scrollActionTimeoutMs = 3000,
    edgeScrollEpsilonPx = DEFAULT_EDGE_SCROLL_EPSILON_PX,
    edgeScrollStableMs = DEFAULT_EDGE_SCROLL_STABLE_MS,
    debugLogEnabled = false,
  } = props;

  const resolvedInitialWindowSize = Math.max(1, Math.round(initialWindowSize));
  const resolvedPageSize = Math.max(1, Math.round(pageSize));
  const resolvedMaxWindowSize = Math.max(
    resolvedInitialWindowSize,
    Math.round(maxWindowSize),
  );
  const resolvedEdgeScrollEpsilonPx = Math.max(0, Math.round(edgeScrollEpsilonPx));
  const resolvedEdgeScrollStableMs = Math.max(0, Math.round(edgeScrollStableMs));

  const scrollRef = useRef<any>(null);
  const cacheRef = useRef<Map<string, RowCacheEntry<TItem>>>(new Map());
  const lastExtraDataRef = useRef(extraData);
  const rowLayoutsRef = useRef<Map<string, RowLayout>>(new Map());
  const rowRefsRef = useRef<Map<string, any>>(new Map());
  const viewableAnchorsRef = useRef<Array<{ key: string; sourceIndex: number }>>([]);
  const pendingScrollActionRef = useRef<PendingScrollAction | null>(null);
  const pendingActionFrameRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);
  const runPendingScrollActionRef = useRef<() => void>(() => {});
  const loadMoreTopRef = useRef<() => void>(() => {});
  const loadMoreBottomRef = useRef<() => void>(() => {});
  const lastWindowChangeAnchorRef = useRef<VisibleAnchor | null>(null);
  const metricsRef = useRef({ offsetY: 0, viewportHeight: 0, contentHeight: 0 });
  const debugLogRef = useRef<Array<Record<string, unknown>>>([]);
  const viewabilityConfigRef = useRef({ itemVisiblePercentThreshold: 1 });
  const [layoutVersion, setLayoutVersion] = useState(0);
  const [loadingEdge, setLoadingEdge] = useState<'top' | 'bottom' | null>(null);
  const [windowRange, setWindowRange] = useState(() =>
    getWindowForEnd(data.length, resolvedInitialWindowSize),
  );
  const useFlatListBacking = backingList === 'flatList';
  const effectiveGrowOnly = useFlatListBacking && growOnly;
  const appendDebugLog = useCallback(
    (event: string, details: Record<string, unknown> = {}) => {
      if (!debugLogEnabled) {
        return;
      }
      const entry = {
        at: Date.now(),
        event,
        windowStart: windowRange.start,
        windowEnd: windowRange.end,
        pendingKind: pendingScrollActionRef.current?.kind ?? null,
        ...details,
      };
      debugLogRef.current = [...debugLogRef.current.slice(-79), entry];
      console.log('[progressiveScroll]', entry);
    },
    [debugLogEnabled, windowRange.end, windowRange.start],
  );
  const onViewableItemsChangedRef = useRef(
    ({
      viewableItems,
    }: {
      viewableItems: Array<{
        item?: RenderedEntry<TItem>;
        index?: number | null;
        isViewable?: boolean;
      }>;
    }) => {
      const anchors = viewableItems
        .filter((entry) => entry.isViewable !== false && entry.item)
        .map((entry) => entry.item as RenderedEntry<TItem>)
        .filter((entry) => entry?.key?.startsWith('msg-'))
        .map((entry) => ({ key: entry.key, sourceIndex: entry.sourceIndex }));
      viewableAnchorsRef.current = anchors;
      const first = viewableItems
        .filter((entry) => entry.isViewable !== false && entry.item)
        .sort((a, b) => (a.index ?? 0) - (b.index ?? 0))[0];
      if (!first?.item) {
        return;
      }
      appendDebugLog('viewableAnchor', {
        key: first.item.key,
        sourceIndex: first.item.sourceIndex,
      });
    },
  );
  const normalizeWindow = useCallback(
    (start: number, end: number) =>
      effectiveGrowOnly
        ? clampWindowBounds(start, end, data.length)
        : clampWindow(start, end, data.length, resolvedMaxWindowSize),
    [data.length, effectiveGrowOnly, resolvedMaxWindowSize],
  );
  const scrollToY = useCallback(
    (y: number, animated?: boolean) => {
      appendDebugLog('scrollToY', { y, animated: animated ?? false, useFlatListBacking });
      if (useFlatListBacking) {
        scrollRef.current?.scrollToOffset?.({ offset: y, animated: animated ?? false });
        return;
      }
      scrollRef.current?.scrollTo?.({ y, animated: animated ?? false });
    },
    [appendDebugLog, useFlatListBacking],
  );
  const scrollToBackingEnd = useCallback(
    (animated?: boolean) => {
      appendDebugLog('scrollToBackingEnd', { animated: animated ?? false });
      scrollRef.current?.scrollToEnd?.({ animated: animated ?? false });
    },
    [appendDebugLog],
  );

  const measureItemViewportOffset = useCallback(
    (key: string): Promise<number | null> => {
      if (!useFlatListBacking) {
        const layout = rowLayoutsRef.current.get(key);
        if (!layout) {
          return Promise.resolve(null);
        }
        return getMacScrollViewMetrics(scrollRef.current).then((metrics) =>
          metrics ? layout.y - metrics.offsetY : null,
        );
      }

      const rowRef = rowRefsRef.current.get(key);
      const nativeScrollRef =
        scrollRef.current?.getNativeScrollRef?.() ??
        scrollRef.current?.getScrollableNode?.() ??
        scrollRef.current;
      if (!rowRef || !nativeScrollRef || typeof rowRef.measureLayout !== 'function') {
        return Promise.resolve(null);
      }
      return new Promise((resolve) => {
        try {
          rowRef.measureLayout(
            nativeScrollRef,
            (_x: number, y: number) => {
              if (!Number.isFinite(y)) {
                resolve(null);
                return;
              }
              getMacScrollViewMetrics(scrollRef.current)
                .then((metrics) => {
                  resolve(metrics ? y - metrics.offsetY : y);
                })
                .catch(() => resolve(y));
            },
            () => resolve(null),
          );
        } catch {
          resolve(null);
        }
      });
    },
    [useFlatListBacking],
  );

  const getKey = useCallback(
    (item: TItem, index: number) => (keyExtractor ? keyExtractor(item, index) : String(index)),
    [keyExtractor],
  );

  const findSourceIndexForRequest = useCallback(
    (request: Pick<ItemAnchorRequest, 'key' | 'sourceIndex'>): number | null => {
      if (request.key != null) {
        for (let index = 0; index < data.length; index += 1) {
          if (getKey(data[index], index) === request.key) {
            return index;
          }
        }
      }
      if (typeof request.sourceIndex === 'number' && Number.isFinite(request.sourceIndex)) {
        return Math.max(0, Math.min(data.length - 1, Math.round(request.sourceIndex)));
      }
      return null;
    },
    [data, getKey],
  );

  const schedulePendingActionAttempt = useCallback(() => {
    if (pendingActionFrameRef.current != null) {
      return;
    }
    pendingActionFrameRef.current = requestAnimationFrame(() => {
      pendingActionFrameRef.current = null;
      runPendingScrollActionRef.current();
    });
  }, []);

  const runPendingScrollAction = useCallback(() => {
    const action = pendingScrollActionRef.current;
    if (!action) {
      return;
    }
    if (!action.checking) {
      appendDebugLog('runPendingAction', {
        actionKind: action.kind,
        actionEdge: action.kind === 'edge' ? action.edge : null,
        actionKey: action.kind === 'itemAnchor' ? action.request.key : null,
        checking: action.checking ?? false,
        usedScroll:
          action.kind === 'edge' ? action.usedScroll ?? false : action.usedIndexScroll ?? false,
      });
    }
    const now = Date.now();
    if (now - action.startedAtMs > scrollActionTimeoutMs) {
      pendingScrollActionRef.current = null;
      if (action.loadingEdge) {
        setLoadingEdge(null);
      }
      appendDebugLog('pendingActionTimeout', { actionKind: action.kind });
      return;
    }

    if (action.kind === 'edge') {
      const desiredWindow =
        action.window ??
        (action.edge === 'top'
          ? getWindowForStart(data.length, resolvedMaxWindowSize)
          : getWindowForEnd(data.length, resolvedMaxWindowSize));
      if (
        windowRange.start !== desiredWindow.start ||
        windowRange.end !== desiredWindow.end
      ) {
        setWindowRange(desiredWindow);
        appendDebugLog('edgeSetWindow', {
          edge: action.edge,
          desiredStart: desiredWindow.start,
          desiredEnd: desiredWindow.end,
        });
        schedulePendingActionAttempt();
        return;
      }
      if (!action.usedScroll) {
        action.usedScroll = true;
        if (action.edge === 'top') {
          scrollToY(0, action.animated);
        } else {
          scrollToBackingEnd(action.animated);
        }
      }
      if (action.checking) {
        return;
      }
      action.checking = true;
      const scrollView = scrollRef.current;
      requestAnimationFrame(() => {
        getMacScrollViewMetrics(scrollView)
          .then((metrics) => {
            if (pendingScrollActionRef.current !== action) {
              return;
            }
            action.checking = false;
            if (!metrics) {
              schedulePendingActionAttempt();
              return;
            }
            metricsRef.current = {
              offsetY: metrics.offsetY,
              viewportHeight: metrics.viewportHeight,
              contentHeight: metrics.contentHeight,
            };
            const maxOffsetY = Math.max(0, metrics.contentHeight - metrics.viewportHeight);
            const targetOffsetY = action.edge === 'top' ? 0 : maxOffsetY;
            const reached =
              action.edge === 'top'
                ? metrics.offsetY <= resolvedEdgeScrollEpsilonPx
                : maxOffsetY - metrics.offsetY <= resolvedEdgeScrollEpsilonPx;
            const maxOffsetStable =
              action.lastMaxOffsetY == null ||
              Math.abs(action.lastMaxOffsetY - maxOffsetY) <= resolvedEdgeScrollEpsilonPx;
            action.lastMaxOffsetY = maxOffsetY;
            if (reached && maxOffsetStable) {
              action.stableSinceMs = action.stableSinceMs ?? Date.now();
            } else {
              action.stableSinceMs = undefined;
              scrollToY(targetOffsetY, false);
            }
            if (
              action.stableSinceMs != null &&
              Date.now() - action.stableSinceMs >= resolvedEdgeScrollStableMs
            ) {
              pendingScrollActionRef.current = null;
              if (action.loadingEdge) {
                setLoadingEdge(null);
              }
              appendDebugLog('edgeComplete', {
                edge: action.edge,
                offsetY: metrics.offsetY,
                maxOffsetY,
              });
              return;
            }
            schedulePendingActionAttempt();
          })
          .catch(() => {
            if (pendingScrollActionRef.current === action) {
              action.checking = false;
              schedulePendingActionAttempt();
            }
          });
      });
      return;
    }

    const targetIndex = findSourceIndexForRequest(action.request);
    if (targetIndex == null) {
      pendingScrollActionRef.current = null;
      if (action.loadingEdge) {
        setLoadingEdge(null);
      }
      appendDebugLog('itemAnchorMissingTarget', { request: action.request });
      return;
    }
    const desiredWindow =
      action.window ??
      getWindowAroundIndex(
        targetIndex,
        data.length,
        action.request.beforeCount ?? defaultAnchorBeforeCount,
        action.request.afterCount ?? defaultAnchorAfterCount,
        resolvedMaxWindowSize,
      );
    if (
      windowRange.start !== desiredWindow.start ||
      windowRange.end !== desiredWindow.end
    ) {
      action.window = desiredWindow;
      action.windowSettled = false;
      setWindowRange(desiredWindow);
      appendDebugLog('itemAnchorSetWindow', {
        key: action.request.key,
        sourceIndex: action.request.sourceIndex,
        desiredStart: desiredWindow.start,
        desiredEnd: desiredWindow.end,
      });
      schedulePendingActionAttempt();
      return;
    }

    const key = action.request.key ?? getKey(data[targetIndex], targetIndex);
    if (useFlatListBacking) {
      if (action.window && !action.windowSettled) {
        action.windowSettleFrames = (action.windowSettleFrames ?? 0) + 1;
        if (action.windowSettleFrames >= 4) {
          action.windowSettled = true;
          appendDebugLog('itemAnchorWindowSettledByFrame', {
            key: action.request.key,
            windowStart: action.window.start,
            windowEnd: action.window.end,
          });
        } else {
          schedulePendingActionAttempt();
          return;
        }
      }
      if (action.window && !action.windowSettled) {
        schedulePendingActionAttempt();
        return;
      }
      const localIndex = targetIndex - windowRange.start;
      if (localIndex < 0 || localIndex >= windowRange.end - windowRange.start) {
        schedulePendingActionAttempt();
        return;
      }
      if (!action.usedIndexScroll) {
        action.usedIndexScroll = true;
        scrollRef.current?.scrollToIndex?.({
          index: localIndex,
          animated: action.request.animated ?? false,
          viewPosition: 0,
          viewOffset: action.request.offsetFromViewportTop,
        });
        appendDebugLog('flatListScrollToIndex', {
          key,
          localIndex,
          offsetFromViewportTop: action.request.offsetFromViewportTop,
        });
      }
      if (action.checking) {
        return;
      }
      action.checking = true;
      requestAnimationFrame(() => {
        if (pendingScrollActionRef.current !== action) {
          return;
        }
        action.checking = false;
        const settleFrames = (action.settleFrames ?? 0) + 1;
        action.settleFrames = settleFrames;
        measureItemViewportOffset(key).then((actualOffset) => {
          if (pendingScrollActionRef.current !== action) {
            return;
          }
          const matches =
            typeof actualOffset === 'number' &&
            Math.abs(actualOffset - action.request.offsetFromViewportTop) <=
              ITEM_ANCHOR_EPSILON_PX;
          if (!matches && settleFrames < 8) {
            action.usedIndexScroll = false;
            schedulePendingActionAttempt();
            return;
          }
          pendingScrollActionRef.current = null;
          if (action.loadingEdge) {
            setLoadingEdge(null);
          }
          appendDebugLog('itemAnchorCompleteFlatList', {
            key,
            requestedOffsetFromViewportTop: action.request.offsetFromViewportTop,
            actualOffsetFromViewportTop:
              typeof actualOffset === 'number' ? actualOffset : null,
            settleFrames,
          });
        });
      });
      return;
    }

    const layout = rowLayoutsRef.current.get(key);
    if (!layout) {
      schedulePendingActionAttempt();
      return;
    }
    const maxOffsetY = Math.max(
      0,
      metricsRef.current.contentHeight - metricsRef.current.viewportHeight,
    );
    const targetY = Math.max(
      0,
      Math.min(maxOffsetY, layout.y - action.request.offsetFromViewportTop),
    );
    scrollToY(targetY, action.request.animated ?? false);
    metricsRef.current.offsetY = targetY;
    if (action.checking) {
      return;
    }
    action.checking = true;
    const scrollView = scrollRef.current;
    requestAnimationFrame(() => {
      getMacScrollViewMetrics(scrollView)
        .then((metrics) => {
          if (pendingScrollActionRef.current !== action) {
            return;
          }
          action.checking = false;
          if (!metrics) {
            schedulePendingActionAttempt();
            return;
          }
          metricsRef.current = {
            offsetY: metrics.offsetY,
            viewportHeight: metrics.viewportHeight,
            contentHeight: metrics.contentHeight,
          };
          const currentLayout = rowLayoutsRef.current.get(key);
          if (!currentLayout) {
            schedulePendingActionAttempt();
            return;
          }
          const actualOffsetFromViewportTop = currentLayout.y - metrics.offsetY;
          if (
            Math.abs(
              actualOffsetFromViewportTop - action.request.offsetFromViewportTop,
            ) <= ITEM_ANCHOR_EPSILON_PX
          ) {
            pendingScrollActionRef.current = null;
            if (action.loadingEdge) {
              setLoadingEdge(null);
            }
            return;
          }
          schedulePendingActionAttempt();
        })
        .catch(() => {
          if (pendingScrollActionRef.current === action) {
            action.checking = false;
            schedulePendingActionAttempt();
          }
        });
    });
  }, [
    data,
    defaultAnchorAfterCount,
    defaultAnchorBeforeCount,
    findSourceIndexForRequest,
    getKey,
    resolvedEdgeScrollEpsilonPx,
    resolvedEdgeScrollStableMs,
    resolvedMaxWindowSize,
    measureItemViewportOffset,
    schedulePendingActionAttempt,
    scrollToBackingEnd,
    scrollActionTimeoutMs,
    scrollToY,
    useFlatListBacking,
    windowRange.end,
    windowRange.start,
  ]);
  runPendingScrollActionRef.current = runPendingScrollAction;

  const captureAnchor = useCallback(async (): Promise<VisibleAnchor | null> => {
    if (useFlatListBacking) {
      const candidates = viewableAnchorsRef.current;
      if (candidates.length === 0) {
        return null;
      }
      const measured = await Promise.all(
        candidates.map(async (candidate) => ({
          ...candidate,
          offsetFromViewportTop: await measureItemViewportOffset(candidate.key),
        })),
      );
      const visible = measured
        .filter((candidate) => typeof candidate.offsetFromViewportTop === 'number')
        .sort((a, b) => (a.offsetFromViewportTop ?? 0) - (b.offsetFromViewportTop ?? 0))[0];
      if (!visible || typeof visible.offsetFromViewportTop !== 'number') {
        return null;
      }
      const anchor = {
        key: visible.key,
        sourceIndex: visible.sourceIndex,
        offsetFromViewportTop: visible.offsetFromViewportTop,
      };
      return anchor;
    }

    const metrics = await getMacScrollViewMetrics(scrollRef.current);
    if (!metrics) {
      return null;
    }
    metricsRef.current = {
      offsetY: metrics.offsetY,
      viewportHeight: metrics.viewportHeight,
      contentHeight: metrics.contentHeight,
    };
    let firstVisible: (RowLayout & { key: string }) | null = null;
    for (const [key, layout] of rowLayoutsRef.current.entries()) {
      if (layout.y + layout.height <= metrics.offsetY + 1) {
        continue;
      }
      if (!firstVisible || layout.y < firstVisible.y) {
        firstVisible = { ...layout, key };
      }
    }
    if (!firstVisible) {
      return null;
    }
    return {
      key: firstVisible.key,
      sourceIndex: firstVisible.sourceIndex,
      offsetFromViewportTop: firstVisible.y - metrics.offsetY,
    };
  }, [measureItemViewportOffset, useFlatListBacking]);

  const exposeHandle = useMemo(() => {
    return {
      scrollTo: (options: { y?: number; animated?: boolean }) => {
        scrollToY(options.y ?? 0, options.animated);
      },
      scrollToOffset: (options: { offset: number; animated?: boolean }) => {
        const maxOffsetY = Math.max(
          0,
          metricsRef.current.contentHeight - metricsRef.current.viewportHeight,
        );
        if (options.offset <= 0) {
          pendingScrollActionRef.current = {
            kind: 'edge',
            edge: 'top',
            animated: options.animated ?? false,
            startedAtMs: Date.now(),
          };
          runPendingScrollActionRef.current();
          return;
        }
        if (maxOffsetY <= 0 || options.offset >= maxOffsetY - 2) {
          pendingScrollActionRef.current = {
            kind: 'edge',
            edge: 'bottom',
            animated: options.animated ?? false,
            startedAtMs: Date.now(),
          };
          runPendingScrollActionRef.current();
          return;
        }
        scrollToY(options.offset, options.animated);
      },
      scrollToEnd: (options?: { animated?: boolean }) => {
        pendingScrollActionRef.current = {
          kind: 'edge',
          edge: 'bottom',
          animated: options?.animated ?? false,
          startedAtMs: Date.now(),
        };
        runPendingScrollActionRef.current();
      },
      scrollToTop: (options?: { animated?: boolean }) => {
        pendingScrollActionRef.current = {
          kind: 'edge',
          edge: 'top',
          animated: options?.animated ?? false,
          startedAtMs: Date.now(),
        };
        runPendingScrollActionRef.current();
      },
      scrollToBottom: (options?: { animated?: boolean }) => {
        pendingScrollActionRef.current = {
          kind: 'edge',
          edge: 'bottom',
          animated: options?.animated ?? false,
          startedAtMs: Date.now(),
        };
        runPendingScrollActionRef.current();
      },
      scrollCurrentWindowToTop: (options?: { animated?: boolean }) => {
        pendingScrollActionRef.current = {
          kind: 'edge',
          edge: 'top',
          window: windowRange,
          animated: options?.animated ?? false,
          startedAtMs: Date.now(),
        };
        runPendingScrollActionRef.current();
      },
      scrollCurrentWindowToBottom: (options?: { animated?: boolean }) => {
        pendingScrollActionRef.current = {
          kind: 'edge',
          edge: 'bottom',
          window: windowRange,
          animated: options?.animated ?? false,
          startedAtMs: Date.now(),
        };
        runPendingScrollActionRef.current();
      },
      scrollToItemAnchor: (request: ItemAnchorRequest) => {
        pendingScrollActionRef.current = {
          kind: 'itemAnchor',
          request,
          startedAtMs: Date.now(),
        };
        runPendingScrollActionRef.current();
      },
      getVisibleAnchor: captureAnchor,
      getLastWindowChangeAnchor: () => lastWindowChangeAnchorRef.current,
      hasPendingScrollAction: () => pendingScrollActionRef.current != null,
      getItemViewportOffset: async (key: string) => {
        return measureItemViewportOffset(key);
      },
      getRenderedWindowRange: () => ({
        start: windowRange.start,
        end: windowRange.end,
        length: data.length,
      }),
      getDebugLog: () => debugLogRef.current,
      loadMoreTop: () => loadMoreTopRef.current(),
      loadMoreBottom: () => loadMoreBottomRef.current(),
      cancelPendingScrollAction: () => {
        if (pendingActionFrameRef.current != null) {
          cancelAnimationFrame(pendingActionFrameRef.current);
          pendingActionFrameRef.current = null;
        }
        pendingScrollActionRef.current = null;
        setLoadingEdge(null);
      },
      getNativeScrollRef: () => scrollRef.current,
      getScrollableNode: () => scrollRef.current?.getScrollableNode?.(),
    };
  }, [
    captureAnchor,
    data.length,
    measureItemViewportOffset,
    scrollToY,
    windowRange.end,
    windowRange.start,
  ]);

  React.useImperativeHandle(listRef as React.Ref<any> | undefined, () => exposeHandle, [
    exposeHandle,
  ]);

  if (!Object.is(lastExtraDataRef.current, extraData)) {
    cacheRef.current.clear();
    lastExtraDataRef.current = extraData;
  }

  useLayoutEffect(() => {
    runPendingScrollActionRef.current();
  }, [layoutVersion, windowRange.start, windowRange.end]);

  useEffect(() => {
    let cancelled = false;
    const adjustForDataChange = async () => {
      if (data.length === 0) {
        setWindowRange({ start: 0, end: 0 });
        return;
      }
      const bottomGap = Math.max(
        0,
        metricsRef.current.contentHeight -
          metricsRef.current.viewportHeight -
          metricsRef.current.offsetY,
      );
      if (bottomGap <= edgeThresholdPx) {
        appendDebugLog('dataChangeFollowBottom', { bottomGap, edgeThresholdPx });
        pendingScrollActionRef.current = {
          kind: 'edge',
          edge: 'bottom',
          animated: false,
          startedAtMs: Date.now(),
        };
        setWindowRange(getWindowForEnd(data.length, resolvedMaxWindowSize));
        schedulePendingActionAttempt();
        return;
      }
      const anchor = await captureAnchor();
      if (cancelled) {
        return;
      }
      if (anchor) {
        appendDebugLog('dataChangeRestoreAnchor', {
          key: anchor.key,
          sourceIndex: anchor.sourceIndex,
          offsetFromViewportTop: anchor.offsetFromViewportTop,
        });
        pendingScrollActionRef.current = {
          kind: 'itemAnchor',
          request: {
            key: anchor.key,
            sourceIndex: anchor.sourceIndex,
            offsetFromViewportTop: anchor.offsetFromViewportTop,
            beforeCount: defaultAnchorBeforeCount,
            afterCount: defaultAnchorAfterCount,
            animated: false,
          },
          startedAtMs: Date.now(),
        };
      }
      setWindowRange((current) =>
        effectiveGrowOnly
          ? clampWindowBounds(current.start, current.end, data.length)
          : clampWindow(current.start, current.end, data.length, resolvedMaxWindowSize),
      );
      schedulePendingActionAttempt();
    };
    adjustForDataChange().catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [
    captureAnchor,
    data.length,
    defaultAnchorAfterCount,
    defaultAnchorBeforeCount,
    edgeThresholdPx,
    resolvedMaxWindowSize,
    schedulePendingActionAttempt,
    effectiveGrowOnly,
  ]);

  const hasMoreAtTop = windowRange.start > 0;
  const hasMoreAtBottom = windowRange.end < data.length;
  const visibleItems = data.slice(windowRange.start, windowRange.end);

  const applyWindowChange = useCallback(
    async (
      nextStart: number,
      nextEnd: number,
      options?: { loadingEdge?: 'top' | 'bottom' },
    ) => {
      const anchor = await captureAnchor();
      const nextWindow = normalizeWindow(nextStart, nextEnd);
      appendDebugLog('applyWindowChange', {
        nextStart,
        nextEnd,
        normalizedStart: nextWindow.start,
        normalizedEnd: nextWindow.end,
        anchorKey: anchor?.key ?? null,
        anchorSourceIndex: anchor?.sourceIndex ?? null,
        anchorOffsetFromViewportTop: anchor?.offsetFromViewportTop ?? null,
      });
      lastWindowChangeAnchorRef.current = anchor;
      if (anchor) {
        pendingScrollActionRef.current = {
          kind: 'itemAnchor',
          request: {
            key: anchor.key,
            sourceIndex: anchor.sourceIndex,
            offsetFromViewportTop: anchor.offsetFromViewportTop,
            beforeCount: defaultAnchorBeforeCount,
            afterCount: defaultAnchorAfterCount,
            animated: false,
          },
          window: nextWindow,
          startedAtMs: Date.now(),
          loadingEdge: options?.loadingEdge,
        };
      } else if (options?.loadingEdge) {
        setLoadingEdge(null);
      }
      setWindowRange(nextWindow);
      schedulePendingActionAttempt();
    },
    [
      captureAnchor,
      data.length,
      defaultAnchorAfterCount,
      defaultAnchorBeforeCount,
      normalizeWindow,
      resolvedMaxWindowSize,
      schedulePendingActionAttempt,
    ],
  );

  const handleLoadMoreTop = useCallback((options?: { auto?: boolean }) => {
    if (options?.auto && loadingEdge) {
      return;
    }
    const nextStart = Math.max(0, windowRange.start - resolvedPageSize);
    const nextEnd = effectiveGrowOnly
      ? windowRange.end
      : Math.min(data.length, nextStart + resolvedMaxWindowSize);
    if (options?.auto) {
      setLoadingEdge('top');
    }
    applyWindowChange(nextStart, nextEnd, {
      loadingEdge: options?.auto ? 'top' : undefined,
    }).catch(() => {
      if (options?.auto) {
        setLoadingEdge(null);
      }
    });
  }, [
    applyWindowChange,
    data.length,
    effectiveGrowOnly,
    loadingEdge,
    resolvedMaxWindowSize,
    resolvedPageSize,
    windowRange.end,
    windowRange.start,
  ]);

  const handleLoadMoreBottom = useCallback((options?: { auto?: boolean }) => {
    if (options?.auto && loadingEdge) {
      return;
    }
    const nextEnd = Math.min(data.length, windowRange.end + resolvedPageSize);
    const nextStart = effectiveGrowOnly
      ? windowRange.start
      : Math.max(0, nextEnd - resolvedMaxWindowSize);
    if (options?.auto) {
      setLoadingEdge('bottom');
    }
    applyWindowChange(nextStart, nextEnd, {
      loadingEdge: options?.auto ? 'bottom' : undefined,
    }).catch(() => {
      if (options?.auto) {
        setLoadingEdge(null);
      }
    });
  }, [
    applyWindowChange,
    data.length,
    effectiveGrowOnly,
    loadingEdge,
    resolvedMaxWindowSize,
    resolvedPageSize,
    windowRange.start,
    windowRange.end,
  ]);

  loadMoreTopRef.current = () => handleLoadMoreTop();
  loadMoreBottomRef.current = () => handleLoadMoreBottom();

  const handleScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const nativeEvent = event.nativeEvent;
      metricsRef.current = {
        offsetY: Number(nativeEvent?.contentOffset?.y ?? 0),
        viewportHeight: Number(nativeEvent?.layoutMeasurement?.height ?? 0),
        contentHeight: Number(nativeEvent?.contentSize?.height ?? 0),
      };
      onScroll?.(event);
      appendDebugLog('onScroll', metricsRef.current);
      runPendingScrollActionRef.current();
      if (!autoLoadEdges) {
        return;
      }
      if (loadingEdge) {
        appendDebugLog('autoLoadSuppressedLoading', { loadingEdge });
        return;
      }
      if (pendingScrollActionRef.current) {
        appendDebugLog('autoLoadSuppressedPending');
        return;
      }
      if (metricsRef.current.offsetY <= edgeThresholdPx && hasMoreAtTop) {
        appendDebugLog('autoLoadTop', { edgeThresholdPx });
        handleLoadMoreTop({ auto: true });
        return;
      }
      const bottomGap = Math.max(
        0,
        metricsRef.current.contentHeight -
          metricsRef.current.viewportHeight -
          metricsRef.current.offsetY,
      );
      if (bottomGap <= edgeThresholdPx && hasMoreAtBottom) {
        appendDebugLog('autoLoadBottom', { bottomGap, edgeThresholdPx });
        handleLoadMoreBottom({ auto: true });
      }
    },
    [
      autoLoadEdges,
      edgeThresholdPx,
      handleLoadMoreBottom,
      handleLoadMoreTop,
      hasMoreAtBottom,
      hasMoreAtTop,
      loadingEdge,
      onScroll,
    ],
  );

  const handleContentSizeChange = useCallback(
    (width: number, height: number) => {
      metricsRef.current.contentHeight = height;
      appendDebugLog('contentSizeChange', { width, height });
      const action = pendingScrollActionRef.current;
      if (
        action?.kind === 'itemAnchor' &&
        action.window &&
        windowRange.start === action.window.start &&
        windowRange.end === action.window.end
      ) {
        action.windowSettled = true;
        appendDebugLog('itemAnchorWindowSettled', {
          key: action.request.key,
          windowStart: action.window.start,
          windowEnd: action.window.end,
        });
      }
      onContentSizeChange?.(width, height);
      runPendingScrollActionRef.current();
    },
    [onContentSizeChange],
  );

  const handleLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? 0);
      metricsRef.current.viewportHeight = height;
      appendDebugLog('layout', { height });
      onLayout?.(event);
      runPendingScrollActionRef.current();
    },
    [onLayout],
  );

  const handleScrollBeginDrag = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      if (pendingActionFrameRef.current != null) {
        cancelAnimationFrame(pendingActionFrameRef.current);
        pendingActionFrameRef.current = null;
      }
      pendingScrollActionRef.current = null;
      setLoadingEdge(null);
      onScrollBeginDrag?.(event);
    },
    [onScrollBeginDrag],
  );

  const cache = cacheRef.current;
  const mountedKeys = new Set<string>();
  const cachedKeysInUse = new Set<string>();
  const Separator = ItemSeparatorComponent;
  const getCachedRow = (item: TItem, sourceIndex: number): { key: string; row: React.ReactElement | null } => {
    const key = getKey(item, sourceIndex);
    cachedKeysInUse.add(key);
    const deps = getItemDependencies ? getItemDependencies(item, sourceIndex) : null;
    const cached = cache.get(key);
    if (cached && cached.item === item && shallowArrayEqual(cached.deps, deps)) {
      return { key, row: cached.element };
    }
    const row = renderItem({ item, index: sourceIndex } as ListRenderItemInfo<TItem>);
    cache.set(key, { item, deps, element: row });
    return { key, row };
  };

  if (prebuildRows) {
    data.forEach((item, sourceIndex) => {
      getCachedRow(item, sourceIndex);
    });
  }

  const renderedEntries: RenderedEntry<TItem>[] = visibleItems.map((item, localIndex) => {
    const sourceIndex = windowRange.start + localIndex;
    const { key, row } = getCachedRow(item, sourceIndex);
    mountedKeys.add(key);
    return { key, row, sourceIndex };
  });

  const renderMeasuredEntry = (entry: RenderedEntry<TItem>): React.ReactElement | null => {
    if (!entry.row) {
      return null;
    }
    return (
      <View
        testID={`progressive-scroll-row-${entry.key}`}
        ref={(node) => {
          if (node) {
            rowRefsRef.current.set(entry.key, node);
          } else {
            rowRefsRef.current.delete(entry.key);
          }
        }}
        collapsable={false}
        onLayout={(event) => {
          const layout = event.nativeEvent?.layout;
          const y = Number(layout?.y ?? NaN);
          const height = Number(layout?.height ?? NaN);
          if (!Number.isFinite(y) || !Number.isFinite(height)) {
            return;
          }
          rowLayoutsRef.current.set(entry.key, {
            y,
            height,
            sourceIndex: entry.sourceIndex,
          });
          setLayoutVersion((version) => version + 1);
          runPendingScrollActionRef.current();
        }}
      >
        {entry.row}
      </View>
    );
  };

  const renderedRows = renderedEntries.map((entry, localIndex) => (
    <React.Fragment key={entry.key}>
      {localIndex > 0 && Separator ? (
        React.isValidElement(Separator) ? (
          Separator
        ) : (
          <View>{renderMaybeComponent(Separator)}</View>
        )
      ) : null}
      {renderMeasuredEntry(entry)}
    </React.Fragment>
  ));

  for (const cachedKey of cache.keys()) {
    if (!cachedKeysInUse.has(cachedKey)) {
      cache.delete(cachedKey);
    }
  }
  for (const layoutKey of rowLayoutsRef.current.keys()) {
    if (!mountedKeys.has(layoutKey)) {
      rowLayoutsRef.current.delete(layoutKey);
    }
  }
  for (const refKey of rowRefsRef.current.keys()) {
    if (!mountedKeys.has(refKey)) {
      rowRefsRef.current.delete(refKey);
    }
  }

  const header = renderMaybeComponent(ListHeaderComponent);
  const footer = renderMaybeComponent(ListFooterComponent);
  const empty = data.length === 0 ? renderMaybeComponent(ListEmptyComponent) : null;
  const renderLoader = (edge: 'top' | 'bottom') => (
    <View style={styles.loadMoreContainer}>
      <View
        testID={`progressive-scroll-loading-${edge}`}
        accessibilityRole="progressbar"
        accessibilityLabel={`Loading messages ${edge === 'top' ? 'above' : 'below'}`}
        style={styles.loadingIndicator}
      >
        <Text style={styles.loadMoreButtonText}>Loading...</Text>
      </View>
    </View>
  );
  const topLoadControl = hasMoreAtTop && autoLoadEdges ? (
    loadingEdge === 'top' ? renderLoader('top') : null
  ) : hasMoreAtTop ? (
    <View style={styles.loadMoreContainer}>
      <Pressable
        testID="progressive-scroll-load-top"
        accessibilityRole="button"
        accessibilityLabel="Load messages above"
        style={styles.loadMoreButton}
        onPress={() => handleLoadMoreTop()}
      >
        <Text style={styles.loadMoreButtonText}>
          {windowRange.start} messages hidden above
        </Text>
      </Pressable>
    </View>
  ) : null;
  const bottomLoadControl = hasMoreAtBottom && autoLoadEdges ? (
    loadingEdge === 'bottom' ? renderLoader('bottom') : null
  ) : hasMoreAtBottom ? (
    <View style={styles.loadMoreContainer}>
      <Pressable
        testID="progressive-scroll-load-bottom"
        accessibilityRole="button"
        accessibilityLabel="Load messages below"
        style={styles.loadMoreButton}
        onPress={() => handleLoadMoreBottom()}
      >
        <Text style={styles.loadMoreButtonText}>
          {data.length - windowRange.end} messages hidden below
        </Text>
      </Pressable>
    </View>
  ) : null;

  if (useFlatListBacking) {
    const separatorElement = renderMaybeComponent(Separator);
    return (
      <FlatList
        ref={scrollRef}
        testID={testID}
        style={style}
        contentContainerStyle={contentContainerStyle}
        data={renderedEntries}
        keyExtractor={(entry) => entry.key}
        renderItem={({ item }) => renderMeasuredEntry(item)}
        ItemSeparatorComponent={
          separatorElement ? () => separatorElement : undefined
        }
        ListHeaderComponent={
          header || topLoadControl || empty ? (
            <>
              {header}
              {topLoadControl}
              {empty}
            </>
          ) : null
        }
        ListFooterComponent={
          bottomLoadControl || footer ? (
            <>
              {bottomLoadControl}
              {footer}
            </>
          ) : null
        }
        scrollEventThrottle={scrollEventThrottle}
        onLayout={handleLayout}
        onContentSizeChange={handleContentSizeChange}
        onScroll={handleScroll}
        onScrollBeginDrag={handleScrollBeginDrag}
        onScrollEndDrag={onScrollEndDrag}
        onMomentumScrollEnd={onMomentumScrollEnd}
        onViewableItemsChanged={onViewableItemsChangedRef.current}
        viewabilityConfig={viewabilityConfigRef.current}
        onScrollToIndexFailed={(info) => {
          appendDebugLog('flatListScrollToIndexFailed', {
            index: info.index,
            highestMeasuredFrameIndex: info.highestMeasuredFrameIndex,
            averageItemLength: info.averageItemLength,
          });
          const action = pendingScrollActionRef.current;
          if (action?.kind === 'itemAnchor') {
            action.usedIndexScroll = false;
            action.checking = false;
            const estimatedOffset =
              Number(info.averageItemLength ?? 0) * Math.max(0, Number(info.index ?? 0));
            if (Number.isFinite(estimatedOffset) && estimatedOffset > 0) {
              scrollToY(estimatedOffset, false);
            }
          }
          schedulePendingActionAttempt();
        }}
        scrollEnabled={scrollEnabled}
        showsVerticalScrollIndicator={showsVerticalScrollIndicator ?? true}
        removeClippedSubviews={false}
      />
    );
  }

  return (
    <ScrollView
      ref={scrollRef}
      testID={testID}
      style={style}
      contentContainerStyle={contentContainerStyle}
      scrollEventThrottle={scrollEventThrottle}
      onLayout={handleLayout}
      onContentSizeChange={handleContentSizeChange}
      onScroll={handleScroll}
      onScrollBeginDrag={handleScrollBeginDrag}
      onScrollEndDrag={onScrollEndDrag}
      onMomentumScrollEnd={onMomentumScrollEnd}
      scrollEnabled={scrollEnabled}
      showsVerticalScrollIndicator={showsVerticalScrollIndicator ?? true}
    >
      {header}
      {topLoadControl}
      {empty}
      {renderedRows}
      {bottomLoadControl}
      {footer}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  loadMoreContainer: {
    paddingVertical: 8,
    alignItems: 'center',
  },
  loadMoreButton: {
    minHeight: 32,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D0D0D0',
    backgroundColor: '#F7F7F7',
    justifyContent: 'center',
  },
  loadingIndicator: {
    minHeight: 32,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D0D0D0',
    backgroundColor: '#F7F7F7',
    justifyContent: 'center',
  },
  loadMoreButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#555555',
  },
});