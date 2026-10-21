import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Animated,
  type GestureResponderEvent,
  type LayoutChangeEvent,
  Modal,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  PanResponder,
  Platform,
  type PanResponderGestureState,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Icon from "react-native-vector-icons/Feather";
import type {
  ConnectionRecord,
  SessionRequestStatus,
} from "@crystal-lattice/frontend-sdk";

import type { SessionsCache } from "../App";
import { useHomeWorkspace } from "./HomeWorkspaceContext";
import {
  deriveHomeSessionCollections,
  type HomeSessionItem,
} from "./homeWorkspaceState";
import { useTheme, type Theme } from "./theme";
import SessionNoteModal from "./components/SessionNoteModal";
import SessionRequestStatusBadge from "./components/SessionRequestStatusBadge";
import {
  applyWatchlistKeyOrder,
  buildWatchlistRenderSlots,
  moveWatchlistValues,
  resolveWatchlistDropTranslation,
  resolveWatchlistDropTarget,
  type WatchlistTileFrame,
} from "./watchlistDrag";
import { resolveMobileHomeSessionPresentation } from "./homeSessionPresentation";

interface HomeScreenProps {
  renderConnectionSection?: (onCollapse: () => void) => React.ReactNode;
  connections: readonly ConnectionRecord[];
  sessionsCache: SessionsCache;
  statusesByConnection: Readonly<
    Record<string, Readonly<Record<string, SessionRequestStatus>>>
  >;
  onOpenGlobalSettings: () => void;
  onOpenDevelopmentSettings?: () => void;
  onOpenEmbeddedSettings?: () => void;
  onNewConnection: () => void;
  onSelectSession: (connectionId: string, sessionId: string) => void;
}

