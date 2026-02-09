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

  const header = renderMaybeComponent(ListHeaderComponent);
  const footer = renderMaybeComponent(ListFooterComponent);

  const empty = data.length === 0 ? renderMaybeComponent(ListEmptyComponent) : null;

  const Separator = ItemSeparatorComponent;

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
      {data.map((item, index) => {
        const key = keyExtractor ? keyExtractor(item, index) : String(index);
        const row = renderItem({ item, index });
        if (!row) {
          return null;
        }

        return (
          <React.Fragment key={key}>
            {index > 0 && Separator ? (
              React.isValidElement(Separator) ? (
                Separator
              ) : (
                <View>
                  {renderMaybeComponent(Separator)}
                </View>
              )
            ) : null}
            {row}
          </React.Fragment>
        );
      })}
      {footer}
    </ScrollView>
  );
}
