import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Animated,
  type GestureResponderEvent,
  type LayoutChangeEvent,
  Modal,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  PanResponder,
  type PanResponderGestureState,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type {
  ConnectionRecord,
  SessionRequestStatus,
} from '@crystal-lattice/frontend-sdk';
import {
  ActionsMenuBar,
  type ActionDefinition,
} from '@crystal-lattice/frontend-rn-components';

import type { SessionsCache } from '../App';
import { useHomeWorkspace } from './HomeWorkspaceContext';
import {
  deriveHomeSessionCollections,
  type HomeSessionItem,
} from './homeWorkspaceState';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import { useTheme, type Theme } from './theme';
import SessionNoteModal from './components/SessionNoteModal';
import SessionRequestStatusBadge from './components/SessionRequestStatusBadge';
import {
  applyWatchlistKeyOrder,
  buildWatchlistRenderSlots,
  moveWatchlistValues,
  resolveWatchlistDropTranslation,
  resolveWatchlistDropTarget,
  type WatchlistTileFrame,
} from './watchlistDrag';

interface HomeActionDefinition extends ActionDefinition {
  iconName: string;
}

const HOME_ACTIONS: HomeActionDefinition[] = [
  { key: 'settings', label: 'Global settings', iconName: 'settings' },
  {
    key: 'embeddedSettings',
    label: 'On-device providers',
    iconName: 'cpu',
    testID: 'home-embedded-settings',
  },
  { key: 'newConnection', label: 'New connection', iconName: 'wifi' },
  { key: 'newSession', label: 'New session', iconName: 'plus' },
];

interface HomeScreenProps {
  connections: readonly ConnectionRecord[];
  sessionsCache: SessionsCache;
  statusesByConnection: Readonly<
    Record<string, Readonly<Record<string, SessionRequestStatus>>>
  >;
  hasActiveBackend: boolean;
  isActive: boolean;
  onOpenGlobalSettings: () => void;
  onOpenEmbeddedSettings?: () => void;
  onNewConnection: () => void;
  onNewSession: () => void;
  onSelectSession: (connectionId: string, sessionId: string) => void;
}

function sessionTitle(item: HomeSessionItem): string {
  return (
    item.summary.presentation?.title ||
    item.summary.preview?.split('\n')[0]?.trim() ||
    item.sessionId
  );
}

