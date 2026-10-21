import React from "react";
import type {
  FlatList,
  FlatListProps,
  LayoutChangeEvent,
  NativeScrollEvent,
  NativeSyntheticEvent,
  StyleProp,
  ViewToken,
  ViewStyle,
} from "react-native";
import { FlatList as NativeFlatList, View } from "react-native";

import {
  DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY,
  type TranscriptAnchorStrategy,
} from "../transcriptAnchorStrategy";
import {
  createSingleFlightAnchorRetryController,
  type TranscriptAnchorDiagnostic,
} from "./transcriptAnchorRetry";

export interface DependencyFlatListRenderItemInfo<TItem> {
  item: TItem;
  index: number;
}

export interface DependencyFlatListProps<TItem> {
  data: ReadonlyArray<TItem>;
  renderItem: (
    info: DependencyFlatListRenderItemInfo<TItem>
  ) => React.ReactElement | null;
  keyExtractor?: (item: TItem, index: number) => string;

  getItemDependencies?: (item: TItem, index: number) => ReadonlyArray<unknown>;

  style?: StyleProp<ViewStyle>;
  contentContainerStyle?: StyleProp<ViewStyle>;
  testID?: string;
  keyboardDismissMode?: FlatListProps<TItem>["keyboardDismissMode"];
  keyboardShouldPersistTaps?: FlatListProps<TItem>["keyboardShouldPersistTaps"];

  ListHeaderComponent?: React.ComponentType<any> | React.ReactElement | null;
  ListFooterComponent?: React.ComponentType<any> | React.ReactElement | null;
  ListEmptyComponent?: React.ComponentType<any> | React.ReactElement | null;
  ItemSeparatorComponent?: React.ComponentType<any> | React.ReactElement | null;

  extraData?: any;
  inverted?: boolean;
  maintainVisibleContentPosition?: any;
  anchorStrategy?: TranscriptAnchorStrategy;
  onAnchorDiagnostic?: (diagnostic: TranscriptAnchorDiagnostic) => void;

  scrollEventThrottle?: number;
  onLayout?: (event: LayoutChangeEvent) => void;
  onContentSizeChange?: (width: number, height: number) => void;
  onScroll?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollBeginDrag?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onScrollEndDrag?: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
  onMomentumScrollEnd?: (
    event: NativeSyntheticEvent<NativeScrollEvent>
  ) => void;
  onScrollToIndexFailed?: (info: {
    index: number;
    highestMeasuredFrameIndex: number;
    averageItemLength: number;
  }) => void;
}

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
  b: ReadonlyArray<unknown> | null
): boolean {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) {
    if (!Object.is(a[i], b[i])) return false;
  }
  return true;
}

