import React from 'react';
import { FlatList, View } from 'react-native';
import type { ViewToken } from 'react-native';

import { getMacScrollViewMetrics } from '../native/MacScrollViewMetrics';
import { resolveFlatListRenderTuning } from './flatListRenderTuning';
import type { PlaceholderFlatListProps } from './PlaceholderFlatList';

type DependencyFlatListRow = {
  key: string;
  value: React.ReactElement | null;
  sourceIndex: number;
};

type VisibleAnchor = {
  key: string;
  sourceIndex: number;
  offsetFromViewportTop: number;
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
  const rowRefsRef = React.useRef<Map<string, any>>(new Map());
  const viewableAnchorsRef = React.useRef<Array<{ key: string; sourceIndex: number }>>([]);
  const pendingScrollToIndexRetryRef = React.useRef<{
    index: number;
    viewOffset: number;
    animated: boolean;
    attempts: number;
    startedAtMs: number;
    deadlineMs: number;
  } | null>(null);
  const pendingItemAnchorRef = React.useRef<{
    key: string;
    index: number;
    viewOffset: number;
    animated: boolean;
    attempts: number;
    startedAtMs: number;
    deadlineMs: number;
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
    eagerRenderThreshold,
    eagerRenderEligibilityCount,
    itemAnchorTimeoutMs = 3000,
    itemAnchorMaxAttempts = 50,
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
    onMomentumScrollBegin,
    onMomentumScrollEnd,
    onViewableItemsChanged,
    viewabilityConfig,
    onScrollToIndexFailed,
    onScrollActionDiagnostic,
  } = props;
  const resolvedItemAnchorTimeoutMs = Math.max(1, Math.round(itemAnchorTimeoutMs));
  const resolvedItemAnchorMaxAttempts = Math.max(1, Math.round(itemAnchorMaxAttempts));
  const renderTuning = React.useMemo(
    () =>
      resolveFlatListRenderTuning({
        rowCount: data.length,
        eagerRenderEligibilityCount,
        eagerRenderThreshold,
        initialNumToRender,
        maxToRenderPerBatch,
        updateCellsBatchingPeriod,
        removeClippedSubviews,
      }),
    [
      data.length,
      eagerRenderEligibilityCount,
      eagerRenderThreshold,
      initialNumToRender,
      maxToRenderPerBatch,
      removeClippedSubviews,
      updateCellsBatchingPeriod,
    ],
  );

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
  const getNativeScrollTarget = React.useCallback(() => {
    return (
      (flatListRef.current as any)?.getNativeScrollRef?.() ??
      flatListRef.current?.getScrollableNode?.() ??
      flatListRef.current
    );
  }, []);
  const measureItemViewportOffset = React.useCallback(
    (key: string): Promise<number | null> => {
      const rowRef = rowRefsRef.current.get(key);
      const nativeScrollRef = getNativeScrollTarget();
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
              getMacScrollViewMetrics(flatListRef.current)
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
    [getNativeScrollTarget],
  );
  const captureVisibleAnchor = React.useCallback(async (): Promise<VisibleAnchor | null> => {
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
  }, [measureItemViewportOffset]);
  const emitScrollActionDiagnostic = React.useCallback(
    (event: string, reason?: string, details?: Record<string, unknown>) => {
      onScrollActionDiagnostic?.({ event, reason, details });
    },
    [onScrollActionDiagnostic],
  );
  const finishPendingItemAnchor = React.useCallback(
    (
      event: 'listAnchorCompleted' | 'listAnchorStopped',
      reason: string,
      pending = pendingItemAnchorRef.current,
      details?: Record<string, unknown>,
    ) => {
      if (!pending) {
        return;
      }
      pendingItemAnchorRef.current = null;
      pendingScrollToIndexRetryRef.current = null;
      emitScrollActionDiagnostic(event, reason, {
        key: pending.key,
        index: pending.index,
        attempts: pending.attempts,
        durationMs: Math.max(0, Date.now() - pending.startedAtMs),
        ...details,
      });
    },
    [emitScrollActionDiagnostic],
  );
  const retryItemAnchor = React.useCallback(() => {
    const pending = pendingItemAnchorRef.current;
    if (!pending) {
      return;
    }
    requestAnimationFrame(() => {
      const current = pendingItemAnchorRef.current;
      if (current !== pending) {
        return;
      }
      measureItemViewportOffset(pending.key).then((actualOffset) => {
        if (pendingItemAnchorRef.current !== pending) {
          return;
        }
        if (
          typeof actualOffset === 'number' &&
          Math.abs(actualOffset - pending.viewOffset) <= 4
        ) {
          finishPendingItemAnchor('listAnchorCompleted', 'stable', pending, {
            requestedOffset: Math.round(pending.viewOffset),
            actualOffset: Math.round(actualOffset),
          });
          return;
        }
        const now = Date.now();
        if (now > pending.deadlineMs) {
          finishPendingItemAnchor('listAnchorStopped', 'deadline', pending, {
            timeoutMs: resolvedItemAnchorTimeoutMs,
            actualOffset:
              typeof actualOffset === 'number' ? Math.round(actualOffset) : null,
          });
          return;
        }
        if (pending.attempts >= resolvedItemAnchorMaxAttempts) {
          finishPendingItemAnchor('listAnchorStopped', 'maxAttempts', pending, {
            maxAttempts: resolvedItemAnchorMaxAttempts,
            actualOffset:
              typeof actualOffset === 'number' ? Math.round(actualOffset) : null,
          });
          return;
        }
        const nextPending = {
          ...pending,
          attempts: pending.attempts + 1,
        };
        pendingItemAnchorRef.current = nextPending;
        if (nextPending.attempts === 1 || nextPending.attempts % 10 === 0) {
          emitScrollActionDiagnostic('listAnchorProgress', 'retry', {
            key: nextPending.key,
            index: nextPending.index,
            attempts: nextPending.attempts,
            elapsedMs: Math.max(0, now - nextPending.startedAtMs),
            actualOffset:
              typeof actualOffset === 'number' ? Math.round(actualOffset) : null,
          });
        }
        const issueIndexRetry = () => {
          if (pendingItemAnchorRef.current !== nextPending) {
            return;
          }
          flatListRef.current?.scrollToIndex?.({
            index: pending.index,
            animated: false,
            viewPosition: 0,
            viewOffset: pending.viewOffset,
          });
          retryItemAnchor();
        };
        if (actualOffset == null) {
          getMacScrollViewMetrics(flatListRef.current)
            .then((metrics) => {
              if (pendingItemAnchorRef.current !== nextPending) {
                return;
              }
              if (metrics && rows.length > 1) {
                const maxOffsetY = Math.max(0, metrics.contentHeight - metrics.viewportHeight);
                const ratio = Math.max(0, Math.min(1, pending.index / (rows.length - 1)));
                flatListRef.current?.scrollToOffset?.({
                  offset: Math.round(maxOffsetY * ratio),
                  animated: false,
                });
              }
              setTimeout(issueIndexRetry, 100);
            })
            .catch(() => setTimeout(issueIndexRetry, 100));
          return;
        }
        issueIndexRetry();
      });
    });
  }, [
    emitScrollActionDiagnostic,
    finishPendingItemAnchor,
    measureItemViewportOffset,
    resolvedItemAnchorMaxAttempts,
    resolvedItemAnchorTimeoutMs,
    rows.length,
  ]);
  const renderRow = React.useCallback(
    ({ item }: { item: DependencyFlatListRow }) => {
      if (!item.value) {
        return null;
      }
      return (
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
      );
    },
    [],
  );
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
      const anchors = info.viewableItems
        .filter((token) => token.isViewable && token.item)
        .map((token) => token.item as DependencyFlatListRow)
        .filter((row) => row?.key?.startsWith('msg-'))
        .map((row) => ({ key: row.key, sourceIndex: row.sourceIndex }));
      viewableAnchorsRef.current = anchors;
      onViewableItemsChanged?.(info);
    },
  );
  handleViewableItemsChanged.current = (info) => {
    const anchors = info.viewableItems
      .filter((token) => token.isViewable && token.item)
      .map((token) => token.item as DependencyFlatListRow)
      .filter((row) => row?.key?.startsWith('msg-'))
      .map((row) => ({ key: row.key, sourceIndex: row.sourceIndex }));
    viewableAnchorsRef.current = anchors;
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
      if (pending && Date.now() > pending.deadlineMs) {
        finishPendingItemAnchor('listAnchorStopped', 'scrollToIndexDeadline');
        return;
      }
      if (pending && pending.attempts < resolvedItemAnchorMaxAttempts) {
        pendingScrollToIndexRetryRef.current = {
          ...pending,
          attempts: pending.attempts + 1,
        };
        const averageOffset = Math.max(
          0,
          Math.max(0, info.index) * Math.max(1, info.averageItemLength || 1),
        );
        getMacScrollViewMetrics(flatListRef.current)
          .then((metrics) => {
            const ratioOffset =
              metrics && rows.length > 1
                ? Math.max(0, metrics.contentHeight - metrics.viewportHeight) *
                  Math.max(0, Math.min(1, info.index / (rows.length - 1)))
                : 0;
            flatListRef.current?.scrollToOffset?.({
              offset: Math.max(averageOffset, ratioOffset),
              animated: false,
            });
            setTimeout(retryPendingScrollToIndex, 100);
          })
          .catch(() => {
            flatListRef.current?.scrollToOffset?.({ offset: averageOffset, animated: false });
            setTimeout(retryPendingScrollToIndex, 100);
          });
      } else if (pending) {
        finishPendingItemAnchor('listAnchorStopped', 'scrollToIndexMaxAttempts');
      }
    },
    [
      finishPendingItemAnchor,
      onScrollToIndexFailed,
      resolvedItemAnchorMaxAttempts,
      retryPendingScrollToIndex,
      rows.length,
    ],
  );
  const cancelPendingItemAnchor = React.useCallback(
    (reason: string) => {
      finishPendingItemAnchor('listAnchorStopped', reason);
    },
    [finishPendingItemAnchor],
  );
  const handleScrollBeginDrag = React.useCallback(
    (event: Parameters<NonNullable<typeof onScrollBeginDrag>>[0]) => {
      cancelPendingItemAnchor('userInteraction');
      onScrollBeginDrag?.(event);
    },
    [cancelPendingItemAnchor, onScrollBeginDrag],
  );
  React.useImperativeHandle(
    listRef,
    () => ({
      scrollToOffset: (options: { offset: number; animated?: boolean }) => {
        cancelPendingItemAnchor('supersededByOffset');
        flatListRef.current?.scrollToOffset?.(options);
      },
      scrollToEnd: (options?: { animated?: boolean }) => {
        cancelPendingItemAnchor('supersededByEnd');
        flatListRef.current?.scrollToEnd?.(options);
      },
      scrollToIndex: (options: {
        index: number;
        animated?: boolean;
        viewPosition?: number;
        viewOffset?: number;
      }) => flatListRef.current?.scrollToIndex?.(options),
      getNativeScrollRef: () => flatListRef.current,
      getScrollableNode: () => flatListRef.current?.getScrollableNode?.(),
      getVisibleAnchor: captureVisibleAnchor,
      getItemViewportOffset: (key: string) => measureItemViewportOffset(key),
      hasPendingScrollAction: () => pendingItemAnchorRef.current != null,
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
          emitScrollActionDiagnostic('listAnchorStopped', 'missingItem', {
            key: request.key ?? null,
            sourceIndex: request.sourceIndex ?? null,
          });
          return;
        }
        const viewOffset = Number.isFinite(request.offsetFromViewportTop)
          ? request.offsetFromViewportTop
          : 0;
        const startedAtMs = Date.now();
        const deadlineMs = startedAtMs + resolvedItemAnchorTimeoutMs;
        cancelPendingItemAnchor('replaced');
        pendingScrollToIndexRetryRef.current = {
          index,
          viewOffset,
          animated: request.animated ?? false,
          attempts: 0,
          startedAtMs,
          deadlineMs,
        };
        pendingItemAnchorRef.current = {
          key: rows[index].key,
          index,
          viewOffset,
          animated: request.animated ?? false,
          attempts: 0,
          startedAtMs,
          deadlineMs,
        };
        emitScrollActionDiagnostic('listAnchorStarted', 'scrollToItemAnchor', {
          key: rows[index].key,
          index,
          requestedOffset: Math.round(viewOffset),
          timeoutMs: resolvedItemAnchorTimeoutMs,
          maxAttempts: resolvedItemAnchorMaxAttempts,
        });
        flatListRef.current?.scrollToIndex?.({
          index,
          animated: request.animated ?? false,
          viewPosition: 0,
          viewOffset,
        });
        retryItemAnchor();
      },
    }),
    [
      cancelPendingItemAnchor,
      captureVisibleAnchor,
      emitScrollActionDiagnostic,
      indexByKey,
      measureItemViewportOffset,
      resolvedItemAnchorMaxAttempts,
      resolvedItemAnchorTimeoutMs,
      retryItemAnchor,
      rows,
    ],
  );
  const diagnosticProps = {
    disableVirtualization,
    initialNumToRender: renderTuning.initialNumToRender,
    maxToRenderPerBatch: renderTuning.maxToRenderPerBatch,
    updateCellsBatchingPeriod: renderTuning.updateCellsBatchingPeriod,
    windowSize,
    removeClippedSubviews: renderTuning.removeClippedSubviews,
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
      onScrollBeginDrag={handleScrollBeginDrag}
      onScrollEndDrag={onScrollEndDrag}
      onMomentumScrollBegin={onMomentumScrollBegin}
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
