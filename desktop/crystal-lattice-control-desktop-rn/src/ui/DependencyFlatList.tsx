import React from 'react';
import { FlatList } from 'react-native';

import type { PlaceholderFlatListProps } from './PlaceholderFlatList';

type DependencyFlatListRow = {
  key: string;
  value: React.ReactElement | null;
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
  const cacheRef = React.useRef<Map<string, RowCacheEntry<TItem>>>(new Map());
  const lastExtraDataRef = React.useRef(props.extraData);

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
      return cached.row;
    }

    const value = renderItem({ item, index });
    const row: DependencyFlatListRow = { key, value };
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
      ref={listRef}
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
      {...diagnosticProps}
    />
  );
}
