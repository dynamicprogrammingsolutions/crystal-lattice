import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Animated,
  PanResponder,
  Platform,
  StyleSheet,
  View,
  type LayoutChangeEvent,
  type PanResponderGestureState,
  type ViewProps,
} from 'react-native';

import {
  applyReorderKeyOrder,
  buildReorderRenderSlots,
  moveReorderValues,
  resolveReorderDropTarget,
  resolveReorderDropTranslation,
  useTheme,
  type HomeSessionItem,
  type ReorderItemFrame,
} from '@crystal-lattice/frontend-rn-components';
import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import type { SessionOpenMode } from '../settings/desktopGlobalSettings';
import { MacDragView, type MacDragEvent } from '../native/MacDragView';
import { DesktopSessionCollectionItem } from './DesktopSessionCollectionItem';

interface ActiveDrag {
  phase: 'dragging' | 'settling';
  key: string;
  sourceIndex: number;
  targetIndex: number;
  sourceKeys: string[];
  targetKeys: string[] | null;
  sourceFrame: ReorderItemFrame;
  frames: ReorderItemFrame[];
}

function nativeDragGesture(event: MacDragEvent): PanResponderGestureState {
  return {
    dx: event.translationX,
    dy: event.translationY,
    moveX: event.pageX,
    moveY: event.pageY,
  } as PanResponderGestureState;
}

export function DesktopWatchlistGrid({
  items,
  statuses,
  selectedKey,
  doubleClickAction,
  onSelect,
  onOpen,
  onRemove,
  onEditNote,
  onMove,
}: {
  items: HomeSessionItem[];
  statuses: Readonly<
    Record<string, Readonly<Record<string, SessionRequestStatus>>>
  >;
  selectedKey: string | null;
  doubleClickAction: SessionOpenMode;
  onSelect: (key: string) => void;
  onOpen: (item: HomeSessionItem, mode: SessionOpenMode) => void;
  onRemove: (item: HomeSessionItem) => void;
  onEditNote: (item: HomeSessionItem) => void;
  onMove: (fromIndex: number, toIndex: number) => void;
}): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const framesRef = useRef<Record<string, ReorderItemFrame>>({});
  const translation = useRef(new Animated.ValueXY()).current;
  const activeRef = useRef<ActiveDrag | null>(null);
  const [active, setActive] = useState<ActiveDrag | null>(null);
  const keyedItems = useMemo(
    () => items.map(item => ({ ...item, key: item.key })),
    [items],
  );
  const sourceItems = useMemo(
    () =>
      active ? applyReorderKeyOrder(keyedItems, active.sourceKeys) : keyedItems,
    [active, keyedItems],
  );
  const slots = useMemo(
    () =>
      active
        ? buildReorderRenderSlots(
            sourceItems,
            active.sourceIndex,
            active.targetIndex,
          )
        : sourceItems.map(item => ({
            kind: 'item' as const,
            item,
          })),
    [active, sourceItems],
  );

  useEffect(() => {
    if (!active || active.phase !== 'settling') return;
    const currentKeys = items.map(item => item.key);
    const sourceMatches =
      currentKeys.length === active.sourceKeys.length &&
      currentKeys.every((key, index) => key === active.sourceKeys[index]);
    const targetMatches =
      !!active.targetKeys &&
      currentKeys.length === active.targetKeys.length &&
      currentKeys.every((key, index) => key === active.targetKeys?.[index]);
    if (targetMatches || !sourceMatches) {
      activeRef.current = null;
      setActive(null);
    }
  }, [active, items]);

  useEffect(() => {
    if (!active) translation.setValue({ x: 0, y: 0 });
  }, [active, translation]);

  const start = useCallback(
    (key: string, sourceIndex: number, gesture: PanResponderGestureState) => {
      const frames = items.map(item => framesRef.current[item.key]);
      if (frames.some(frame => !frame)) return;
      const next: ActiveDrag = {
        phase: 'dragging',
        key,
        sourceIndex,
        targetIndex: sourceIndex,
        sourceKeys: items.map(item => item.key),
        targetKeys: null,
        sourceFrame: frames[sourceIndex],
        frames,
      };
      activeRef.current = next;
      translation.setValue({ x: gesture.dx, y: gesture.dy });
      setActive(next);
    },
    [items, translation],
  );

  const move = useCallback(
    (gesture: PanResponderGestureState) => {
      const current = activeRef.current;
      if (!current) return;
      translation.setValue({ x: gesture.dx, y: gesture.dy });
      const targetIndex = resolveReorderDropTarget(
        current.frames,
        current.sourceIndex,
        gesture.dx,
        gesture.dy,
      );
      if (targetIndex !== current.targetIndex) {
        const next = { ...current, targetIndex };
        activeRef.current = next;
        setActive(next);
      }
    },
    [translation],
  );

  const release = useCallback(
    (gesture: PanResponderGestureState) => {
      move(gesture);
      const settled = activeRef.current;
      activeRef.current = null;
      if (!settled || settled.sourceIndex === settled.targetIndex) {
        setActive(null);
        return;
      }
      const targetKeys = moveReorderValues(
        settled.sourceKeys,
        settled.sourceIndex,
        settled.targetIndex,
      );
      translation.setValue(
        resolveReorderDropTranslation(
          settled.frames,
          settled.sourceIndex,
          settled.targetIndex,
        ),
      );
      setActive({
        ...settled,
        phase: 'settling',
        targetKeys,
      });
      onMove(settled.sourceIndex, settled.targetIndex);
    },
    [move, onMove, translation],
  );

  return (
    <View style={styles.grid} testID="desktop-home-watchlist">
      {slots.map(slot => {
        if (slot.kind === 'placeholder') {
          return active ? (
            <View
              key={`placeholder-${active.key}`}
              testID={`desktop-watchlist-placeholder-${active.key}`}
              style={[
                styles.placeholder,
                {
                  width: active.sourceFrame.width,
                  height: active.sourceFrame.height,
                },
              ]}
            />
          ) : null;
        }
        const item = slot.item;
        const index = sourceItems.findIndex(
          candidate => candidate.key === item.key,
        );
        const isDragged = slot.kind === 'dragged';
        return (
          <WatchlistDragHost
            key={item.key}
            frame={isDragged ? active?.sourceFrame : undefined}
            translation={isDragged ? translation : undefined}
            dragging={isDragged}
            onLayout={event => {
              if (isDragged) return;
              framesRef.current[item.key] = event.nativeEvent.layout;
            }}
            onStart={gesture => start(item.key, index, gesture)}
            onMove={move}
            onRelease={release}
            onCancel={() => {
              activeRef.current = null;
              setActive(null);
            }}
            renderHandle={panHandlers => (
              <DesktopSessionCollectionItem
                item={item}
                variant="tile"
                selected={selectedKey === item.key}
                status={statuses[item.connectionId]?.[item.sessionId] ?? null}
                doubleClickAction={doubleClickAction}
                watched
                onSelect={() => onSelect(item.key)}
                onOpen={mode => onOpen(item, mode)}
                onToggleWatch={() => onRemove(item)}
                onEditNote={() => onEditNote(item)}
                onMoveEarlier={
                  index > 0 ? () => onMove(index, index - 1) : undefined
                }
                onMoveLater={
                  index < sourceItems.length - 1
                    ? () => onMove(index, index + 1)
                    : undefined
                }
                dragHandleProps={panHandlers}
              />
            )}
          />
        );
      })}
    </View>
  );
}

