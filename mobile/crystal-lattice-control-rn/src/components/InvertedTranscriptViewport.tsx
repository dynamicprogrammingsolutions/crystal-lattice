import React from "react";
import {
  StyleSheet,
  View,
  type FlatList,
  type StyleProp,
  type ViewStyle,
} from "react-native";

import {
  isChatScrollAnchor,
  PINNED_TO_BOTTOM_THRESHOLD_PX,
  type ChatScrollAnchor,
} from "../chatScroll";
import {
  deriveInvertedTranscriptScrollState,
  scrollInvertedTranscriptToBottom,
  type InvertedTranscriptScrollState,
} from "../invertedTranscriptScroll";
import {
  DependencyFlatList,
  type DependencyFlatListProps,
} from "./DependencyFlatList";
import { TranscriptEdgeButtons } from "./TranscriptEdgeButtons";

type InvertedTranscriptViewportProps<TItem> = Pick<
  DependencyFlatListProps<TItem>,
  | "data"
  | "renderItem"
  | "keyExtractor"
  | "getItemDependencies"
  | "ListHeaderComponent"
  | "ListFooterComponent"
  | "ListEmptyComponent"
  | "ItemSeparatorComponent"
  | "extraData"
  | "contentContainerStyle"
> & {
  listRef: React.RefObject<FlatList<any> | null>;
  initialScrollAnchor?: ChatScrollAnchor | null;
  onScrollStateChange?: (state: InvertedTranscriptScrollState) => void;
  style?: StyleProp<ViewStyle>;
  listStyle?: StyleProp<ViewStyle>;
  testID?: string;
};

const TOP_NAVIGATION_MAX_MS = 30000;
const TOP_NAVIGATION_MAX_ATTEMPTS = 60;

