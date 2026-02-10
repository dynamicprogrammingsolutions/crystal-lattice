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
  element: React.ReactElement | null;
};

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
  const lastRenderItemRef = React.useRef(props.renderItem);
  const lastKeyExtractorRef = React.useRef(props.keyExtractor);
  const lastExtraDataRef = React.useRef(props.extraData);

  const {
    data,
    renderItem,
    keyExtractor,
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
  } = props;

  const cache = cacheRef.current;
  if (lastRenderItemRef.current !== renderItem) {
    console.log('PlaceholderFlatList: renderItem function changed, clearing cache');
    cache.clear();
    lastRenderItemRef.current = renderItem;
  }
  /*if (lastKeyExtractorRef.current !== keyExtractor) {
    console.log('PlaceholderFlatList: keyExtractor function changed, clearing cache');
    cache.clear();
    lastKeyExtractorRef.current = keyExtractor;
  }*/
  if (!Object.is(lastExtraDataRef.current, props.extraData)) {
    console.log('PlaceholderFlatList: extraData changed, clearing cache');
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

    const cached = cache.get(key);
    let row: React.ReactElement | null;
    if (cached && cached.item === item) {
      row = cached.element;
    } else {
      console.log(`PlaceholderFlatList: rendering item at index ${index} with key ${key}`);
      row = renderItem({ item, index });
      cache.set(key, { item, element: row });
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
      style={style}
      contentContainerStyle={contentContainerStyle}
      scrollEventThrottle={scrollEventThrottle}
      onLayout={onLayout}
      onContentSizeChange={onContentSizeChange}
      onScroll={onScroll}
    >
      {header}
      {empty}
      {rows}
      {footer}
    </ScrollView>
  );
}