function WatchlistDragHost({
  frame,
  translation,
  dragging,
  onLayout,
  onStart,
  onMove,
  onRelease,
  onCancel,
  renderHandle,
}: {
  frame?: ReorderItemFrame;
  translation?: Animated.ValueXY;
  dragging: boolean;
  onLayout: (event: LayoutChangeEvent) => void;
  onStart: (gesture: PanResponderGestureState) => void;
  onMove: (gesture: PanResponderGestureState) => void;
  onRelease: (gesture: PanResponderGestureState) => void;
  onCancel: () => void;
  renderHandle: (panHandlers: ViewProps) => React.ReactNode;
}) {
  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: (_event, gesture) => onStart(gesture),
        onPanResponderMove: (_event, gesture) => onMove(gesture),
        onPanResponderRelease: (_event, gesture) => onRelease(gesture),
        onPanResponderTerminate: onCancel,
        onPanResponderTerminationRequest: () => false,
      }),
    [onCancel, onMove, onRelease, onStart],
  );
  const content = renderHandle(
    Platform.OS === 'macos' ? {} : panResponder.panHandlers,
  );
  return (
    <Animated.View
      {...({ mouseDownCanMoveWindow: false } as any)}
      onLayout={!dragging ? onLayout : undefined}
      style={[
        stylesStatic.wrapper,
        dragging && frame
          ? {
              position: 'absolute',
              left: frame.x,
              top: frame.y,
              width: frame.width,
              height: frame.height,
              zIndex: 100,
              transform: translation?.getTranslateTransform(),
            }
          : null,
      ]}
    >
      {Platform.OS === 'macos' ? (
        <MacDragView
          mouseDownCanMoveWindow={false}
          onDragStart={event => onStart(nativeDragGesture(event))}
          onDragMove={event => onMove(nativeDragGesture(event))}
          onDragEnd={event => onRelease(nativeDragGesture(event))}
          onDragCancel={onCancel}
        >
          {content}
        </MacDragView>
      ) : (
        content
      )}
    </Animated.View>
  );
}

const stylesStatic = StyleSheet.create({
  wrapper: {
    width: '48.7%',
  },
});

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    grid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
      position: 'relative',
    },
    placeholder: {
      borderWidth: 1,
      borderStyle: 'dashed',
      borderColor: theme.primary,
      borderRadius: 12,
      backgroundColor: theme.primaryMuted,
    },
  });
}