export function InvertedTranscriptViewport<TItem>({
  listRef,
  initialScrollAnchor,
  onScrollStateChange,
  style,
  listStyle,
  testID,
  ...listProps
}: InvertedTranscriptViewportProps<TItem>): React.JSX.Element {
  const offsetYRef = React.useRef(0);
  const viewportHeightRef = React.useRef(0);
  const contentHeightRef = React.useRef(0);
  const initialScrollAnchorRef = React.useRef<ChatScrollAnchor | null>(
    isChatScrollAnchor(initialScrollAnchor) ? initialScrollAnchor : null
  );
  const hasRestoredScrollRef = React.useRef(false);
  const onScrollStateChangeRef = React.useRef(onScrollStateChange);
  const scrollStateRef = React.useRef<InvertedTranscriptScrollState | null>(
    null
  );
  const topNavigationRef = React.useRef<{
    attempts: number;
    deadlineMs: number;
    topReachedAtMs: number | null;
  } | null>(null);
  const topNavigationTimerRef = React.useRef<ReturnType<
    typeof setTimeout
  > | null>(null);
  const runTopNavigationRef = React.useRef<() => void>(() => {});
  const [scrollState, setScrollState] =
    React.useState<InvertedTranscriptScrollState>(() =>
      deriveInvertedTranscriptScrollState(
        {
          offsetY: 0,
          viewportHeight: 0,
          contentHeight: 0,
        },
        PINNED_TO_BOTTOM_THRESHOLD_PX
      )
    );

  React.useEffect(() => {
    onScrollStateChangeRef.current = onScrollStateChange;
  }, [onScrollStateChange]);

  React.useEffect(() => {
    if (hasRestoredScrollRef.current) {
      return;
    }
    initialScrollAnchorRef.current = isChatScrollAnchor(initialScrollAnchor)
      ? initialScrollAnchor
      : null;
  }, [initialScrollAnchor]);

  const clearTopNavigationTimer = React.useCallback(() => {
    if (topNavigationTimerRef.current != null) {
      clearTimeout(topNavigationTimerRef.current);
      topNavigationTimerRef.current = null;
    }
  }, []);

  const stopTopNavigation = React.useCallback(() => {
    clearTopNavigationTimer();
    topNavigationRef.current = null;
  }, [clearTopNavigationTimer]);

  React.useEffect(
    () => () => {
      clearTopNavigationTimer();
    },
    [clearTopNavigationTimer]
  );

  const updateMetrics = React.useCallback(
    (updates: {
      offsetY?: number;
      viewportHeight?: number;
      contentHeight?: number;
    }) => {
      const offsetY =
        typeof updates.offsetY === "number" && Number.isFinite(updates.offsetY)
          ? updates.offsetY
          : offsetYRef.current;
      const viewportHeight =
        typeof updates.viewportHeight === "number" &&
        Number.isFinite(updates.viewportHeight)
          ? updates.viewportHeight
          : viewportHeightRef.current;
      const contentHeight =
        typeof updates.contentHeight === "number" &&
        Number.isFinite(updates.contentHeight)
          ? updates.contentHeight
          : contentHeightRef.current;

      viewportHeightRef.current = Math.max(0, viewportHeight);
      contentHeightRef.current = Math.max(0, contentHeight);
      const next = deriveInvertedTranscriptScrollState(
        {
          offsetY,
          viewportHeight,
          contentHeight,
        },
        PINNED_TO_BOTTOM_THRESHOLD_PX
      );
      offsetYRef.current = next.offsetY;
      scrollStateRef.current = next;
      const topNavigation = topNavigationRef.current;
      if (topNavigation) {
        if (next.canScrollToTop) {
          topNavigation.topReachedAtMs = null;
        }
        clearTopNavigationTimer();
        topNavigationTimerRef.current = setTimeout(() => {
          topNavigationTimerRef.current = null;
          runTopNavigationRef.current();
        }, 50);
      }
      onScrollStateChangeRef.current?.(next);
      setScrollState((current) =>
        current.canScrollToTop === next.canScrollToTop &&
        current.canScrollToBottom === next.canScrollToBottom &&
        current.pinnedToBottom === next.pinnedToBottom
          ? current
          : next
      );
    },
    [clearTopNavigationTimer]
  );

  const maybeRestoreScroll = React.useCallback(() => {
    if (hasRestoredScrollRef.current) {
      return;
    }
    if (
      viewportHeightRef.current <= 0 ||
      contentHeightRef.current <= 0 ||
      !listRef.current
    ) {
      return;
    }

    const anchor = initialScrollAnchorRef.current;
    const offset = anchor && !anchor.pinnedToBottom ? anchor.bottomGapPx : 0;
    listRef.current.scrollToOffset({ offset, animated: false });
    updateMetrics({ offsetY: offset });
    hasRestoredScrollRef.current = true;
  }, [listRef, updateMetrics]);

  const handleLayout = React.useCallback(
    (event: any) => {
      updateMetrics({
        viewportHeight: event?.nativeEvent?.layout?.height,
      });
      maybeRestoreScroll();
    },
    [maybeRestoreScroll, updateMetrics]
  );

  const handleContentSizeChange = React.useCallback(
    (_width: number, contentHeight: number) => {
      updateMetrics({ contentHeight });
      maybeRestoreScroll();
    },
    [maybeRestoreScroll, updateMetrics]
  );

  const handleScroll = React.useCallback(
    (event: any) => {
      updateMetrics({
        offsetY: event?.nativeEvent?.contentOffset?.y,
        viewportHeight: event?.nativeEvent?.layoutMeasurement?.height,
        contentHeight: event?.nativeEvent?.contentSize?.height,
      });
    },
    [updateMetrics]
  );

  const scheduleTopNavigation = React.useCallback(
    (delayMs: number) => {
      clearTopNavigationTimer();
      topNavigationTimerRef.current = setTimeout(() => {
        topNavigationTimerRef.current = null;
        runTopNavigationRef.current();
      }, delayMs);
    },
    [clearTopNavigationTimer]
  );

  const runTopNavigation = React.useCallback(() => {
    const operation = topNavigationRef.current;
    const list = listRef.current;
    if (!operation || !list || listProps.data.length === 0) {
      stopTopNavigation();
      return;
    }
    const now = Date.now();
    if (scrollStateRef.current?.canScrollToTop === false) {
      if (operation.topReachedAtMs == null) {
        operation.topReachedAtMs = now;
        scheduleTopNavigation(400);
        return;
      }
      if (now - operation.topReachedAtMs >= 400) {
        stopTopNavigation();
        return;
      }
      scheduleTopNavigation(400 - (now - operation.topReachedAtMs));
      return;
    }
    if (
      now >= operation.deadlineMs ||
      operation.attempts >= TOP_NAVIGATION_MAX_ATTEMPTS
    ) {
      stopTopNavigation();
      return;
    }

    operation.attempts += 1;
    operation.topReachedAtMs = null;
    if (operation.attempts % 2 === 1) {
      list.scrollToIndex({
        index: listProps.data.length - 1,
        animated: operation.attempts === 1,
        viewPosition: 0,
      });
    } else {
      list.scrollToOffset({
        offset: scrollStateRef.current?.maxOffsetY ?? 0,
        animated: false,
      });
    }
    scheduleTopNavigation(operation.attempts === 1 ? 500 : 150);
  }, [
    listProps.data.length,
    listRef,
    scheduleTopNavigation,
    stopTopNavigation,
  ]);

  runTopNavigationRef.current = runTopNavigation;

  const startTopNavigation = React.useCallback(() => {
    stopTopNavigation();
    topNavigationRef.current = {
      attempts: 0,
      deadlineMs: Date.now() + TOP_NAVIGATION_MAX_MS,
      topReachedAtMs: null,
    };
    runTopNavigationRef.current();
  }, [stopTopNavigation]);

  const handleScrollToIndexFailed = React.useCallback(
    (info: {
      index: number;
      highestMeasuredFrameIndex: number;
      averageItemLength: number;
    }) => {
      if (!topNavigationRef.current || !listRef.current) {
        return;
      }
      const approximateOffset = Math.max(
        0,
        info.averageItemLength * info.index
      );
      listRef.current.scrollToOffset({
        offset: approximateOffset,
        animated: false,
      });
      scheduleTopNavigation(100);
    },
    [listRef, scheduleTopNavigation]
  );

  const handleScrollBeginDrag = React.useCallback(() => {
    stopTopNavigation();
  }, [stopTopNavigation]);

  const handleScrollSettled = React.useCallback(() => {
    if (topNavigationRef.current) {
      scheduleTopNavigation(50);
    }
  }, [scheduleTopNavigation]);

  return (
    <View style={[styles.frame, style]}>
      <DependencyFlatList
        {...listProps}
        ref={listRef}
        style={[styles.list, listStyle]}
        testID={testID}
        inverted
        onLayout={handleLayout}
        onContentSizeChange={handleContentSizeChange}
        onScroll={handleScroll}
        onScrollBeginDrag={handleScrollBeginDrag}
        onScrollEndDrag={handleScrollSettled}
        onMomentumScrollEnd={handleScrollSettled}
        onScrollToIndexFailed={handleScrollToIndexFailed}
        scrollEventThrottle={16}
        maintainVisibleContentPosition={{
          minIndexForVisible: 0,
          autoscrollToTopThreshold: PINNED_TO_BOTTOM_THRESHOLD_PX,
        }}
      />
      <TranscriptEdgeButtons
        canScrollToTop={scrollState.canScrollToTop}
        canScrollToBottom={scrollState.canScrollToBottom}
        onScrollToTop={startTopNavigation}
        onScrollToBottom={() => {
          stopTopNavigation();
          scrollInvertedTranscriptToBottom(listRef.current);
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    flex: 1,
    position: "relative",
  },
  list: {
    flex: 1,
  },
});