function relativeModified(modified: number): string {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - modified));
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
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
          gesture: PanResponderGestureState,
        ) => {
          const pageY = event.nativeEvent.pageY;
          onDragMove(gesture, Number.isFinite(pageY) ? pageY : null);
        },
        onPanResponderRelease: (_event, gesture) => onDragRelease(gesture),
        onPanResponderTerminate: onDragCancel,
        onPanResponderTerminationRequest: () => false,
        onShouldBlockNativeResponder: () => true,
      }),
    [item.key, onDragCancel, onDragMove, onDragRelease, onDragStart],
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
            position: 'absolute',
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
          accessibilityLabel={`Reorder ${sessionTitle(item)}`}
          accessibilityActions={[
            { name: 'increment', label: 'Move later' },
            { name: 'decrement', label: 'Move earlier' },
          ]}
          onAccessibilityAction={(event) => {
            if (event.nativeEvent.actionName === 'increment') {
              onMove(index, Math.min(itemCount - 1, index + 1));
            } else if (event.nativeEvent.actionName === 'decrement') {
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
              item.note ? 'Edit session note' : 'Add session note'
            }
            style={styles.iconButton}
            onPress={onEditNote}
          >
            <Icon
              name={item.note ? 'edit-3' : 'file-plus'}
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
        <Text style={styles.watchTitle} numberOfLines={2}>
          {sessionTitle(item)}
        </Text>
        <Text style={styles.connectionName} numberOfLines={1}>
          {item.connection.name}
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
        <Text style={styles.relativeTime}>
          {relativeModified(item.summary.modified)}
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
};

interface ActiveWatchlistDrag {
  phase: 'dragging' | 'settling';
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
  right: readonly string[],
): boolean {
  return (
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  );
}

const HomeScreen: React.FC<HomeScreenProps> = ({
  connections,
  sessionsCache,
  statusesByConnection,
  hasActiveBackend,
  isActive,
  onOpenGlobalSettings,
  onOpenEmbeddedSettings,
  onNewConnection,
  onNewSession,
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
  const { pinned, setPinned } = usePersistentPinnedActions<string>(
    'clc_pinned_home_actions_v1',
    ['settings', 'embeddedSettings', 'newConnection'],
  );
  const derivedCollections = useMemo(
    () =>
      deriveHomeSessionCollections({
        connections,
        sessionsCache,
        watchlist,
        notes,
        recentSessionsWindow,
      }),
    [connections, notes, recentSessionsWindow, sessionsCache, watchlist],
  );
  const [menuVisible, setMenuVisible] = useState(false);
  const [noteSessionId, setNoteSessionId] = useState<string | null>(null);
  const [activeDrag, setActiveDrag] = useState<ActiveWatchlistDrag | null>(
    null,
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
              settledWatchlistOrder.targetKeys,
            ),
          }
        : derivedCollections,
    [derivedCollections, settledWatchlistOrder],
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
        current?.phase === 'settling' ? null : current,
      );
    }
  }, [derivedCollections.watchlist, settledWatchlistOrder]);
  const activeDragRef = useRef<ActiveWatchlistDrag | null>(null);
  const tileFramesRef = useRef<Record<string, WatchlistTileFrame>>({});
  const dragTranslation = useRef(new Animated.ValueXY()).current;
  const scrollViewRef = useRef<ScrollView | null>(null);
  const embeddedSettingsOpeningRef = useRef(false);
  const scrollOffsetRef = useRef(0);
  const scrollViewportRef = useRef<ScrollViewport | null>(null);
  const scrollContentHeightRef = useRef(0);
  const watchlistItems = useMemo(
    () =>
      activeDrag
        ? applyWatchlistKeyOrder(
            derivedCollections.watchlist,
            activeDrag.sourceKeys,
          )
        : collections.watchlist,
    [activeDrag, collections.watchlist, derivedCollections.watchlist],
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
        translationY,
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
    [dragTranslation],
  );

  const startWatchlistDrag = useCallback(
    (key: string) => {
      const currentItems = collectionsRef.current.watchlist;
      const sourceIndex = currentItems.findIndex((item) => item.key === key);
      const slotFrames = currentItems.map(
        (item) => tileFramesRef.current[item.key],
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
        phase: 'dragging',
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
    [dragTranslation],
  );

  const autoScrollForDrag = useCallback((pageY: number | null) => {
    const viewport = scrollViewportRef.current;
    if (pageY === null || !viewport) return;
    const maxOffset = Math.max(
      0,
      scrollContentHeightRef.current - viewport.height,
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
      Math.min(maxOffset, scrollOffsetRef.current + delta),
    );
    if (nextOffset === scrollOffsetRef.current) return;
    scrollViewRef.current?.scrollTo({ y: nextOffset, animated: false });
  }, []);

  const moveWatchlistDrag = useCallback(
    (gesture: PanResponderGestureState, pageY: number | null) => {
      updateDragPosition(gesture.dx, gesture.dy);
      autoScrollForDrag(pageY);
    },
    [autoScrollForDrag, updateDragPosition],
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
          settled.targetIndex,
        );
        dragTranslation.setValue(
          resolveWatchlistDropTranslation(
            settled.slotFrames,
            settled.sourceIndex,
            settled.targetIndex,
          ),
        );
        setActiveDrag({
          ...settled,
          phase: 'settling',
          targetIndex: settled.targetIndex,
        });
        setSettledWatchlistOrder({ sourceKeys, targetKeys });
        moveWatchlistItem(settled.sourceIndex, settled.targetIndex);
      } else {
        setActiveDrag(null);
      }
    },
    [dragTranslation, moveWatchlistItem, updateDragPosition],
  );

  const cancelWatchlistDrag = useCallback(() => {
    activeDragRef.current = null;
    setActiveDrag(null);
  }, []);

  const recordTileFrame = useCallback(
    (key: string, event: LayoutChangeEvent) => {
      tileFramesRef.current[key] = event.nativeEvent.layout;
    },
    [],
  );

  const handleHomeScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      scrollOffsetRef.current = event.nativeEvent.contentOffset.y;
      const current = activeDragRef.current;
      if (current) {
        updateDragPosition(current.gestureX, current.gestureY);
      }
    },
    [updateDragPosition],
  );

  const measureScrollViewport = useCallback(() => {
    scrollViewRef.current
      ?.getNativeScrollRef()
      ?.measureInWindow((_x, y, _width, height) => {
        scrollViewportRef.current = { y, height };
      });
  }, []);

  const openEmbeddedSettingsFromMenu = useCallback(() => {
    if (!onOpenEmbeddedSettings || embeddedSettingsOpeningRef.current) {
      return;
    }
    embeddedSettingsOpeningRef.current = true;
    setMenuVisible(false);
    setTimeout(() => {
      onOpenEmbeddedSettings();
      embeddedSettingsOpeningRef.current = false;
    }, 300);
  }, [onOpenEmbeddedSettings]);

  const watchlistRenderSlots = useMemo(
    () =>
      activeDrag
        ? buildWatchlistRenderSlots(
            watchlistItems,
            activeDrag.sourceIndex,
            activeDrag.targetIndex,
          )
        : watchlistItems.map((item) => ({
            kind: 'item' as const,
            item,
          })),
    [activeDrag, watchlistItems],
  );
  const recentWindowLabel =
    recentSessionsWindow === '24h'
      ? 'Last 24 hours'
      : recentSessionsWindow === '1w'
      ? 'Last week'
      : 'Last 3 days';

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
          accessibilityLabel="Open Home menu"
          style={styles.headerIcon}
          onPress={() => setMenuVisible(true)}
        >
          <Icon name="menu" size={21} color={theme.text} />
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Home</Text>
        <View style={styles.homeActions}>
          <ActionsMenuBar<HomeActionDefinition>
            title="Home actions"
            baseActions={HOME_ACTIONS}
            availableActions={
              onOpenEmbeddedSettings
                ? ['settings', 'embeddedSettings', 'newConnection', 'newSession']
                : ['settings', 'newConnection', 'newSession']
            }
            pinned={pinned}
            onChangePinned={setPinned}
            isActive={isActive}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            renderPinIcon={({ size, color }) => (
              <Icon name="star" size={size} color={color} />
            )}
            menuButtonTestID="home-actions-menu"
            isActionDisabled={(key) =>
              key === 'newSession' && !hasActiveBackend
            }
            onAction={(key) => {
              if (key === 'settings') onOpenGlobalSettings();
              if (key === 'embeddedSettings') onOpenEmbeddedSettings?.();
              if (key === 'newConnection') onNewConnection();
              if (key === 'newSession') onNewSession();
            }}
          />
        </View>
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
              if (slot.kind === 'placeholder') {
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
              if (slot.kind === 'dragged') {
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
                (candidate) => candidate.key === item.key,
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
            {collections.recent.map((item, index) => (
              <View
                key={item.key}
                style={styles.timelineRow}
                testID={`home-recent-${item.connectionId}-${item.sessionId}`}
              >
                <View style={styles.timelineRail}>
                  <View style={styles.timelineDot} />
                  {index < collections.recent.length - 1 ? (
                    <View style={styles.timelineLine} />
                  ) : null}
                </View>
                <TouchableOpacity
                  testID={`home-recent-open-${item.connectionId}-${item.sessionId}`}
                  style={styles.timelineBody}
                  onPress={() =>
                    onSelectSession(item.connectionId, item.sessionId)
                  }
                >
                  <Text style={styles.recentTitle} numberOfLines={2}>
                    {sessionTitle(item)}
                  </Text>
                  <Text style={styles.connectionName} numberOfLines={1}>
                    {item.connection.name} ·{' '}
                    {relativeModified(item.summary.modified)}
                  </Text>
                  <SessionRequestStatusBadge
                    status={
                      statusesByConnection[item.connectionId]?.[
                        item.sessionId
                      ] ?? null
                    }
                    testID={`home-recent-status-${item.connectionId}-${item.sessionId}`}
                  />
                  {item.note ? (
                    <Text style={styles.notePreview} numberOfLines={2}>
                      {item.note}
                    </Text>
                  ) : null}
                </TouchableOpacity>
                <View style={styles.timelineActions}>
                  <TouchableOpacity
                    testID={`home-recent-note-${item.connectionId}-${item.sessionId}`}
                    accessibilityLabel={
                      item.note ? 'Edit session note' : 'Add session note'
                    }
                    style={styles.iconButton}
                    onPress={() => setNoteSessionId(item.sessionId)}
                  >
                    <Icon
                      name={item.note ? 'edit-3' : 'file-plus'}
                      size={17}
                      color={theme.primary}
                    />
                  </TouchableOpacity>
                  <TouchableOpacity
                    testID={`home-recent-watch-${item.connectionId}-${item.sessionId}`}
                    accessibilityLabel={
                      isWatched(item.connectionId, item.sessionId)
                        ? 'In Watchlist'
                        : 'Add to Watchlist'
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
            ))}
          </View>
        )}
      </ScrollView>

      <Modal
        visible={menuVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setMenuVisible(false)}
      >
        <View style={styles.menuOverlay}>
          <View style={styles.menuPanel}>
            <Text style={styles.menuTitle}>Home menu</Text>
            <TouchableOpacity
              testID="home-menu-global-settings"
              style={styles.menuItem}
              onPress={() => {
                setMenuVisible(false);
                onOpenGlobalSettings();
              }}
            >
              <Icon name="settings" size={18} color={theme.text} />
              <Text style={styles.menuItemText}>Global Settings</Text>
            </TouchableOpacity>
            {onOpenEmbeddedSettings ? (
              <TouchableOpacity
                testID="home-menu-embedded-settings"
                style={styles.menuItem}
                accessibilityRole="button"
                onPress={openEmbeddedSettingsFromMenu}
              >
                <Icon name="cpu" size={18} color={theme.text} />
                <Text
                  testID="home-menu-embedded-settings-label"
                  style={styles.menuItemText}
                  onPress={openEmbeddedSettingsFromMenu}
                >
                  On-device Provider Settings
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
      alignItems: 'center',
      justifyContent: 'center',
    },
    header: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    headerIcon: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
    },
    screenTitle: {
      flex: 1,
      color: theme.text,
      fontSize: theme.typography.fontSize.title,
      lineHeight: theme.typography.lineHeight.title,
      fontWeight: '700',
      marginLeft: 4,
    },
    homeActions: {
      flexShrink: 1,
    },
    scroll: {
      flex: 1,
    },
    scrollContent: {
      paddingBottom: 24,
    },
    sectionHeader: {
      flexDirection: 'row',
      alignItems: 'baseline',
      justifyContent: 'space-between',
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
      fontWeight: '700',
    },
    sectionHint: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
    },
    watchGrid: {
      position: 'relative',
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      rowGap: 10,
    },
    watchTile: {
      width: '48.5%',
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
      borderStyle: 'dashed',
      borderColor: theme.primary,
      borderRadius: 14,
      backgroundColor: theme.surfaceAlt,
      opacity: 0.6,
    },
    draggedTile: {
      zIndex: 20,
      elevation: 8,
      opacity: 0.94,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 5 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
    },
    tileTopRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 4,
    },
    dragHandle: {
      width: 36,
      height: 32,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    tileActions: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    iconButton: {
      width: 36,
      height: 36,
      alignItems: 'center',
      justifyContent: 'center',
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
      fontWeight: '700',
      marginBottom: 3,
    },
    recentTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.large,
      lineHeight: theme.typography.lineHeight.large,
      fontWeight: '600',
    },
    connectionName: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      marginBottom: 6,
    },
    notePreview: {
      color: theme.text,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontStyle: 'italic',
      marginTop: 7,
    },
    relativeTime: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      marginTop: 'auto',
      paddingTop: 6,
    },
    emptyText: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      paddingVertical: 14,
    },
    timelineRow: {
      flexDirection: 'row',
      minHeight: 96,
    },
    timelineRail: {
      width: 24,
      alignItems: 'center',
    },
    timelineDot: {
      width: 10,
      height: 10,
      marginTop: 7,
      borderRadius: 5,
      backgroundColor: theme.primary,
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
      flexDirection: 'row',
      alignSelf: 'flex-start',
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
      fontWeight: '600',
      paddingHorizontal: 8,
      paddingBottom: 6,
    },
    menuItem: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
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
