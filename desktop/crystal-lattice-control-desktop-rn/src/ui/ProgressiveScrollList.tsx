import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type {
  LayoutChangeEvent,
  NativeScrollEvent,
  NativeSyntheticEvent,
  StyleProp,
  ViewStyle,
} from 'react-native';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';
import type { ListRenderItemInfo, PlaceholderFlatListProps } from './PlaceholderFlatList';

type ProgressiveScrollListProps<TItem> = PlaceholderFlatListProps<TItem> & {
  initialWindowSize?: number;
  pageSize?: number;
  maxWindowSize?: number;
  autoLoadEdges?: boolean;
  edgeThresholdPx?: number;
  prebuildRows?: boolean;
  defaultAnchorBeforeCount?: number;
  defaultAnchorAfterCount?: number;
  scrollActionTimeoutMs?: number;
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
    }
  | {
      kind: 'edge';
      edge: 'top' | 'bottom';
      animated: boolean;
      startedAtMs: number;
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
    initialWindowSize = 50,
    pageSize = 50,
    maxWindowSize = 100,
    autoLoadEdges = false,
    edgeThresholdPx = 240,
    prebuildRows = true,
    defaultAnchorBeforeCount = 40,
    defaultAnchorAfterCount = 59,
    scrollActionTimeoutMs = 3000,
  } = props;

  const resolvedInitialWindowSize = Math.max(1, Math.round(initialWindowSize));
  const resolvedPageSize = Math.max(1, Math.round(pageSize));
  const resolvedMaxWindowSize = Math.max(
    resolvedInitialWindowSize,
    Math.round(maxWindowSize),
  );

  const scrollRef = useRef<any>(null);
  const cacheRef = useRef<Map<string, RowCacheEntry<TItem>>>(new Map());
  const lastExtraDataRef = useRef(extraData);
  const rowLayoutsRef = useRef<Map<string, RowLayout>>(new Map());
  const pendingScrollActionRef = useRef<PendingScrollAction | null>(null);
  const pendingActionFrameRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);
  const runPendingScrollActionRef = useRef<() => void>(() => {});
  const metricsRef = useRef({ offsetY: 0, viewportHeight: 0, contentHeight: 0 });
  const [layoutVersion, setLayoutVersion] = useState(0);
  const [windowRange, setWindowRange] = useState(() =>
    getWindowForEnd(data.length, resolvedInitialWindowSize),
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

  const getClosestMeasuredLayout = useCallback(
    (sourceIndex: number): (RowLayout & { key: string }) | null => {
      let closest: (RowLayout & { key: string }) | null = null;
      let closestDistance = Number.POSITIVE_INFINITY;
      for (const [key, candidate] of rowLayoutsRef.current.entries()) {
        const distance = Math.abs(candidate.sourceIndex - sourceIndex);
        if (distance < closestDistance) {
          closest = { ...candidate, key };
          closestDistance = distance;
        }
      }
      return closest;
    },
    [],
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
    const now = Date.now();
    if (now - action.startedAtMs > scrollActionTimeoutMs) {
      pendingScrollActionRef.current = null;
      return;
    }

    if (action.kind === 'edge') {
      const desiredWindow =
        action.edge === 'top'
          ? getWindowForStart(data.length, resolvedMaxWindowSize)
          : getWindowForEnd(data.length, resolvedMaxWindowSize);
      if (
        windowRange.start !== desiredWindow.start ||
        windowRange.end !== desiredWindow.end
      ) {
        setWindowRange(desiredWindow);
        schedulePendingActionAttempt();
        return;
      }
      if (action.edge === 'top') {
        scrollRef.current?.scrollTo?.({ y: 0, animated: action.animated });
      } else {
        scrollRef.current?.scrollToEnd?.({ animated: action.animated });
      }
      pendingScrollActionRef.current = null;
      return;
    }

    const targetIndex = findSourceIndexForRequest(action.request);
    if (targetIndex == null) {
      pendingScrollActionRef.current = null;
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
      setWindowRange(desiredWindow);
      schedulePendingActionAttempt();
      return;
    }

    const key = action.request.key ?? getKey(data[targetIndex], targetIndex);
    const layout =
      rowLayoutsRef.current.get(key) ?? getClosestMeasuredLayout(targetIndex);
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
    scrollRef.current?.scrollTo?.({ y: targetY, animated: action.request.animated ?? false });
    metricsRef.current.offsetY = targetY;
    pendingScrollActionRef.current = null;
  }, [
    data,
    defaultAnchorAfterCount,
    defaultAnchorBeforeCount,
    findSourceIndexForRequest,
    getClosestMeasuredLayout,
    getKey,
    resolvedMaxWindowSize,
    schedulePendingActionAttempt,
    scrollActionTimeoutMs,
    windowRange.end,
    windowRange.start,
  ]);
  runPendingScrollActionRef.current = runPendingScrollAction;

  const captureAnchor = useCallback(async (): Promise<VisibleAnchor | null> => {
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
  }, []);

  const exposeHandle = useMemo(() => {
    return {
      scrollTo: (options: { y?: number; animated?: boolean }) => {
        scrollRef.current?.scrollTo?.(options);
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
        scrollRef.current?.scrollTo?.({ y: options.offset, animated: options.animated });
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
      scrollToItemAnchor: (request: ItemAnchorRequest) => {
        pendingScrollActionRef.current = {
          kind: 'itemAnchor',
          request,
          startedAtMs: Date.now(),
        };
        runPendingScrollActionRef.current();
      },
      getVisibleAnchor: captureAnchor,
      cancelPendingScrollAction: () => {
        if (pendingActionFrameRef.current != null) {
          cancelAnimationFrame(pendingActionFrameRef.current);
          pendingActionFrameRef.current = null;
        }
        pendingScrollActionRef.current = null;
      },
      getNativeScrollRef: () => scrollRef.current,
      getScrollableNode: () => scrollRef.current?.getScrollableNode?.(),
    };
  }, [captureAnchor]);

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
        clampWindow(current.start, current.end, data.length, resolvedMaxWindowSize),
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
  ]);

  const hasMoreAtTop = windowRange.start > 0;
  const hasMoreAtBottom = windowRange.end < data.length;
  const visibleItems = data.slice(windowRange.start, windowRange.end);

  const applyWindowChange = useCallback(
    async (nextStart: number, nextEnd: number) => {
      const anchor = await captureAnchor();
      const nextWindow = clampWindow(nextStart, nextEnd, data.length, resolvedMaxWindowSize);
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
        };
      }
      setWindowRange(nextWindow);
      schedulePendingActionAttempt();
    },
    [
      captureAnchor,
      data.length,
      defaultAnchorAfterCount,
      defaultAnchorBeforeCount,
      resolvedMaxWindowSize,
      schedulePendingActionAttempt,
    ],
  );

  const handleLoadMoreTop = useCallback(() => {
    const nextStart = Math.max(0, windowRange.start - resolvedPageSize);
    const nextEnd = Math.min(data.length, nextStart + resolvedMaxWindowSize);
    applyWindowChange(nextStart, nextEnd).catch(() => {});
  }, [
    applyWindowChange,
    data.length,
    resolvedMaxWindowSize,
    resolvedPageSize,
    windowRange.start,
  ]);

  const handleLoadMoreBottom = useCallback(() => {
    const nextEnd = Math.min(data.length, windowRange.end + resolvedPageSize);
    const nextStart = Math.max(0, nextEnd - resolvedMaxWindowSize);
    applyWindowChange(nextStart, nextEnd).catch(() => {});
  }, [
    applyWindowChange,
    data.length,
    resolvedMaxWindowSize,
    resolvedPageSize,
    windowRange.end,
  ]);

  const handleScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const nativeEvent = event.nativeEvent;
      metricsRef.current = {
        offsetY: Number(nativeEvent?.contentOffset?.y ?? 0),
        viewportHeight: Number(nativeEvent?.layoutMeasurement?.height ?? 0),
        contentHeight: Number(nativeEvent?.contentSize?.height ?? 0),
      };
      onScroll?.(event);
      if (!autoLoadEdges) {
        return;
      }
      if (metricsRef.current.offsetY <= edgeThresholdPx && hasMoreAtTop) {
        handleLoadMoreTop();
        return;
      }
      const bottomGap = Math.max(
        0,
        metricsRef.current.contentHeight -
          metricsRef.current.viewportHeight -
          metricsRef.current.offsetY,
      );
      if (bottomGap <= edgeThresholdPx && hasMoreAtBottom) {
        handleLoadMoreBottom();
      }
    },
    [
      autoLoadEdges,
      edgeThresholdPx,
      handleLoadMoreBottom,
      handleLoadMoreTop,
      hasMoreAtBottom,
      hasMoreAtTop,
      onScroll,
    ],
  );

  const handleContentSizeChange = useCallback(
    (width: number, height: number) => {
      metricsRef.current.contentHeight = height;
      onContentSizeChange?.(width, height);
      runPendingScrollActionRef.current();
    },
    [onContentSizeChange],
  );

  const handleLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? 0);
      metricsRef.current.viewportHeight = height;
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

  const renderedRows = visibleItems.map((item, localIndex) => {
    const sourceIndex = windowRange.start + localIndex;
    const { key, row } = getCachedRow(item, sourceIndex);
    if (!row) {
      return null;
    }
    mountedKeys.add(key);
    return (
      <React.Fragment key={key}>
        {localIndex > 0 && Separator ? (
          React.isValidElement(Separator) ? (
            Separator
          ) : (
            <View>{renderMaybeComponent(Separator)}</View>
          )
        ) : null}
        <View
          collapsable={false}
          onLayout={(event) => {
            const layout = event.nativeEvent?.layout;
            const y = Number(layout?.y ?? NaN);
            const height = Number(layout?.height ?? NaN);
            if (!Number.isFinite(y) || !Number.isFinite(height)) {
              return;
            }
            rowLayoutsRef.current.set(key, { y, height, sourceIndex });
            setLayoutVersion((version) => version + 1);
            runPendingScrollActionRef.current();
          }}
        >
          {row}
        </View>
      </React.Fragment>
    );
  });

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

  const header = renderMaybeComponent(ListHeaderComponent);
  const footer = renderMaybeComponent(ListFooterComponent);
  const empty = data.length === 0 ? renderMaybeComponent(ListEmptyComponent) : null;

  return (
    <ScrollView
      ref={scrollRef}
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
      {hasMoreAtTop ? (
        <View style={styles.loadMoreContainer}>
          <Pressable style={styles.loadMoreButton} onPress={handleLoadMoreTop}>
            <Text style={styles.loadMoreButtonText}>
              {windowRange.start} messages hidden above
            </Text>
          </Pressable>
        </View>
      ) : null}
      {empty}
      {renderedRows}
      {hasMoreAtBottom ? (
        <View style={styles.loadMoreContainer}>
          <Pressable style={styles.loadMoreButton} onPress={handleLoadMoreBottom}>
            <Text style={styles.loadMoreButtonText}>
              {data.length - windowRange.end} messages hidden below
            </Text>
          </Pressable>
        </View>
      ) : null}
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
  loadMoreButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#555555',
  },
});