const WatchlistTile: React.FC<{
  item: HomeSessionItem;
  index: number;
  itemCount: number;
  status: SessionRequestStatus | null;
  dragFrame?: WatchlistTileFrame;
  dragTranslation?: Animated.ValueXY;
  isDragging?: boolean;
  onLayout?: (event: LayoutChangeEvent) => void;
  onPress: () => void;
  onMove: (fromIndex: number, toIndex: number) => void;
  onDragStart: (key: string) => void;
  onDragMove: (gesture: PanResponderGestureState, pageY: number | null) => void;
  onDragRelease: (gesture: PanResponderGestureState) => void;
  onDragCancel: () => void;
  onEditNote: () => void;
  onRemove: () => void;
}> = ({
  item,
  index,
  itemCount,
  status,
  dragFrame,
  dragTranslation,
  isDragging = false,
  onLayout,
  onPress,
  onMove,
  onDragStart,
  onDragMove,
  onDragRelease,
  onDragCancel,
  onEditNote,
  onRemove,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const presentation = useMemo(
    () => resolveMobileHomeSessionPresentation(item),
    [item]
  );
  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onStartShouldSetPanResponderCapture: () => true,
        onMoveShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponderCapture: () => true,
        onPanResponderGrant: () => {
          onDragStart(item.key);
        },
        onPanResponderMove: (
          event: GestureResponderEvent,
          gesture: PanResponderGestureState
        ) => {
          const pageY = event.nativeEvent.pageY;
          onDragMove(gesture, Number.isFinite(pageY) ? pageY : null);
        },
        onPanResponderRelease: (_event, gesture) => onDragRelease(gesture),
        onPanResponderTerminate: onDragCancel,
        onPanResponderTerminationRequest: () => false,
        onShouldBlockNativeResponder: () => true,
      }),
    [item.key, onDragCancel, onDragMove, onDragRelease, onDragStart]
  );

  return (
    <Animated.View
      testID={`home-watchlist-tile-${item.connectionId}-${item.sessionId}`}
      onLayout={onLayout}
      style={[
        styles.watchTile,
        isDragging && styles.draggedTile,
        isDragging &&
          dragFrame &&
          dragTranslation && {
            position: "absolute",
            left: dragFrame.x,
            top: dragFrame.y,
            width: dragFrame.width,
            height: dragFrame.height,
            transform: dragTranslation.getTranslateTransform(),
          },
      ]}
    >
      <View style={styles.tileTopRow}>
        <View
          testID={`home-watchlist-drag-${item.connectionId}-${item.sessionId}`}
          accessibilityRole="adjustable"
          accessibilityLabel={`Reorder ${presentation.title}`}
          accessibilityActions={[
            { name: "increment", label: "Move later" },
            { name: "decrement", label: "Move earlier" },
          ]}
          onAccessibilityAction={(event) => {
            if (event.nativeEvent.actionName === "increment") {
              onMove(index, Math.min(itemCount - 1, index + 1));
            } else if (event.nativeEvent.actionName === "decrement") {
              onMove(index, Math.max(0, index - 1));
            }
          }}
          style={styles.dragHandle}
          {...panResponder.panHandlers}
        >
          <Icon name="move" size={17} color={theme.textSecondary} />
        </View>
        <View style={styles.tileActions}>
          <TouchableOpacity
            testID={`home-watchlist-note-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={
              item.note ? "Edit session note" : "Add session note"
            }
            style={styles.iconButton}
            onPress={onEditNote}
          >
            <Icon
              name={item.note ? "edit-3" : "file-plus"}
              size={16}
              color={theme.primary}
            />
          </TouchableOpacity>
          <TouchableOpacity
            testID={`home-watchlist-remove-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel="Remove from Watchlist"
            style={styles.iconButton}
            onPress={onRemove}
          >
            <Icon name="x" size={17} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>
      </View>
      <TouchableOpacity
        testID={`home-watchlist-open-${item.connectionId}-${item.sessionId}`}
        style={styles.tileBody}
        onPress={onPress}
      >
        <Text
          testID={`home-watchlist-title-${item.connectionId}-${item.sessionId}`}
          accessibilityLabel={presentation.title}
          style={styles.watchTitle}
          numberOfLines={2}
        >
          {presentation.title}
        </Text>
        {presentation.subtitle ? (
          <Text
            testID={`home-watchlist-subtitle-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={presentation.subtitle}
            style={styles.sessionSubtitle}
            numberOfLines={2}
          >
            {presentation.subtitle}
          </Text>
        ) : null}
        <Text
          testID={`home-watchlist-session-id-${item.connectionId}-${item.sessionId}`}
          accessibilityLabel={`Session ID ${presentation.sessionId}`}
          style={styles.sessionId}
          numberOfLines={1}
          ellipsizeMode="tail"
        >
          {presentation.sessionId}
        </Text>
        <SessionRequestStatusBadge
          status={status}
          testID={`home-watchlist-status-${item.connectionId}-${item.sessionId}`}
        />
        {item.note ? (
          <Text
            testID={`home-watchlist-note-preview-${item.connectionId}-${item.sessionId}`}
            style={styles.notePreview}
            numberOfLines={2}
          >
            {item.note}
          </Text>
        ) : null}
        <View
          testID={`home-watchlist-metadata-${item.connectionId}-${item.sessionId}`}
          style={[styles.metadataRow, styles.watchMetadataRow]}
        >
          <Text
            testID={`home-watchlist-connection-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={`Connection ${presentation.connectionName}`}
            style={styles.metadataConnection}
            numberOfLines={1}
            ellipsizeMode="tail"
          >
            {presentation.connectionName}
          </Text>
          <Text
            testID={`home-watchlist-time-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={`Modified ${presentation.relativeTime}`}
            style={styles.metadataTime}
            numberOfLines={1}
          >
            {presentation.relativeTime}
          </Text>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
};

interface ActiveWatchlistDrag {
  phase: "dragging" | "settling";
  key: string;
  sourceKeys: string[];
  sourceIndex: number;
  targetIndex: number;
  sourceFrame: WatchlistTileFrame;
  slotFrames: WatchlistTileFrame[];
  startScrollOffset: number;
  gestureX: number;
  gestureY: number;
}

interface ScrollViewport {
  y: number;
  height: number;
}

interface SettledWatchlistOrder {
  sourceKeys: string[];
  targetKeys: string[];
}

const DRAG_EDGE_SIZE = 64;
const DRAG_EDGE_SCROLL_STEP = 18;

function sameKeyOrder(
  left: readonly string[],
  right: readonly string[]
): boolean {
  return (
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  );
}

const HomeScreen: React.FC<HomeScreenProps> = ({
  renderConnectionSection,
  connections,
  sessionsCache,
  statusesByConnection,
  onOpenGlobalSettings,
  onOpenDevelopmentSettings,
  onOpenEmbeddedSettings,
  onNewConnection,
  onSelectSession,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const {
    hydrated,
    watchlist,
    notes,
    recentSessionsWindow,
    isWatched,
    addToWatchlist,
    removeFromWatchlist,
    moveWatchlistItem,
    setSessionNote,
    removeSessionNote,
  } = useHomeWorkspace();
  const derivedCollections = useMemo(
    () =>
      deriveHomeSessionCollections({
        connections,
        sessionsCache,
        watchlist,
        notes,
        recentSessionsWindow,
      }),
    [connections, notes, recentSessionsWindow, sessionsCache, watchlist]
  );
  const [menuVisible, setMenuVisible] = useState(false);
  const [noteSessionId, setNoteSessionId] = useState<string | null>(null);
  const [activeDrag, setActiveDrag] = useState<ActiveWatchlistDrag | null>(
    null
  );
  const [settledWatchlistOrder, setSettledWatchlistOrder] =
    useState<SettledWatchlistOrder | null>(null);
  const collections = useMemo(
    () =>
      settledWatchlistOrder
        ? {
            ...derivedCollections,
            watchlist: applyWatchlistKeyOrder(
              derivedCollections.watchlist,
              settledWatchlistOrder.targetKeys
            ),
          }
        : derivedCollections,
    [derivedCollections, settledWatchlistOrder]
  );
  useEffect(() => {
    if (!settledWatchlistOrder) return;
    const currentKeys = derivedCollections.watchlist.map((item) => item.key);
    if (
      sameKeyOrder(currentKeys, settledWatchlistOrder.targetKeys) ||
      !sameKeyOrder(currentKeys, settledWatchlistOrder.sourceKeys)
    ) {
      setSettledWatchlistOrder(null);
      setActiveDrag((current) =>
        current?.phase === "settling" ? null : current
      );
    }
  }, [derivedCollections.watchlist, settledWatchlistOrder]);
  const activeDragRef = useRef<ActiveWatchlistDrag | null>(null);
  const tileFramesRef = useRef<Record<string, WatchlistTileFrame>>({});
  const dragTranslation = useRef(new Animated.ValueXY()).current;
  const scrollViewRef = useRef<ScrollView | null>(null);
  const settingsOpeningRef = useRef(false);
  const pendingSettingsOpenRef = useRef<(() => void) | null>(null);
  const scrollOffsetRef = useRef(0);
  const scrollViewportRef = useRef<ScrollViewport | null>(null);
  const scrollContentHeightRef = useRef(0);
  const watchlistItems = useMemo(
    () =>
      activeDrag
        ? applyWatchlistKeyOrder(
            derivedCollections.watchlist,
            activeDrag.sourceKeys
          )
        : collections.watchlist,
    [activeDrag, collections.watchlist, derivedCollections.watchlist]
  );
  const collectionsRef = useRef({
    ...collections,
    watchlist: watchlistItems,
  });
  collectionsRef.current = { ...collections, watchlist: watchlistItems };

  useEffect(() => {
    if (!activeDrag) {
      dragTranslation.setValue({ x: 0, y: 0 });
    }
  }, [activeDrag, dragTranslation]);

  const updateDragPosition = useCallback(
    (gestureX: number, gestureY: number) => {
      const current = activeDragRef.current;
      if (!current) return;
      const scrollDelta = scrollOffsetRef.current - current.startScrollOffset;
      const translationY = gestureY + scrollDelta;
      dragTranslation.setValue({ x: gestureX, y: translationY });
      const targetIndex = resolveWatchlistDropTarget(
        current.slotFrames,
        current.sourceIndex,
        gestureX,
        translationY
      );
      const next = {
        ...current,
        targetIndex,
        gestureX,
        gestureY,
      };
      activeDragRef.current = next;
      if (targetIndex !== current.targetIndex) setActiveDrag(next);
    },
    [dragTranslation]
  );

  const startWatchlistDrag = useCallback(
    (key: string) => {
      const currentItems = collectionsRef.current.watchlist;
      const sourceIndex = currentItems.findIndex((item) => item.key === key);
      const slotFrames = currentItems.map(
        (item) => tileFramesRef.current[item.key]
      );
      const sourceFrame = slotFrames[sourceIndex];
      if (
        sourceIndex < 0 ||
        !sourceFrame ||
        slotFrames.some((frame) => frame === undefined)
      ) {
        return;
      }
      const measuredSlotFrames = slotFrames as WatchlistTileFrame[];
      const next: ActiveWatchlistDrag = {
        phase: "dragging",
        key,
        sourceKeys: currentItems.map((item) => item.key),
        sourceIndex,
        targetIndex: sourceIndex,
        sourceFrame,
        slotFrames: measuredSlotFrames,
        startScrollOffset: scrollOffsetRef.current,
        gestureX: 0,
        gestureY: 0,
      };
      dragTranslation.setValue({ x: 0, y: 0 });
      activeDragRef.current = next;
      setActiveDrag(next);
    },
    [dragTranslation]
  );

  const autoScrollForDrag = useCallback((pageY: number | null) => {
    const viewport = scrollViewportRef.current;
    if (pageY === null || !viewport) return;
    const maxOffset = Math.max(
      0,
      scrollContentHeightRef.current - viewport.height
    );
    let delta = 0;
    if (pageY < viewport.y + DRAG_EDGE_SIZE) {
      delta = -DRAG_EDGE_SCROLL_STEP;
    } else if (pageY > viewport.y + viewport.height - DRAG_EDGE_SIZE) {
      delta = DRAG_EDGE_SCROLL_STEP;
    }
    if (delta === 0) return;
    const nextOffset = Math.max(
      0,
      Math.min(maxOffset, scrollOffsetRef.current + delta)
    );
    if (nextOffset === scrollOffsetRef.current) return;
    scrollViewRef.current?.scrollTo({ y: nextOffset, animated: false });
  }, []);

  const moveWatchlistDrag = useCallback(
    (gesture: PanResponderGestureState, pageY: number | null) => {
      updateDragPosition(gesture.dx, gesture.dy);
      autoScrollForDrag(pageY);
    },
    [autoScrollForDrag, updateDragPosition]
  );

  const releaseWatchlistDrag = useCallback(
    (gesture: PanResponderGestureState) => {
      updateDragPosition(gesture.dx, gesture.dy);
      const settled = activeDragRef.current;
      activeDragRef.current = null;
      if (settled && settled.sourceIndex !== settled.targetIndex) {
        const sourceKeys = settled.sourceKeys;
        const targetKeys = moveWatchlistValues(
          sourceKeys,
          settled.sourceIndex,
          settled.targetIndex
        );
        dragTranslation.setValue(
          resolveWatchlistDropTranslation(
            settled.slotFrames,
            settled.sourceIndex,
            settled.targetIndex
          )
        );
        setActiveDrag({
          ...settled,
          phase: "settling",
          targetIndex: settled.targetIndex,
        });
        setSettledWatchlistOrder({ sourceKeys, targetKeys });
        moveWatchlistItem(settled.sourceIndex, settled.targetIndex);
      } else {
        setActiveDrag(null);
      }
    },
    [dragTranslation, moveWatchlistItem, updateDragPosition]
  );

  const cancelWatchlistDrag = useCallback(() => {
    activeDragRef.current = null;
    setActiveDrag(null);
  }, []);

  const recordTileFrame = useCallback(
    (key: string, event: LayoutChangeEvent) => {
      tileFramesRef.current[key] = event.nativeEvent.layout;
    },
    []
  );

  const handleHomeScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      scrollOffsetRef.current = event.nativeEvent.contentOffset.y;
      const current = activeDragRef.current;
      if (current) {
        updateDragPosition(current.gestureX, current.gestureY);
      }
    },
    [updateDragPosition]
  );

  const measureScrollViewport = useCallback(() => {
    scrollViewRef.current
      ?.getNativeScrollRef()
      ?.measureInWindow((_x, y, _width, height) => {
        scrollViewportRef.current = { y, height };
      });
  }, []);

  const finishSettingsHandoff = useCallback(() => {
    const open = pendingSettingsOpenRef.current;
    pendingSettingsOpenRef.current = null;
    settingsOpeningRef.current = false;
    open?.();
  }, []);
  const openSettingsFromMenu = useCallback((open: () => void) => {
    if (settingsOpeningRef.current) {
      return;
    }
    settingsOpeningRef.current = true;
    pendingSettingsOpenRef.current = open;
    setMenuVisible(false);
    if (Platform.OS !== "ios") {
      setTimeout(finishSettingsHandoff, 300);
    }
  }, [finishSettingsHandoff]);
  const openEmbeddedSettingsFromMenu = useCallback(() => {
    if (onOpenEmbeddedSettings) openSettingsFromMenu(onOpenEmbeddedSettings);
  }, [onOpenEmbeddedSettings, openSettingsFromMenu]);
  const openGlobalSettingsFromMenu = useCallback(() => {
    openSettingsFromMenu(onOpenGlobalSettings);
  }, [onOpenGlobalSettings, openSettingsFromMenu]);
  const openDevelopmentSettingsFromMenu = useCallback(() => {
    if (onOpenDevelopmentSettings) openSettingsFromMenu(onOpenDevelopmentSettings);
  }, [onOpenDevelopmentSettings, openSettingsFromMenu]);
  const openNewConnectionFromMenu = useCallback(() => {
    openSettingsFromMenu(onNewConnection);
  }, [onNewConnection, openSettingsFromMenu]);

  const watchlistRenderSlots = useMemo(
    () =>
      activeDrag
        ? buildWatchlistRenderSlots(
            watchlistItems,
            activeDrag.sourceIndex,
            activeDrag.targetIndex
          )
        : watchlistItems.map((item) => ({
            kind: "item" as const,
            item,
          })),
    [activeDrag, watchlistItems]
  );
  const recentWindowLabel =
    recentSessionsWindow === "24h"
      ? "Last 24 hours"
      : recentSessionsWindow === "1w"
      ? "Last week"
      : "Last 3 days";

  if (!hydrated) {
    return (
      <View style={styles.centered}>
        <Text style={styles.emptyText}>Loading Home…</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header} testID="home-screen-header">
        <TouchableOpacity
          testID="home-menu"
          accessibilityRole="button"
          accessibilityLabel="Open Home menu"
          style={styles.headerIcon}
          onPress={() => setMenuVisible(true)}
        >
          <Icon name="menu" size={21} color={theme.text} />
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Home</Text>
        <View style={styles.headerIcon} testID="home-account-slot" />
      </View>

      <ScrollView
        ref={scrollViewRef}
        testID="home-scroll"
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        scrollEnabled={activeDrag === null}
        scrollEventThrottle={16}
        onLayout={measureScrollViewport}
        onScroll={handleHomeScroll}
        onContentSizeChange={(_width, height) => {
          scrollContentHeightRef.current = height;
        }}
      >
        {renderConnectionSection?.(() => {
          scrollViewRef.current?.scrollTo({ y: 0, animated: false });
        })}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Watchlist</Text>
          <Text style={styles.sectionHint}>Stored on this device</Text>
        </View>
        {watchlistItems.length === 0 ? (
          <Text style={styles.emptyText}>
            Add recent sessions to your Watchlist for quick access.
          </Text>
        ) : (
          <View style={styles.watchGrid} testID="home-watchlist-grid">
            {watchlistRenderSlots.map((slot, slotIndex) => {
              if (slot.kind === "placeholder") {
                return activeDrag ? (
                  <View
                    key={`placeholder-${activeDrag.key}`}
                    testID={`home-watchlist-placeholder-${activeDrag.key}`}
                    style={[
                      styles.watchPlaceholder,
                      {
                        width: activeDrag.sourceFrame.width,
                        height: activeDrag.sourceFrame.height,
                      },
                    ]}
                  />
                ) : null;
              }
              if (slot.kind === "dragged") {
                const item = slot.item;
                return activeDrag ? (
                  <WatchlistTile
                    key={item.key}
                    item={item}
                    index={activeDrag.sourceIndex}
                    itemCount={watchlistItems.length}
                    status={
                      statusesByConnection[item.connectionId]?.[
                        item.sessionId
                      ] ?? null
                    }
                    dragFrame={activeDrag.sourceFrame}
                    dragTranslation={dragTranslation}
                    isDragging
                    onPress={() =>
                      onSelectSession(item.connectionId, item.sessionId)
                    }
                    onMove={moveWatchlistItem}
                    onDragStart={startWatchlistDrag}
                    onDragMove={moveWatchlistDrag}
                    onDragRelease={releaseWatchlistDrag}
                    onDragCancel={cancelWatchlistDrag}
                    onEditNote={() => setNoteSessionId(item.sessionId)}
                    onRemove={() =>
                      removeFromWatchlist(item.connectionId, item.sessionId)
                    }
                  />
                ) : null;
              }
              const item = slot.item;
              const storedIndex = watchlistItems.findIndex(
                (candidate) => candidate.key === item.key
              );
              return (
                <WatchlistTile
                  key={item.key}
                  item={item}
                  index={storedIndex >= 0 ? storedIndex : slotIndex}
                  itemCount={watchlistItems.length}
                  status={
                    statusesByConnection[item.connectionId]?.[item.sessionId] ??
                    null
                  }
                  onLayout={(event) => recordTileFrame(item.key, event)}
                  onPress={() =>
                    onSelectSession(item.connectionId, item.sessionId)
                  }
                  onMove={moveWatchlistItem}
                  onDragStart={startWatchlistDrag}
                  onDragMove={moveWatchlistDrag}
                  onDragRelease={releaseWatchlistDrag}
                  onDragCancel={cancelWatchlistDrag}
                  onEditNote={() => setNoteSessionId(item.sessionId)}
                  onRemove={() =>
                    removeFromWatchlist(item.connectionId, item.sessionId)
                  }
                />
              );
            })}
          </View>
        )}

        <View style={[styles.sectionHeader, styles.recentHeader]}>
          <Text style={styles.sectionTitle}>Recent Sessions</Text>
          <Text style={styles.sectionHint}>{recentWindowLabel}</Text>
        </View>
        {collections.recent.length === 0 ? (
          <Text style={styles.emptyText}>
            No cached sessions were modified in this timeframe.
          </Text>
        ) : (
          <View testID="home-recent-timeline">
            {collections.recent.map((item, index) => {
              const presentation = resolveMobileHomeSessionPresentation(item);
              return (
                <View
                  key={item.key}
                  style={styles.timelineRow}
                  testID={`home-recent-${item.connectionId}-${item.sessionId}`}
                >
                  <View style={styles.timelineRail}>
                    <View
                      testID={`home-recent-dot-${item.connectionId}-${item.sessionId}`}
                      accessible
                      accessibilityLabel="Timeline event"
                      style={styles.timelineDot}
                    />
                    {index < collections.recent.length - 1 ? (
                      <View
                        testID={`home-recent-line-${item.connectionId}-${item.sessionId}`}
                        style={styles.timelineLine}
                      />
                    ) : null}
                  </View>
                  <TouchableOpacity
                    testID={`home-recent-open-${item.connectionId}-${item.sessionId}`}
                    style={styles.timelineBody}
                    onPress={() =>
                      onSelectSession(item.connectionId, item.sessionId)
                    }
                  >
                    <Text
                      testID={`home-recent-title-${item.connectionId}-${item.sessionId}`}
                      accessibilityLabel={presentation.title}
                      style={styles.recentTitle}
                      numberOfLines={2}
                    >
                      {presentation.title}
                    </Text>
                    {presentation.subtitle ? (
                      <Text
                        testID={`home-recent-subtitle-${item.connectionId}-${item.sessionId}`}
                        accessibilityLabel={presentation.subtitle}
                        style={styles.sessionSubtitle}
                        numberOfLines={2}
                      >
                        {presentation.subtitle}
                      </Text>
                    ) : null}
                    <Text
                      testID={`home-recent-session-id-${item.connectionId}-${item.sessionId}`}
                      accessibilityLabel={`Session ID ${presentation.sessionId}`}
                      style={styles.sessionId}
                      numberOfLines={1}
                      ellipsizeMode="tail"
                    >
                      {presentation.sessionId}
                    </Text>
                    <SessionRequestStatusBadge
                      status={
                        statusesByConnection[item.connectionId]?.[
                          item.sessionId
                        ] ?? null
                      }
                      variant="inline"
                      testID={`home-recent-status-${item.connectionId}-${item.sessionId}`}
                    />
                    {item.note ? (
                      <Text
                        testID={`home-recent-note-preview-${item.connectionId}-${item.sessionId}`}
                        style={styles.notePreview}
                        numberOfLines={2}
                      >
                        {item.note}
                      </Text>
                    ) : null}
                    <View
                      testID={`home-recent-metadata-${item.connectionId}-${item.sessionId}`}
                      style={styles.metadataRow}
                    >
                      <Text
                        testID={`home-recent-connection-${item.connectionId}-${item.sessionId}`}
                        accessibilityLabel={`Connection ${presentation.connectionName}`}
                        style={styles.metadataConnection}
                        numberOfLines={1}
                        ellipsizeMode="tail"
                      >
                        {presentation.connectionName}
                      </Text>
                      <Text
                        testID={`home-recent-time-${item.connectionId}-${item.sessionId}`}
                        accessibilityLabel={`Modified ${presentation.relativeTime}`}
                        style={styles.metadataTime}
                        numberOfLines={1}
                      >
                        {presentation.relativeTime}
                      </Text>
                    </View>
                  </TouchableOpacity>
                  <View
                    testID={`home-recent-actions-${item.connectionId}-${item.sessionId}`}
                    style={styles.timelineActions}
                  >
                    <TouchableOpacity
                      testID={`home-recent-note-${item.connectionId}-${item.sessionId}`}
                      accessibilityLabel={
                        item.note ? "Edit session note" : "Add session note"
                      }
                      style={styles.iconButton}
                      onPress={() => setNoteSessionId(item.sessionId)}
                    >
                      <Icon
                        name={item.note ? "edit-3" : "file-plus"}
                        size={17}
                        color={theme.primary}
                      />
                    </TouchableOpacity>
                    <TouchableOpacity
                      testID={`home-recent-watch-${item.connectionId}-${item.sessionId}`}
                      accessibilityLabel={
                        isWatched(item.connectionId, item.sessionId)
                          ? "In Watchlist"
                          : "Add to Watchlist"
                      }
                      accessibilityState={{
                        disabled: isWatched(item.connectionId, item.sessionId),
                      }}
                      disabled={isWatched(item.connectionId, item.sessionId)}
                      style={[
                        styles.iconButton,
                        isWatched(item.connectionId, item.sessionId) &&
                          styles.disabledAction,
                      ]}
                      onPress={() =>
                        addToWatchlist(item.connectionId, item.sessionId)
                      }
                    >
                      <Icon name="bookmark" size={17} color={theme.primary} />
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

      <Modal
        visible={menuVisible}
        transparent
        animationType="fade"
        onDismiss={finishSettingsHandoff}
        testID="home-menu-modal"
        onRequestClose={() => setMenuVisible(false)}
      >
        <View style={styles.menuOverlay}>
          <View style={styles.menuPanel}>
            <Text style={styles.menuTitle}>Home menu</Text>
            <TouchableOpacity
              testID="home-menu-new-connection"
              style={styles.menuItem}
              accessibilityRole="button"
              accessibilityLabel="New connection"
              accessibilityActions={[{ name: "activate", label: "New connection" }]}
              onAccessibilityAction={(event) => {
                if (event.nativeEvent.actionName === "activate") openNewConnectionFromMenu();
              }}
              onPress={openNewConnectionFromMenu}
            >
              <Icon name="plus" size={18} color={theme.text} />
              <Text style={styles.menuItemText} onPress={openNewConnectionFromMenu}>
                New connection
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="home-menu-global-settings"
              style={styles.menuItem}
              accessibilityRole="button"
              accessibilityLabel="Global Settings"
              accessibilityActions={[{ name: "activate", label: "Open Global Settings" }]}
              onAccessibilityAction={(event) => {
                if (event.nativeEvent.actionName === "activate") openGlobalSettingsFromMenu();
              }}
              onPress={openGlobalSettingsFromMenu}
            >
              <Icon name="settings" size={18} color={theme.text} />
              <Text
                style={styles.menuItemText}
                onPress={openGlobalSettingsFromMenu}
              >Global Settings</Text>
            </TouchableOpacity>
            {onOpenDevelopmentSettings ? (
              <TouchableOpacity
                testID="home-menu-development-settings"
                style={styles.menuItem}
                accessibilityRole="button"
                accessibilityLabel="Development Settings"
                accessibilityActions={[{ name: "activate", label: "Open Development Settings" }]}
                onAccessibilityAction={(event) => {
                  if (event.nativeEvent.actionName === "activate") openDevelopmentSettingsFromMenu();
                }}
                onPress={openDevelopmentSettingsFromMenu}
              >
                <Icon name="tool" size={18} color={theme.text} />
                <Text style={styles.menuItemText} onPress={openDevelopmentSettingsFromMenu}>
                  Development Settings
                </Text>
              </TouchableOpacity>
            ) : null}
            {onOpenEmbeddedSettings ? (
              <TouchableOpacity
                testID="home-menu-embedded-settings"
                style={styles.menuItem}
                accessibilityRole="button"
                accessibilityLabel="Local provider settings"
                accessibilityActions={[{ name: "activate", label: "Open Local provider settings" }]}
                onAccessibilityAction={(event) => {
                  if (event.nativeEvent.actionName === "activate") openEmbeddedSettingsFromMenu();
                }}
                onPress={openEmbeddedSettingsFromMenu}
              >
                <Icon name="cpu" size={18} color={theme.text} />
                <Text
                  testID="home-menu-embedded-settings-label"
                  style={styles.menuItemText}
                  onPress={openEmbeddedSettingsFromMenu}
                >
                  Local provider settings
                </Text>
              </TouchableOpacity>
            ) : null}
            <TouchableOpacity
              testID="home-menu-close"
              style={styles.menuItem}
              onPress={() => setMenuVisible(false)}
            >
              <Icon name="x" size={18} color={theme.textSecondary} />
              <Text style={styles.menuItemText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <SessionNoteModal
        visible={noteSessionId !== null}
        sessionId={noteSessionId}
        note={noteSessionId ? notes[noteSessionId] ?? null : null}
        onSave={(note) => {
          if (noteSessionId) setSessionNote(noteSessionId, note);
        }}
        onRemove={() => {
          if (noteSessionId) removeSessionNote(noteSessionId);
        }}
        onRequestClose={() => setNoteSessionId(null)}
      />
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    container: {
      flex: 1,
    },
    centered: {
      flex: 1,
      alignItems: "center",
      justifyContent: "center",
    },
    header: {
      minHeight: 44,
      flexDirection: "row",
      alignItems: "center",
      marginBottom: 8,
    },
    headerIcon: {
      width: 40,
      height: 40,
      alignItems: "center",
      justifyContent: "center",
    },
    screenTitle: {
      flex: 1,
      color: theme.text,
      fontSize: theme.typography.fontSize.title,
      lineHeight: theme.typography.lineHeight.title,
      fontWeight: "700",
      marginLeft: 4,
    },
    scroll: {
      flex: 1,
    },
    scrollContent: {
      paddingBottom: 24,
    },
    sectionHeader: {
      flexDirection: "row",
      alignItems: "baseline",
      justifyContent: "space-between",
      gap: 12,
      marginBottom: 8,
    },
    recentHeader: {
      marginTop: 22,
    },
    sectionTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.large,
      lineHeight: theme.typography.lineHeight.large,
      fontWeight: "700",
    },
    sectionHint: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
    },
    watchGrid: {
      position: "relative",
      flexDirection: "row",
      flexWrap: "wrap",
      justifyContent: "space-between",
      rowGap: 10,
    },
    watchTile: {
      width: "48.5%",
      minHeight: 172,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 14,
      backgroundColor: theme.surface,
      padding: 10,
      zIndex: 1,
    },
    watchPlaceholder: {
      minHeight: 172,
      borderWidth: 1,
      borderStyle: "dashed",
      borderColor: theme.primary,
      borderRadius: 14,
      backgroundColor: theme.surfaceAlt,
      opacity: 0.6,
    },
    draggedTile: {
      zIndex: 20,
      elevation: 8,
      opacity: 0.94,
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 5 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
    },
    tileTopRow: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 4,
    },
    dragHandle: {
      width: 36,
      height: 32,
      alignItems: "center",
      justifyContent: "center",
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    tileActions: {
      flexDirection: "row",
      alignItems: "center",
    },
    iconButton: {
      width: 36,
      height: 36,
      alignItems: "center",
      justifyContent: "center",
      borderRadius: 8,
    },
    disabledAction: {
      opacity: 0.45,
    },
    tileBody: {
      flex: 1,
    },
    watchTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: "700",
      marginBottom: 3,
    },
    recentTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: "700",
    },
    sessionSubtitle: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      marginBottom: 3,
    },
    sessionId: {
      color: theme.textMuted,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      marginBottom: 5,
    },
    notePreview: {
      color: theme.text,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontStyle: "italic",
      marginTop: 7,
    },
    metadataRow: {
      minWidth: 0,
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      paddingTop: 6,
    },
    watchMetadataRow: {
      marginTop: "auto",
    },
    metadataConnection: {
      minWidth: 0,
      flex: 1,
      color: theme.textMuted,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
    },
    metadataTime: {
      flexShrink: 0,
      color: theme.textMuted,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
    },
    emptyText: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      paddingVertical: 14,
    },
    timelineRow: {
      flexDirection: "row",
      minHeight: 96,
    },
    timelineRail: {
      width: 24,
      alignItems: "center",
    },
    timelineDot: {
      width: 10,
      height: 10,
      marginTop: 7,
      borderRadius: 5,
      backgroundColor: theme.textMuted,
    },
    timelineLine: {
      width: 2,
      flex: 1,
      marginVertical: 4,
      backgroundColor: theme.border,
    },
    timelineBody: {
      flex: 1,
      paddingBottom: 18,
      paddingHorizontal: 8,
    },
    timelineActions: {
      flexDirection: "row",
      alignSelf: "flex-start",
      flexShrink: 0,
    },
    menuOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      paddingTop: 58,
      paddingHorizontal: 16,
    },
    menuPanel: {
      zIndex: 1,
      width: 260,
      borderRadius: 12,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      padding: 10,
    },
    menuTitle: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: "600",
      paddingHorizontal: 8,
      paddingBottom: 6,
    },
    menuItem: {
      minHeight: 44,
      flexDirection: "row",
      alignItems: "center",
      gap: 10,
      paddingHorizontal: 8,
    },
    menuItemText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
  });

export default HomeScreen;
