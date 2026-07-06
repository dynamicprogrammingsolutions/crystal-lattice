import React from 'react';
import type { LayoutChangeEvent, NativeScrollEvent, NativeSyntheticEvent, StyleProp, ViewStyle } from 'react-native';
import { ScrollView, View } from 'react-native';

export interface ListRenderItemInfo<TItem> {
  item: TItem;
  index: number;
}

/**
 * Placeholder FlatList-like component.
 *
 * We keep a FlatList-style API surface so we can swap in a real
 * virtualization implementation later (e.g. if RN macOS gains a
 * reliable/performant list).
 *
 * Current behavior: renders all items in a plain ScrollView.
 */
export interface PlaceholderFlatListProps<TItem> {
  data: ReadonlyArray<TItem>;
  renderItem: (info: ListRenderItemInfo<TItem>) => React.ReactElement | null;
  keyExtractor?: (item: TItem, index: number) => string;

  listRef?: React.Ref<any>;

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

  scrollEnabled?: boolean;
  showsVerticalScrollIndicator?: boolean;

  scrollEventThrottle?: number;
  disableVirtualization?: boolean;
  initialNumToRender?: number;
  maxToRenderPerBatch?: number;
  updateCellsBatchingPeriod?: number;
  windowSize?: number;
  removeClippedSubviews?: boolean;
  onLayout?: (event: LayoutChangeEvent) => void;
  onContentSizeChange?: (width: number, height: number) => void;
  onScroll?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollEndDrag?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollEnd?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
}

type RowCacheEntry<TItem> = {
  item: TItem;
  deps: ReadonlyArray<unknown> | null;
  element: React.ReactElement | null;
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
  const debugEnabled =
    (globalThis as any).CLC_DEBUG_SCROLL_PERSIST === true ||
    (globalThis as any).CLC_DEBUG_SCROLL_PERSIST === 'true';
  const lastScrollDebugAtRef = React.useRef(0);

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
    scrollEventThrottle,
    onLayout,
    onContentSizeChange,
    onScroll,
    onScrollEndDrag,
    onMomentumScrollEnd,
    scrollEnabled,
    showsVerticalScrollIndicator,
  } = props;

  const wrapScrollHandler = React.useCallback(
    (
      kind: 'scroll' | 'endDrag' | 'momentumEnd',
      handler?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void,
    ) => {
      if (!debugEnabled && !handler) {
        return undefined;
      }
      return (event: NativeSyntheticEvent<NativeScrollEvent>) => {
        if (debugEnabled) {
          const now = Date.now();
          if (now - lastScrollDebugAtRef.current > 500) {
            lastScrollDebugAtRef.current = now;
            console.log('[PlaceholderFlatList] scroll event', {
              kind,
              hasNativeEvent: !!event?.nativeEvent,
              contentOffset: (event as any)?.nativeEvent?.contentOffset,
            });
          }
        }
        handler?.(event);
      };
    },
    [debugEnabled],
  );

  const cache = cacheRef.current;
  if (!Object.is(lastExtraDataRef.current, props.extraData)) {
    cache.clear();
    lastExtraDataRef.current = props.extraData;
  }

  const header = renderMaybeComponent(ListHeaderComponent);
  const footer = renderMaybeComponent(ListFooterComponent);

  const empty = data.length === 0 ? renderMaybeComponent(ListEmptyComponent) : null;

  const Separator = ItemSeparatorComponent;

  const keysInUse = new Set<string>();

  const rows = data.map((item, index) => {
    const key = keyExtractor ? keyExtractor(item, index) : String(index);
    keysInUse.add(key);

    const deps = getItemDependencies ? getItemDependencies(item, index) : null;

    const cached = cache.get(key);
    let row: React.ReactElement | null;
    if (cached && cached.item === item && shallowArrayEqual(cached.deps, deps)) {
      row = cached.element;
    } else {
      row = renderItem({ item, index });
      cache.set(key, { item, deps, element: row });
    }

    if (!row) {
      return null;
    }

    return (
      <React.Fragment key={key}>
        {index > 0 && Separator ? (
          React.isValidElement(Separator) ? (
            Separator
          ) : (
            <View>{renderMaybeComponent(Separator)}</View>
          )
        ) : null}
        {row}
      </React.Fragment>
    );
  });

  for (const cachedKey of cache.keys()) {
    if (!keysInUse.has(cachedKey)) {
      cache.delete(cachedKey);
    }
  }

  return (
    <ScrollView
      ref={listRef}
      style={style}
      contentContainerStyle={contentContainerStyle}
      scrollEventThrottle={scrollEventThrottle}
      onLayout={onLayout}
      onContentSizeChange={onContentSizeChange}
      onScroll={wrapScrollHandler('scroll', onScroll)}
      onScrollEndDrag={wrapScrollHandler('endDrag', onScrollEndDrag)}
      onMomentumScrollEnd={wrapScrollHandler('momentumEnd', onMomentumScrollEnd)}
      scrollEnabled={scrollEnabled}
      showsVerticalScrollIndicator={showsVerticalScrollIndicator ?? true}
    >
      {header}
      {empty}
      {rows}
      {footer}
    </ScrollView>
  );
}


