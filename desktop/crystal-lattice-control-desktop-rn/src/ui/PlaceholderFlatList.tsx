import React from 'react';
import type { LayoutChangeEvent, NativeScrollEvent, NativeSyntheticEvent, StyleProp, ViewStyle } from 'react-native';
import { FlatList, ScrollView, View, VirtualizedList } from 'react-native';

export interface ListRenderItemInfo<TItem> {
  item: TItem;
  index: number;
}

export type PlaceholderFlatListImplementation = 'scrollView' | 'flatList' | 'virtualizedScroll';

/**
 * Placeholder FlatList-like component.
 *
 * We keep a FlatList-style API surface so we can swap in a real
 * virtualization implementation later (e.g. if RN macOS gains a
 * reliable/performant list).
 *
 * Default behavior: renders all items in a plain ScrollView.
 * Use `implementation` to switch to `FlatList` or `VirtualizedList`.
 */
export interface PlaceholderFlatListProps<TItem> {
  implementation?: PlaceholderFlatListImplementation;

  data: ReadonlyArray<TItem>;
  renderItem: (info: ListRenderItemInfo<TItem>) => React.ReactElement | null;
  keyExtractor?: (item: TItem, index: number) => string;

  /**
   * Optional per-item dependency array.
   *
   * If provided, cached rows are recomputed when either:
   * - the `item` object identity changes, or
   * - the dependency array changes (shallow compare via `Object.is`).
   *
   * This lets callers invalidate only specific rows even if `renderItem` is
   * recreated due to capturing external state (e.g. editing).
   */
  getItemDependencies?: (item: TItem, index: number) => ReadonlyArray<unknown>;

  style?: StyleProp<ViewStyle>;
  contentContainerStyle?: StyleProp<ViewStyle>;

  ListHeaderComponent?: React.ComponentType<any> | React.ReactElement | null;
  ListFooterComponent?: React.ComponentType<any> | React.ReactElement | null;
  ListEmptyComponent?: React.ComponentType<any> | React.ReactElement | null;
  ItemSeparatorComponent?: React.ComponentType<any> | React.ReactElement | null;

  extraData?: any;
  inverted?: boolean;
  maintainVisibleContentPosition?: any;

  scrollEventThrottle?: number;
  onLayout?: (event: LayoutChangeEvent) => void;
  onContentSizeChange?: (width: number, height: number) => void;
  onScroll?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
}

type RowCacheEntry<TItem> = {
  item: TItem;
  deps: ReadonlyArray<unknown> | null;
  row: PlaceholderFlatListRow;
};

type PlaceholderFlatListRow = {
  key: string;
  value: React.ReactElement | null;
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

export function PlaceholderFlatList<TItem>(props: PlaceholderFlatListProps<TItem>): React.JSX.Element {
  const cacheRef = React.useRef<Map<string, RowCacheEntry<TItem>>>(new Map());
  const lastExtraDataRef = React.useRef(props.extraData);

  const {
    implementation = 'virtualizedScroll',
    data,
    renderItem,
    keyExtractor,
    getItemDependencies,
    style,
    contentContainerStyle,
    ListHeaderComponent,
    ListFooterComponent,
    ListEmptyComponent,
    ItemSeparatorComponent,
    scrollEventThrottle,
    onLayout,
    onContentSizeChange,
    onScroll,
    extraData,
    inverted,
    maintainVisibleContentPosition,
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
    const row: PlaceholderFlatListRow = { key, value };
    cache.set(key, { item, deps, row });
    return row;
  });

  for (const cachedKey of cache.keys()) {
    if (!keysInUse.has(cachedKey)) {
      cache.delete(cachedKey);
    }
  }

  const extractRowKey = React.useCallback((row: PlaceholderFlatListRow) => row.key, []);
  const renderRow = React.useCallback(
    ({ item }: { item: PlaceholderFlatListRow }) => item.value,
    [],
  );

  if (implementation === 'flatList') {
    return (
      <FlatList<PlaceholderFlatListRow>
        style={style}
        contentContainerStyle={contentContainerStyle}
        data={rows}
        inverted={inverted}
        maintainVisibleContentPosition={maintainVisibleContentPosition}
        scrollEventThrottle={scrollEventThrottle}
        onLayout={onLayout}
        onContentSizeChange={onContentSizeChange}
        onScroll={onScroll}
        keyExtractor={extractRowKey}
        extraData={extraData}
        renderItem={renderRow}
        ListHeaderComponent={ListHeaderComponent}
        ListFooterComponent={ListFooterComponent}
        ListEmptyComponent={ListEmptyComponent}
        ItemSeparatorComponent={normalizedSeparatorComponent}
      />
    );
  }

  if (implementation === 'virtualizedScroll') {
    return (
      <VirtualizedList<PlaceholderFlatListRow>
        style={style}
        contentContainerStyle={contentContainerStyle}
        data={rows}
        inverted={inverted}
        maintainVisibleContentPosition={maintainVisibleContentPosition}
        scrollEventThrottle={scrollEventThrottle}
        onLayout={onLayout}
        onContentSizeChange={onContentSizeChange}
        onScroll={onScroll}
        keyExtractor={extractRowKey}
        extraData={extraData}
        renderItem={renderRow}
        getItemCount={(items) => items.length}
        getItem={(items, index) => items[index]}
        ListHeaderComponent={ListHeaderComponent}
        ListFooterComponent={ListFooterComponent}
        ListEmptyComponent={ListEmptyComponent}
        ItemSeparatorComponent={normalizedSeparatorComponent}
      />
    );
  }

  const header = renderMaybeComponent(ListHeaderComponent);
  const footer = renderMaybeComponent(ListFooterComponent);

  const empty = data.length === 0 ? renderMaybeComponent(ListEmptyComponent) : null;

  const Separator = ItemSeparatorComponent;

  const scrollRows = rows.map((row, index) => {
    if (!row.value) {
      return null;
    }

    return (
      <React.Fragment key={row.key}>
        {index > 0 && Separator ? (
          React.isValidElement(Separator) ? (
            Separator
          ) : (
            <View>{renderMaybeComponent(Separator)}</View>
          )
        ) : null}
        {row.value}
      </React.Fragment>
    );
  });

  return (
    <ScrollView
      style={style}
      contentContainerStyle={contentContainerStyle}
      scrollEventThrottle={scrollEventThrottle}
      onLayout={onLayout}
      onContentSizeChange={onContentSizeChange}
      onScroll={onScroll}
    >
      {header}
      {empty}
      {scrollRows}
      {footer}
    </ScrollView>
  );
}


