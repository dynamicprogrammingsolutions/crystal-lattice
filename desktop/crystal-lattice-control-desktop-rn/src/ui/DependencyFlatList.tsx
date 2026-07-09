import React from 'react';
import { FlatList } from 'react-native';
import type { ViewToken } from 'react-native';

import type { PlaceholderFlatListProps } from './PlaceholderFlatList';

type DependencyFlatListRow = {
  key: string;
  value: React.ReactElement | null;
  sourceIndex: number;
};

type RowCacheEntry<TItem> = {
  item: TItem;
  deps: ReadonlyArray<unknown> | null;
  row: DependencyFlatListRow;
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

export function DependencyFlatList<TItem>(props: PlaceholderFlatListProps<TItem>): React.JSX.Element {
  const flatListRef = React.useRef<FlatList<DependencyFlatListRow> | null>(null);
  const cacheRef = React.useRef<Map<string, RowCacheEntry<TItem>>>(new Map());
  const lastExtraDataRef = React.useRef(props.extraData);
  const firstViewableAnchorRef = React.useRef<{
    key: string;
    sourceIndex: number;
    offsetFromViewportTop: number;
  } | null>(null);
  const pendingScrollToIndexRetryRef = React.useRef<{
    index: number;
    viewOffset: number;
    animated: boolean;
    attempts: number;
  } | null>(null);

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
    inverted,
    maintainVisibleContentPosition,
    scrollEventThrottle,
    disableVirtualization,
    initialNumToRender,
    maxToRenderPerBatch,
    updateCellsBatchingPeriod,
    windowSize,
    removeClippedSubviews,
    onLayout,
    onContentSizeChange,
    onScroll,
    onScrollBeginDrag,
    onScrollEndDrag,
    onMomentumScrollEnd,
    onViewableItemsChanged,
    viewabilityConfig,
    onScrollToIndexFailed,
  } = props;

  const cache = cacheRef.current;
  if (!Object.is(lastExtraDataRef.current, extraData)) {
    cache.clear();
    lastExtraDataRef.current = extraData;
  }

  const normalizedSeparatorComponent = React.useMemo(() => {
    if (!ItemSeparatorComponent) {
      return undefined;
    }
    if (React.isValidElement(ItemSeparatorComponent)) {
      const element = ItemSeparatorComponent;
      return () => element;
    }
    return ItemSeparatorComponent as React.ComponentType<any>;
  }, [ItemSeparatorComponent]);

  const keysInUse = new Set<string>();

  const rows = data.map((item, index) => {
    const key = keyExtractor ? keyExtractor(item, index) : String(index);
    keysInUse.add(key);

    const deps = getItemDependencies ? getItemDependencies(item, index) : null;

    const cached = cache.get(key);
    if (cached && cached.item === item && shallowArrayEqual(cached.deps, deps)) {
      cached.row.sourceIndex = index;
      return cached.row;
    }

    const value = renderItem({ item, index });
    const row: DependencyFlatListRow = { key, value, sourceIndex: index };
    cache.set(key, { item, deps, row });
    return row;
  });

  for (const cachedKey of cache.keys()) {
    if (!keysInUse.has(cachedKey)) {
      cache.delete(cachedKey);
    }
  }

  const extractRowKey = React.useCallback((row: DependencyFlatListRow) => row.key, []);
  const renderRow = React.useCallback(({ item }: { item: DependencyFlatListRow }) => item.value, []);
  const indexByKey = React.useMemo(() => {
    const next = new Map<string, number>();
    rows.forEach((row, index) => {
      next.set(row.key, index);
    });
    return next;
  }, [rows]);
  const combinedViewabilityConfig = React.useMemo(
    () => viewabilityConfig ?? { itemVisiblePercentThreshold: 1 },
    [viewabilityConfig],
  );
  const handleViewableItemsChanged = React.useRef(
    (info: { viewableItems: ViewToken[]; changed: ViewToken[] }) => {
      const first = info.viewableItems
        .filter((token) => token.isViewable && token.item)
        .sort((a, b) => (a.index ?? 0) - (b.index ?? 0))[0];
      const row = first?.item as DependencyFlatListRow | undefined;
      if (row && row.key.startsWith('msg-')) {
        firstViewableAnchorRef.current = {
          key: row.key,
          sourceIndex: row.sourceIndex,
          offsetFromViewportTop: 0,
        };
      }
      onViewableItemsChanged?.(info);
    },
  );
  handleViewableItemsChanged.current = (info) => {
    const first = info.viewableItems
      .filter((token) => token.isViewable && token.item)
      .sort((a, b) => (a.index ?? 0) - (b.index ?? 0))[0];
    const row = first?.item as DependencyFlatListRow | undefined;
    if (row && row.key.startsWith('msg-')) {
      firstViewableAnchorRef.current = {
        key: row.key,
        sourceIndex: row.sourceIndex,
        offsetFromViewportTop: 0,
      };
    }
    onViewableItemsChanged?.(info);
  };
  const onViewableItemsChangedStable = React.useCallback(
    (info: { viewableItems: ViewToken[]; changed: ViewToken[] }) =>
      handleViewableItemsChanged.current(info),
    [],
  );
  const retryPendingScrollToIndex = React.useCallback(() => {
    const pending = pendingScrollToIndexRetryRef.current;
    if (!pending) {
      return;
    }
    pendingScrollToIndexRetryRef.current = null;
    requestAnimationFrame(() => {
      flatListRef.current?.scrollToIndex?.({
        index: pending.index,
        animated: pending.animated,
        viewPosition: 0,
        viewOffset: pending.viewOffset,
      });
    });
  }, []);
  const handleScrollToIndexFailed = React.useCallback(
    (info: { index: number; highestMeasuredFrameIndex: number; averageItemLength: number }) => {
      onScrollToIndexFailed?.(info);
      const pending = pendingScrollToIndexRetryRef.current;
      if (pending && pending.attempts < 5) {
        pendingScrollToIndexRetryRef.current = {
          ...pending,
          attempts: pending.attempts + 1,
        };
        const approximateOffset = Math.max(
          0,
          Math.min(info.index, Math.max(0, info.highestMeasuredFrameIndex)) *
            Math.max(1, info.averageItemLength || 1),
        );
        flatListRef.current?.scrollToOffset?.({ offset: approximateOffset, animated: false });
        retryPendingScrollToIndex();
      }
    },
    [onScrollToIndexFailed, retryPendingScrollToIndex],
  );
  React.useImperativeHandle(
    listRef,
    () => ({
      scrollToOffset: (options: { offset: number; animated?: boolean }) =>
        flatListRef.current?.scrollToOffset?.(options),
      scrollToEnd: (options?: { animated?: boolean }) =>
        flatListRef.current?.scrollToEnd?.(options),
      scrollToIndex: (options: {
        index: number;
        animated?: boolean;
        viewPosition?: number;
        viewOffset?: number;
      }) => flatListRef.current?.scrollToIndex?.(options),
      getNativeScrollRef: () => flatListRef.current,
      getScrollableNode: () => flatListRef.current?.getScrollableNode?.(),
      getVisibleAnchor: async () => firstViewableAnchorRef.current,
      scrollToItemAnchor: (request: {
        key?: string;
        sourceIndex?: number;
        offsetFromViewportTop: number;
        animated?: boolean;
      }) => {
        const index =
          request.key != null
            ? indexByKey.get(request.key)
            : typeof request.sourceIndex === 'number'
              ? request.sourceIndex
              : undefined;
        if (index == null || index < 0 || index >= rows.length) {
          return;
        }
        const viewOffset = Math.max(0, request.offsetFromViewportTop);
        pendingScrollToIndexRetryRef.current = {
          index,
          viewOffset,
          animated: request.animated ?? false,
          attempts: 0,
        };
        flatListRef.current?.scrollToIndex?.({
          index,
          animated: request.animated ?? false,
          viewPosition: 0,
          viewOffset,
        });
      },
    }),
    [indexByKey, listRef, rows.length],
  );
  const diagnosticProps = {
    disableVirtualization,
    initialNumToRender,
    maxToRenderPerBatch,
    updateCellsBatchingPeriod,
    windowSize,
    removeClippedSubviews,
  } as any;

  return (
    <FlatList<DependencyFlatListRow>
      ref={flatListRef}
      style={style}
      contentContainerStyle={contentContainerStyle}
      data={rows}
      inverted={inverted}
      maintainVisibleContentPosition={maintainVisibleContentPosition}
      scrollEventThrottle={scrollEventThrottle}
      onLayout={onLayout}
      onContentSizeChange={onContentSizeChange}
      onScroll={onScroll}
      onScrollBeginDrag={onScrollBeginDrag}
      onScrollEndDrag={onScrollEndDrag}
      onMomentumScrollEnd={onMomentumScrollEnd}
      keyExtractor={extractRowKey}
      extraData={extraData}
      renderItem={renderRow}
      ListHeaderComponent={ListHeaderComponent}
      ListFooterComponent={ListFooterComponent}
      ListEmptyComponent={ListEmptyComponent}
      ItemSeparatorComponent={normalizedSeparatorComponent}
      onViewableItemsChanged={onViewableItemsChangedStable}
      viewabilityConfig={combinedViewabilityConfig}
      onScrollToIndexFailed={handleScrollToIndexFailed}
      {...diagnosticProps}
    />
  );
}
