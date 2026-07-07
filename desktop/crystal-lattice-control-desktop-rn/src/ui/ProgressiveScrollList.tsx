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
  const pendingAnchorRef = useRef<VisibleAnchor | null>(null);
  const pendingScrollToBottomRef = useRef(false);
  const metricsRef = useRef({ offsetY: 0, viewportHeight: 0, contentHeight: 0 });
  const [layoutVersion, setLayoutVersion] = useState(0);
  const [windowRange, setWindowRange] = useState(() =>
    getWindowForEnd(data.length, resolvedInitialWindowSize),
  );

  const exposeHandle = useMemo(() => {
    return {
      scrollTo: (options: { y?: number; animated?: boolean }) => {
        scrollRef.current?.scrollTo?.(options);
      },
      scrollToOffset: (options: { offset: number; animated?: boolean }) => {
        scrollRef.current?.scrollTo?.({ y: options.offset, animated: options.animated });
      },
      scrollToEnd: (options?: { animated?: boolean }) => {
        pendingScrollToBottomRef.current = true;
        setWindowRange(getWindowForEnd(data.length, resolvedMaxWindowSize));
        requestAnimationFrame(() => {
          scrollRef.current?.scrollToEnd?.({ animated: options?.animated ?? false });
        });
      },
      getNativeScrollRef: () => scrollRef.current,
      getScrollableNode: () => scrollRef.current?.getScrollableNode?.(),
    };
  }, [data.length, resolvedMaxWindowSize]);

  React.useImperativeHandle(listRef as React.Ref<any> | undefined, () => exposeHandle, [
    exposeHandle,
  ]);

  if (!Object.is(lastExtraDataRef.current, extraData)) {
    cacheRef.current.clear();
    lastExtraDataRef.current = extraData;
  }

  const getKey = useCallback(
    (item: TItem, index: number) => (keyExtractor ? keyExtractor(item, index) : String(index)),
    [keyExtractor],
  );

  const captureAnchor = useCallback(async (): Promise<VisibleAnchor | null> => {
    const metrics = await getMacScrollViewMetrics(exposeHandle);
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
  }, [exposeHandle]);

  const restoreAnchor = useCallback(() => {
    const anchor = pendingAnchorRef.current;
    if (!anchor) {
      return false;
    }

    let layout = rowLayoutsRef.current.get(anchor.key);
    if (!layout) {
      let closest: (RowLayout & { key: string }) | null = null;
      let closestDistance = Number.POSITIVE_INFINITY;
      for (const [key, candidate] of rowLayoutsRef.current.entries()) {
        const distance = Math.abs(candidate.sourceIndex - anchor.sourceIndex);
        if (distance < closestDistance) {
          closest = { ...candidate, key };
          closestDistance = distance;
        }
      }
      if (!closest) {
        return false;
      }
      layout = closest;
    }

    const maxOffsetY = Math.max(
      0,
      metricsRef.current.contentHeight - metricsRef.current.viewportHeight,
    );
    const targetY = Math.max(
      0,
      Math.min(maxOffsetY, layout.y - anchor.offsetFromViewportTop),
    );
    scrollRef.current?.scrollTo?.({ y: targetY, animated: false });
    metricsRef.current.offsetY = targetY;
    pendingAnchorRef.current = null;
    return true;
  }, []);

  useLayoutEffect(() => {
    if (pendingScrollToBottomRef.current) {
      pendingScrollToBottomRef.current = false;
      scrollRef.current?.scrollToEnd?.({ animated: false });
      return;
    }
    if (pendingAnchorRef.current) {
      restoreAnchor();
    }
  }, [layoutVersion, restoreAnchor, windowRange.start, windowRange.end]);

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
        pendingScrollToBottomRef.current = true;
        setWindowRange(getWindowForEnd(data.length, resolvedMaxWindowSize));
        return;
      }
      const anchor = await captureAnchor();
      if (cancelled) {
        return;
      }
      pendingAnchorRef.current = anchor;
      setWindowRange((current) =>
        clampWindow(current.start, current.end, data.length, resolvedMaxWindowSize),
      );
    };
    adjustForDataChange().catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [captureAnchor, data.length, edgeThresholdPx, resolvedMaxWindowSize]);

  const hasMoreAtTop = windowRange.start > 0;
  const hasMoreAtBottom = windowRange.end < data.length;
  const visibleItems = data.slice(windowRange.start, windowRange.end);

  const applyWindowChange = useCallback(
    async (nextStart: number, nextEnd: number) => {
      pendingAnchorRef.current = await captureAnchor();
      setWindowRange(clampWindow(nextStart, nextEnd, data.length, resolvedMaxWindowSize));
    },
    [captureAnchor, data.length, resolvedMaxWindowSize],
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
    },
    [onContentSizeChange],
  );

  const handleLayout = useCallback(
    (event: LayoutChangeEvent) => {
      const height = Number(event.nativeEvent?.layout?.height ?? 0);
      metricsRef.current.viewportHeight = height;
      onLayout?.(event);
    },
    [onLayout],
  );

  const cache = cacheRef.current;
  const keysInUse = new Set<string>();
  const Separator = ItemSeparatorComponent;
  const renderedRows = visibleItems.map((item, localIndex) => {
    const sourceIndex = windowRange.start + localIndex;
    const key = getKey(item, sourceIndex);
    const deps = getItemDependencies ? getItemDependencies(item, sourceIndex) : null;
    const cached = cache.get(key);
    let row: React.ReactElement | null;
    if (cached && cached.item === item && shallowArrayEqual(cached.deps, deps)) {
      row = cached.element;
    } else {
      row = renderItem({ item, index: sourceIndex } as ListRenderItemInfo<TItem>);
      cache.set(key, { item, deps, element: row });
    }
    if (!row) {
      return null;
    }
    keysInUse.add(key);
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
          }}
        >
          {row}
        </View>
      </React.Fragment>
    );
  });

  for (const cachedKey of cache.keys()) {
    if (!keysInUse.has(cachedKey)) {
      cache.delete(cachedKey);
    }
  }
  for (const layoutKey of rowLayoutsRef.current.keys()) {
    if (!keysInUse.has(layoutKey)) {
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
      onScrollBeginDrag={onScrollBeginDrag}
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