function DependencyFlatListInner<TItem>(
  props: DependencyFlatListProps<TItem>,
  ref: React.ForwardedRef<FlatList<any>>
): React.JSX.Element {
  const cacheRef = React.useRef<Map<string, RowCacheEntry<TItem>>>(new Map());
  const lastExtraDataRef = React.useRef(props.extraData);
  const flatListRef = React.useRef<FlatList<DependencyFlatListRow> | null>(
    null
  );
  const rowRefsRef = React.useRef<Map<string, any>>(new Map());
  const visibleMessageKeysRef = React.useRef<string[]>([]);
  const pendingV1AnchorRef = React.useRef<{
    key: string;
    offsetFromViewportTop: number;
    attempts: number;
    deadlineMs: number;
  } | null>(null);
  const v1AnchorTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(
    null
  );
  const scrollMetricsRef = React.useRef({
    offsetY: 0,
    viewportHeight: 0,
    contentHeight: 0,
  });
  const indexByKeyRef = React.useRef(new Map<string, number>());
  const invertedRef = React.useRef(false);
  const measureItemViewportOffsetRef = React.useRef<
    (key: string) => Promise<number | null>
  >(() => Promise.resolve(null));
  const onAnchorDiagnosticRef = React.useRef<
    ((diagnostic: TranscriptAnchorDiagnostic) => void) | undefined
  >(props.onAnchorDiagnostic);
  const singleFlightFallbackOffsetRef = React.useRef<number | null>(null);

  const {
    data,
    renderItem,
    keyExtractor,
    getItemDependencies,
    style,
    contentContainerStyle,
    testID,
    keyboardDismissMode,
    keyboardShouldPersistTaps,
    ListHeaderComponent,
    ListFooterComponent,
    ListEmptyComponent,
    ItemSeparatorComponent,
    extraData,
    inverted,
    maintainVisibleContentPosition,
    anchorStrategy = DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY,
    onAnchorDiagnostic,
    scrollEventThrottle,
    onLayout,
    onContentSizeChange,
    onScroll,
    onScrollBeginDrag,
    onScrollEndDrag,
    onMomentumScrollEnd,
    onScrollToIndexFailed,
  } = props;
  invertedRef.current = inverted === true;
  onAnchorDiagnosticRef.current = onAnchorDiagnostic;

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
    if (
      cached &&
      cached.item === item &&
      shallowArrayEqual(cached.deps, deps)
    ) {
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

  const extractRowKey = React.useCallback(
    (row: DependencyFlatListRow) => row.key,
    []
  );
  const renderRow = React.useCallback(
    ({ item }: { item: DependencyFlatListRow }) => (
      <View
        ref={(node) => {
          if (node) {
            rowRefsRef.current.set(item.key, node);
          } else {
            rowRefsRef.current.delete(item.key);
          }
        }}
        collapsable={false}
      >
        {item.value}
      </View>
    ),
    []
  );
  const indexByKey = React.useMemo(() => {
    const next = new Map<string, number>();
    rows.forEach((row, index) => next.set(row.key, index));
    return next;
  }, [rows]);
  indexByKeyRef.current = indexByKey;
  const measureWindowY = React.useCallback(
    (node: any): Promise<number | null> => {
      if (!node || typeof node.measureInWindow !== "function") {
        return Promise.resolve(null);
      }
      return new Promise((resolve) => {
        try {
          node.measureInWindow((_x: number, y: number) => {
            resolve(Number.isFinite(y) ? y : null);
          });
        } catch {
          resolve(null);
        }
      });
    },
    []
  );
  const measureItemViewportOffset = React.useCallback(
    async (key: string): Promise<number | null> => {
      const row = rowRefsRef.current.get(key);
      const nativeScroll =
        (flatListRef.current as any)?.getNativeScrollRef?.() ??
        flatListRef.current;
      const [rowY, viewportY] = await Promise.all([
        measureWindowY(row),
        measureWindowY(nativeScroll),
      ]);
      return rowY == null || viewportY == null ? null : rowY - viewportY;
    },
    [measureWindowY]
  );
  measureItemViewportOffsetRef.current = measureItemViewportOffset;
  const singleFlightAnchorController = React.useMemo(
    () =>
      createSingleFlightAnchorRetryController({
        now: Date.now,
        requestFrame: (callback) => requestAnimationFrame(callback),
        cancelFrame: (handle) => cancelAnimationFrame(handle as number),
        setTimer: (callback, delayMs) => setTimeout(callback, delayMs),
        clearTimer: (handle) =>
          clearTimeout(handle as ReturnType<typeof setTimeout>),
        measure: (key) => measureItemViewportOffsetRef.current(key),
        applyCorrection: (operation, actualOffset) => {
          const index = indexByKeyRef.current.get(operation.key);
          if (index == null) {
            return;
          }
          if (actualOffset == null) {
            flatListRef.current?.scrollToIndex({
              index,
              animated: false,
              viewPosition: 0,
            });
            return;
          }
          const metrics = scrollMetricsRef.current;
          const maxOffsetY = Math.max(
            0,
            metrics.contentHeight - metrics.viewportHeight
          );
          const visualError = actualOffset - operation.offsetFromViewportTop;
          const correction = invertedRef.current ? -visualError : visualError;
          flatListRef.current?.scrollToOffset({
            offset: Math.max(
              0,
              Math.min(maxOffsetY, metrics.offsetY + correction)
            ),
            animated: false,
          });
        },
        onDiagnostic: (diagnostic) => {
          if (diagnostic.event === "anchorStopped") {
            const fallbackOffset = singleFlightFallbackOffsetRef.current;
            if (fallbackOffset != null) {
              flatListRef.current?.scrollToOffset({
                offset: fallbackOffset,
                animated: false,
              });
            }
          }
          if (
            diagnostic.event === "anchorCompleted" ||
            diagnostic.event === "anchorStopped" ||
            diagnostic.event === "anchorCancelled"
          ) {
            singleFlightFallbackOffsetRef.current = null;
          }
          onAnchorDiagnosticRef.current?.(diagnostic);
        },
        timeoutMs: 5000,
        maxAttempts: 30,
        tolerancePx: 8,
        retryDelayMs: 50,
      }),
    []
  );
  const clearV1AnchorTimer = React.useCallback(() => {
    if (v1AnchorTimerRef.current != null) {
      clearTimeout(v1AnchorTimerRef.current);
      v1AnchorTimerRef.current = null;
    }
  }, []);
  const cancelV1PendingAnchor = React.useCallback(() => {
    clearV1AnchorTimer();
    pendingV1AnchorRef.current = null;
  }, [clearV1AnchorTimer]);
  const cancelPendingAnchor = React.useCallback(
    (reason = "cancelled") => {
      cancelV1PendingAnchor();
      singleFlightAnchorController.cancel(reason);
    },
    [cancelV1PendingAnchor, singleFlightAnchorController]
  );
  React.useEffect(
    () => () => {
      clearV1AnchorTimer();
      singleFlightAnchorController.cancel("unmount");
    },
    [clearV1AnchorTimer, singleFlightAnchorController]
  );
  const retryV1AnchorRef = React.useRef<() => void>(() => {});
  const retryV1Anchor = React.useCallback(() => {
    const pending = pendingV1AnchorRef.current;
    if (!pending) {
      return;
    }
    requestAnimationFrame(() => {
      if (pendingV1AnchorRef.current !== pending) {
        return;
      }
      measureItemViewportOffset(pending.key).then((actualOffset) => {
        if (pendingV1AnchorRef.current !== pending) {
          return;
        }
        if (
          actualOffset != null &&
          Math.abs(actualOffset - pending.offsetFromViewportTop) <= 8
        ) {
          cancelV1PendingAnchor();
          return;
        }
        if (Date.now() >= pending.deadlineMs || pending.attempts >= 80) {
          cancelV1PendingAnchor();
          return;
        }
        pendingV1AnchorRef.current = {
          ...pending,
          attempts: pending.attempts + 1,
        };
        const index = indexByKey.get(pending.key);
        if (index == null || actualOffset == null) {
          if (index != null) {
            flatListRef.current?.scrollToIndex({
              index,
              animated: false,
              viewPosition: 0,
            });
          }
          clearV1AnchorTimer();
          v1AnchorTimerRef.current = setTimeout(() => {
            v1AnchorTimerRef.current = null;
            retryV1AnchorRef.current();
          }, 50);
          return;
        }
        const metrics = scrollMetricsRef.current;
        const maxOffsetY = Math.max(
          0,
          metrics.contentHeight - metrics.viewportHeight
        );
        const visualError = actualOffset - pending.offsetFromViewportTop;
        const correction = inverted ? -visualError : visualError;
        flatListRef.current?.scrollToOffset({
          offset: Math.max(
            0,
            Math.min(maxOffsetY, metrics.offsetY + correction)
          ),
          animated: false,
        });
        clearV1AnchorTimer();
        v1AnchorTimerRef.current = setTimeout(
          () => {
            v1AnchorTimerRef.current = null;
            retryV1AnchorRef.current();
          },
          pending.attempts === 0 ? 100 : 50
        );
      });
    });
  }, [
    cancelV1PendingAnchor,
    clearV1AnchorTimer,
    indexByKey,
    inverted,
    measureItemViewportOffset,
  ]);
  retryV1AnchorRef.current = retryV1Anchor;
  React.useEffect(() => {
    if (anchorStrategy === "mobile-anchor-v1" && pendingV1AnchorRef.current) {
      retryV1AnchorRef.current();
    }
    if (anchorStrategy === "single-flight-anchor") {
      singleFlightAnchorController.notifyLayoutChanged();
    }
  }, [anchorStrategy, rows, singleFlightAnchorController]);
  React.useEffect(() => {
    if (anchorStrategy !== "mobile-anchor-v1") {
      cancelV1PendingAnchor();
    }
    if (anchorStrategy !== "single-flight-anchor") {
      singleFlightAnchorController.cancel("strategyChanged");
    }
  }, [anchorStrategy, cancelV1PendingAnchor, singleFlightAnchorController]);
  const handleViewableItemsChanged = React.useRef(
    (info: { viewableItems: ViewToken[] }) => {
      visibleMessageKeysRef.current = info.viewableItems
        .filter((token) => token.isViewable && token.item)
        .map((token) => token.item as DependencyFlatListRow)
        .filter((row) => row.key.startsWith("msg-"))
        .map((row) => row.key);
    }
  );
  React.useImperativeHandle(
    ref,
    () =>
      ({
        scrollToOffset: (options: { offset: number; animated?: boolean }) => {
          cancelPendingAnchor();
          flatListRef.current?.scrollToOffset(options);
        },
        scrollToEnd: (options?: { animated?: boolean }) => {
          cancelPendingAnchor();
          flatListRef.current?.scrollToEnd(options);
        },
        scrollToIndex: (options: {
          index: number;
          animated?: boolean;
          viewPosition?: number;
          viewOffset?: number;
        }) => {
          cancelPendingAnchor();
          flatListRef.current?.scrollToIndex(options);
        },
        getVisibleMessageAnchors: async () => {
          const measured = await Promise.all(
            visibleMessageKeysRef.current.map(async (key) => ({
              key,
              offsetFromViewportTop: await measureItemViewportOffset(key),
            }))
          );
          return measured
            .filter(
              (item): item is { key: string; offsetFromViewportTop: number } =>
                item.offsetFromViewportTop != null
            )
            .sort(
              (left, right) =>
                left.offsetFromViewportTop - right.offsetFromViewportTop
            );
        },
        scrollToMessageAnchor: (request: {
          key: string;
          offsetFromViewportTop: number;
        }) => {
          cancelPendingAnchor("replaced");
          if (anchorStrategy === "simple-reload") {
            return;
          }
          if (anchorStrategy === "mobile-anchor-v1") {
            pendingV1AnchorRef.current = {
              key: request.key,
              offsetFromViewportTop: request.offsetFromViewportTop,
              attempts: 0,
              deadlineMs: Date.now() + 15000,
            };
            retryV1AnchorRef.current();
            return;
          }
          singleFlightFallbackOffsetRef.current =
            scrollMetricsRef.current.offsetY;
          singleFlightAnchorController.start(request);
        },
        cancelMessageAnchor: () => cancelPendingAnchor("cancelled"),
      } as any),
    [
      anchorStrategy,
      cancelPendingAnchor,
      measureItemViewportOffset,
      singleFlightAnchorController,
    ]
  );
  const handleScrollBeginDragWithAnchorCancellation = React.useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      cancelPendingAnchor("userNavigation");
      onScrollBeginDrag?.(event);
    },
    [cancelPendingAnchor, onScrollBeginDrag]
  );
  const handleScrollWithMetrics = React.useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      scrollMetricsRef.current = {
        offsetY: Number(event.nativeEvent?.contentOffset?.y ?? 0),
        viewportHeight: Number(
          event.nativeEvent?.layoutMeasurement?.height ?? 0
        ),
        contentHeight: Number(event.nativeEvent?.contentSize?.height ?? 0),
      };
      onScroll?.(event);
    },
    [onScroll]
  );
  const handleLayoutWithMetrics = React.useCallback(
    (event: LayoutChangeEvent) => {
      scrollMetricsRef.current.viewportHeight = Number(
        event.nativeEvent?.layout?.height ?? 0
      );
      onLayout?.(event);
    },
    [onLayout]
  );
  const handleContentSizeChangeWithMetrics = React.useCallback(
    (width: number, height: number) => {
      scrollMetricsRef.current.contentHeight = Number(height ?? 0);
      onContentSizeChange?.(width, height);
    },
    [onContentSizeChange]
  );
  const handleScrollToIndexFailedWithAnchorRetry = React.useCallback(
    (info: {
      index: number;
      highestMeasuredFrameIndex: number;
      averageItemLength: number;
    }) => {
      const pendingV1 = pendingV1AnchorRef.current;
      if (anchorStrategy === "mobile-anchor-v1" && pendingV1) {
        const index = indexByKey.get(pendingV1.key) ?? info.index;
        flatListRef.current?.scrollToOffset({
          offset: Math.max(0, info.averageItemLength * index),
          animated: false,
        });
        clearV1AnchorTimer();
        v1AnchorTimerRef.current = setTimeout(() => {
          v1AnchorTimerRef.current = null;
          retryV1AnchorRef.current();
        }, 100);
      }
      if (anchorStrategy === "single-flight-anchor") {
        const pending = singleFlightAnchorController.getPending();
        if (pending) {
          const index = indexByKey.get(pending.key) ?? info.index;
          flatListRef.current?.scrollToOffset({
            offset: Math.max(0, info.averageItemLength * index),
            animated: false,
          });
          singleFlightAnchorController.notifyLayoutChanged();
        }
      }
      onScrollToIndexFailed?.(info);
    },
    [
      anchorStrategy,
      clearV1AnchorTimer,
      indexByKey,
      onScrollToIndexFailed,
      singleFlightAnchorController,
    ]
  );

  return (
    <NativeFlatList<DependencyFlatListRow>
      keyboardDismissMode={keyboardDismissMode}
      keyboardShouldPersistTaps={keyboardShouldPersistTaps}
      style={style}
      ref={flatListRef}
      contentContainerStyle={contentContainerStyle}
      testID={testID}
      data={rows}
      inverted={inverted}
      maintainVisibleContentPosition={maintainVisibleContentPosition}
      scrollEventThrottle={scrollEventThrottle}
      onLayout={handleLayoutWithMetrics}
      onContentSizeChange={handleContentSizeChangeWithMetrics}
      onScroll={handleScrollWithMetrics}
      onScrollBeginDrag={handleScrollBeginDragWithAnchorCancellation}
      onScrollEndDrag={onScrollEndDrag}
      onMomentumScrollEnd={onMomentumScrollEnd}
      onScrollToIndexFailed={handleScrollToIndexFailedWithAnchorRetry}
      onViewableItemsChanged={handleViewableItemsChanged.current}
      viewabilityConfig={{ itemVisiblePercentThreshold: 1 }}
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

export const DependencyFlatList = React.forwardRef(DependencyFlatListInner) as <
  TItem
>(
  props: DependencyFlatListProps<TItem> & React.RefAttributes<FlatList<any>>
) => React.JSX.Element;
