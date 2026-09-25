import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  ActionSheetIOS,
  Animated,
  PanResponder,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  findNodeHandle,
  type GestureResponderEvent,
  type LayoutChangeEvent,
  type PanResponderGestureState,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  DropdownMenuSurface,
  SessionRequestStatusIndicator,
  applyReorderKeyOrder,
  buildReorderRenderSlots,
  moveReorderValues,
  resolveReorderDropTarget,
  resolveReorderDropTranslation,
  useTheme,
  type ReorderItemFrame,
} from '@crystal-lattice/frontend-rn-components';
import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import type { TabStripStyle } from './tabStripStyle';
import type { DesktopSessionTab } from './desktopWorkspaceState';
import { MacDragView, type MacDragEvent } from '../native/MacDragView';

export type { DesktopSessionTab } from './desktopWorkspaceState';

interface ActiveTabDrag {
  phase: 'dragging' | 'settling';
  key: string;
  sourceIndex: number;
  targetIndex: number;
  sourceKeys: string[];
  targetKeys: string[] | null;
  sourceFrame: ReorderItemFrame;
  slotFrames: ReorderItemFrame[];
  startScrollX: number;
}

function nativeDragGesture(event: MacDragEvent): PanResponderGestureState {
  return {
    dx: event.translationX,
    dy: event.translationY,
    moveX: event.pageX,
    moveY: event.pageY,
  } as PanResponderGestureState;
}

export interface SessionTabsProps {
  permanentTabs?: DesktopSessionTab[];
  /** Compatibility input for callers that have not adopted preview state. */
  tabs?: DesktopSessionTab[];
  previewTab?: DesktopSessionTab | null;
  homeActive?: boolean;
  activeTabId: string | null;
  styleVariant: TabStripStyle;
  connectionNameById: Record<string, string>;
  requestStatuses?: Readonly<
    Record<string, Readonly<Record<string, SessionRequestStatus>>>
  >;
  onSelectHome?: () => void;
  onSelectTab: (tabId: string) => void;
  onCloseTab: (tabId: string) => void;
  onPromotePreview?: (tabId: string) => void;
  onReorderPermanent?: (fromIndex: number, toIndex: number) => void;
}

export function SessionTabs({
  permanentTabs,
  tabs: compatibilityTabs,
  previewTab = null,
  homeActive = false,
  activeTabId,
  styleVariant,
  connectionNameById,
  requestStatuses = {},
  onSelectHome = () => {},
  onSelectTab,
  onCloseTab,
  onPromotePreview = () => {},
  onReorderPermanent = () => {},
}: SessionTabsProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(
    () => createStyles(theme, styleVariant),
    [theme, styleVariant],
  );
  const [hoveredTabId, setHoveredTabId] = useState<string | null>(null);
  const [activeDrag, setActiveDrag] = useState<ActiveTabDrag | null>(null);
  const activeDragRef = useRef<ActiveTabDrag | null>(null);
  const framesRef = useRef<Record<string, ReorderItemFrame>>({});
  const translation = useRef(new Animated.ValueXY()).current;
  const scrollRef = useRef<ScrollView>(null);
  const scrollXRef = useRef(0);
  const contentWidthRef = useRef(0);
  const viewportRef = useRef({ x: 0, width: 0 });
  const lastPreviewClickRef = useRef<{ tabId: string; atMs: number } | null>(
    null,
  );

  const menuAnchorRef = useRef<any>(null);
  const [menuVisible, setMenuVisible] = useState(false);
  const resolvedPermanentTabs = useMemo(
    () => permanentTabs ?? compatibilityTabs ?? [],
    [compatibilityTabs, permanentTabs],
  );
  const keyedPermanentTabs = useMemo(
    () =>
      resolvedPermanentTabs.map(tab => ({
        ...tab,
        key: tab.tabId,
      })),
    [resolvedPermanentTabs],
  );

  const sourceOrderedTabs = useMemo(
    () =>
      activeDrag
        ? applyReorderKeyOrder(keyedPermanentTabs, activeDrag.sourceKeys)
        : keyedPermanentTabs,
    [activeDrag, keyedPermanentTabs],
  );
  const renderSlots = useMemo(
    () =>
      activeDrag
        ? buildReorderRenderSlots(
            sourceOrderedTabs,
            activeDrag.sourceIndex,
            activeDrag.targetIndex,
          )
        : sourceOrderedTabs.map(item => ({
            kind: 'item' as const,
            item,
          })),
    [activeDrag, sourceOrderedTabs],
  );

  useEffect(() => {
    if (!activeDrag || activeDrag.phase !== 'settling') return;
    const currentKeys = resolvedPermanentTabs.map(tab => tab.tabId);
    const sourceMatches =
      currentKeys.length === activeDrag.sourceKeys.length &&
      currentKeys.every((key, index) => key === activeDrag.sourceKeys[index]);
    const targetMatches =
      !!activeDrag.targetKeys &&
      currentKeys.length === activeDrag.targetKeys.length &&
      currentKeys.every((key, index) => key === activeDrag.targetKeys?.[index]);
    if (targetMatches || !sourceMatches) {
      activeDragRef.current = null;
      setActiveDrag(null);
    }
  }, [activeDrag, resolvedPermanentTabs]);

  useEffect(() => {
    if (!activeDrag) translation.setValue({ x: 0, y: 0 });
  }, [activeDrag, translation]);

  const recordFrame = useCallback((tabId: string, event: LayoutChangeEvent) => {
    const { x, y, width, height } = event.nativeEvent.layout;
    framesRef.current[tabId] = { x, y, width, height };
  }, []);

  const startDrag = useCallback(
    (key: string, index: number, gesture: PanResponderGestureState) => {
      const slotFrames = resolvedPermanentTabs.map(
        tab => framesRef.current[tab.tabId],
      );
      if (
        slotFrames.some(
          frame =>
            !frame ||
            !Number.isFinite(frame.x) ||
            !Number.isFinite(frame.width),
        )
      ) {
        return;
      }
      const sourceFrame = slotFrames[index];
      const next: ActiveTabDrag = {
        phase: 'dragging',
        key,
        sourceIndex: index,
        targetIndex: index,
        sourceKeys: resolvedPermanentTabs.map(tab => tab.tabId),
        targetKeys: null,
        sourceFrame,
        slotFrames,
        startScrollX: scrollXRef.current,
      };
      activeDragRef.current = next;
      translation.setValue({ x: gesture.dx, y: 0 });
      setActiveDrag(next);
    },
    [resolvedPermanentTabs, translation],
  );

  const moveDrag = useCallback(
    (gesture: PanResponderGestureState) => {
      const current = activeDragRef.current;
      if (!current) return;
      const scrollDelta = scrollXRef.current - current.startScrollX;
      const translationX = gesture.dx + scrollDelta;
      translation.setValue({ x: translationX, y: 0 });
      const targetIndex = resolveReorderDropTarget(
        current.slotFrames,
        current.sourceIndex,
        translationX,
        0,
      );
      if (targetIndex !== current.targetIndex) {
        const next = { ...current, targetIndex };
        activeDragRef.current = next;
        setActiveDrag(next);
      }

      const { x, width } = viewportRef.current;
      const maxScroll = Math.max(0, contentWidthRef.current - width);
      let nextScroll = scrollXRef.current;
      if (gesture.moveX < x + 32) nextScroll -= 18;
      if (gesture.moveX > x + width - 32) nextScroll += 18;
      nextScroll = Math.max(0, Math.min(maxScroll, nextScroll));
      if (nextScroll !== scrollXRef.current) {
        scrollXRef.current = nextScroll;
        scrollRef.current?.scrollTo({ x: nextScroll, animated: false });
      }
    },
    [translation],
  );

  const releaseDrag = useCallback(
    (gesture: PanResponderGestureState) => {
      moveDrag(gesture);
      const settled = activeDragRef.current;
      activeDragRef.current = null;
      if (!settled || settled.sourceIndex === settled.targetIndex) {
        setActiveDrag(null);
        return;
      }
      const targetKeys = moveReorderValues(
        settled.sourceKeys,
        settled.sourceIndex,
        settled.targetIndex,
      );
      translation.setValue(
        resolveReorderDropTranslation(
          settled.slotFrames,
          settled.sourceIndex,
          settled.targetIndex,
        ),
      );
      const next = {
        ...settled,
        phase: 'settling' as const,
        targetKeys,
      };
      setActiveDrag(next);
      onReorderPermanent(settled.sourceIndex, settled.targetIndex);
    },
    [moveDrag, onReorderPermanent, translation],
  );

  const cancelDrag = useCallback(() => {
    activeDragRef.current = null;
    setActiveDrag(null);
  }, []);

  const openNativeMenu = () => {
    const options = ['Tab actions (placeholder)', 'Cancel'];
    const cancelButtonIndex = options.length - 1;
    let anchor: number | null = null;
    if (menuAnchorRef.current) {
      try {
        anchor = findNodeHandle(menuAnchorRef.current) as any;
      } catch {
        anchor = null;
      }
    }
    ActionSheetIOS.showActionSheetWithOptions(
      { options, cancelButtonIndex, anchor: anchor ?? undefined },
      () => {},
    );
  };

  const handlePreviewPress = (tabId: string) => {
    onSelectTab(tabId);
    const now = Date.now();
    const previous = lastPreviewClickRef.current;
    lastPreviewClickRef.current = { tabId, atMs: now };
    if (previous?.tabId === tabId && now - previous.atMs <= 350) {
      lastPreviewClickRef.current = null;
      onPromotePreview(tabId);
    }
  };

  return (
    <View style={styles.root} testID="desktop-session-tab-strip">
      <Pressable
        testID="desktop-home-tab"
        accessibilityRole="button"
        accessibilityLabel="Home"
        accessibilityState={{ selected: homeActive }}
        style={[
          styles.homeTab,
          homeActive ? styles.tabActive : styles.tabInactive,
        ]}
        onPress={onSelectHome}
      >
        <Icon
          name="home"
          size={17}
          color={homeActive ? theme.primary : theme.textSecondary}
        />
      </Pressable>
      <ScrollView
        ref={scrollRef}
        horizontal
        scrollEnabled={!activeDrag}
        showsHorizontalScrollIndicator={false}
        style={styles.scrollView}
        contentContainerStyle={styles.tabsContainer}
        scrollEventThrottle={16}
        onLayout={event => {
          const width = event.nativeEvent.layout.width;
          (event.currentTarget as any)?.measureInWindow?.((x: number) => {
            viewportRef.current = { x, width };
          });
          viewportRef.current = { ...viewportRef.current, width };
        }}
        onContentSizeChange={width => {
          contentWidthRef.current = width;
        }}
        onScroll={event => {
          scrollXRef.current = event.nativeEvent.contentOffset.x;
        }}
      >
        {renderSlots.map((slot, slotIndex) => {
          if (slot.kind === 'placeholder') {
            return activeDrag ? (
              <View
                key={`placeholder-${activeDrag.key}`}
                testID={`desktop-tab-placeholder-${activeDrag.key}`}
                style={[
                  styles.placeholder,
                  {
                    width: activeDrag.sourceFrame.width,
                    height: activeDrag.sourceFrame.height,
                  },
                ]}
              />
            ) : null;
          }
          const tab = slot.item;
          const storedIndex = sourceOrderedTabs.findIndex(
            candidate => candidate.tabId === tab.tabId,
          );
          const isDragged = slot.kind === 'dragged';
          return (
            <SessionTabItem
              key={tab.tabId}
              tab={tab}
              index={storedIndex >= 0 ? storedIndex : slotIndex}
              itemCount={sourceOrderedTabs.length}
              active={tab.tabId === activeTabId}
              hovered={tab.tabId === hoveredTabId}
              preview={false}
              status={
                requestStatuses[tab.connectionId]?.[tab.sessionId] ?? null
              }
              connectionName={
                connectionNameById[tab.connectionId] ?? tab.connectionId
              }
              styleVariant={styleVariant}
              styles={styles}
              isDragging={isDragged}
              dragFrame={isDragged ? activeDrag?.sourceFrame : undefined}
              translation={isDragged ? translation : undefined}
              onLayout={event => recordFrame(tab.tabId, event)}
              onPress={() => onSelectTab(tab.tabId)}
              onHoverIn={() => setHoveredTabId(tab.tabId)}
              onHoverOut={() =>
                setHoveredTabId(current =>
                  current === tab.tabId ? null : current,
                )
              }
              onClose={() => onCloseTab(tab.tabId)}
              onDragStart={gesture =>
                startDrag(tab.tabId, storedIndex, gesture)
              }
              onDragMove={moveDrag}
              onDragRelease={releaseDrag}
              onDragCancel={cancelDrag}
              onMoveAccessible={direction => {
                const target = storedIndex + direction;
                if (target >= 0 && target < resolvedPermanentTabs.length) {
                  onReorderPermanent(storedIndex, target);
                }
              }}
            />
          );
        })}
        {previewTab ? (
          <SessionTabItem
            key={`preview-${previewTab.tabId}`}
            tab={previewTab}
            index={resolvedPermanentTabs.length}
            itemCount={resolvedPermanentTabs.length + 1}
            active={previewTab.tabId === activeTabId}
            hovered={previewTab.tabId === hoveredTabId}
            preview
            status={
              requestStatuses[previewTab.connectionId]?.[
                previewTab.sessionId
              ] ?? null
            }
            connectionName={
              connectionNameById[previewTab.connectionId] ??
              previewTab.connectionId
            }
            styleVariant={styleVariant}
            styles={styles}
            onPress={() => handlePreviewPress(previewTab.tabId)}
            onHoverIn={() => setHoveredTabId(previewTab.tabId)}
            onHoverOut={() =>
              setHoveredTabId(current =>
                current === previewTab.tabId ? null : current,
              )
            }
            onClose={() => onCloseTab(previewTab.tabId)}
          />
        ) : null}
      </ScrollView>

      <View ref={menuAnchorRef} collapsable={false}>
        <Pressable
          style={styles.menuButton}
          onPress={() => {
            if (Platform.OS === 'macos') openNativeMenu();
            else setMenuVisible(true);
          }}
        >
          <Text style={styles.menuButtonText}>⋯</Text>
        </Pressable>
      </View>
      {Platform.OS !== 'macos' ? (
        <DropdownMenuSurface
          visible={menuVisible}
          onRequestClose={() => setMenuVisible(false)}
          anchorRef={menuAnchorRef}
          offset={{ y: 6 }}
        >
          <Pressable onPress={() => setMenuVisible(false)}>
            <Text>Tab actions (placeholder)</Text>
          </Pressable>
        </DropdownMenuSurface>
      ) : null}
    </View>
  );
}

function SessionTabItem({
  tab,
  index,
  itemCount,
  active,
  hovered,
  preview,
  status,
  connectionName,
  styles,
  isDragging = false,
  dragFrame,
  translation,
  onLayout,
  onPress,
  onHoverIn,
  onHoverOut,
  onClose,
  onDragStart,
  onDragMove,
  onDragRelease,
  onDragCancel,
  onMoveAccessible,
}: {
  tab: DesktopSessionTab;
  index: number;
  itemCount: number;
  active: boolean;
  hovered: boolean;
  preview: boolean;
  status: SessionRequestStatus | null;
  connectionName: string;
  styleVariant: TabStripStyle;
  styles: ReturnType<typeof createStyles>;
  isDragging?: boolean;
  dragFrame?: ReorderItemFrame;
  translation?: Animated.ValueXY;
  onLayout?: (event: LayoutChangeEvent) => void;
  onPress: () => void;
  onHoverIn: () => void;
  onHoverOut: () => void;
  onClose: () => void;
  onDragStart?: (gesture: PanResponderGestureState) => void;
  onDragMove?: (gesture: PanResponderGestureState) => void;
  onDragRelease?: (gesture: PanResponderGestureState) => void;
  onDragCancel?: () => void;
  onMoveAccessible?: (direction: -1 | 1) => void;
}) {
  const dragStartedRef = useRef(false);
  const panResponder = useMemo(() => {
    const shouldCapture = (
      _event: GestureResponderEvent,
      gesture: PanResponderGestureState,
    ) =>
      !preview &&
      Math.abs(gesture.dx) >= 6 &&
      Math.abs(gesture.dx) > Math.abs(gesture.dy);
    return PanResponder.create({
      onStartShouldSetPanResponder: () => !preview,
      onMoveShouldSetPanResponder: shouldCapture,
      onPanResponderGrant: () => {
        dragStartedRef.current = false;
      },
      onPanResponderMove: (event, gesture) => {
        if (!dragStartedRef.current && shouldCapture(event, gesture)) {
          dragStartedRef.current = true;
          onDragStart?.(gesture);
        }
        if (dragStartedRef.current) {
          onDragMove?.(gesture);
        }
      },
      onPanResponderRelease: (_event, gesture) => {
        if (dragStartedRef.current) {
          onDragRelease?.(gesture);
        } else {
          onDragCancel?.();
          onPress();
        }
        dragStartedRef.current = false;
      },
      onPanResponderTerminate: () => {
        dragStartedRef.current = false;
        onDragCancel?.();
      },
      onPanResponderTerminationRequest: () => false,
    });
  }, [onDragCancel, onDragMove, onDragRelease, onDragStart, onPress, preview]);
  const subtitle =
    typeof tab.subtitle === 'string' && tab.subtitle.trim()
      ? tab.subtitle
      : connectionName;
  const showClose = active || hovered || preview;
  const wrapperStyle = [
    isDragging && dragFrame
      ? {
          position: 'absolute' as const,
          left: dragFrame.x,
          top: dragFrame.y,
          width: dragFrame.width,
          height: dragFrame.height,
          zIndex: 100,
          transform: translation?.getTranslateTransform(),
        }
      : null,
  ];

  const tabContent = (
    <Pressable
      testID={`desktop-session-tab-${tab.tabId}`}
      accessibilityLabel={`${tab.title}${preview ? ', Preview' : ''}`}
      accessibilityValue={{
        text: `${preview ? 'Preview, ' : ''}${index + 1} of ${itemCount}`,
      }}
      accessibilityActions={
        preview
          ? undefined
          : [
              { name: 'decrement', label: 'Move tab left' },
              { name: 'increment', label: 'Move tab right' },
            ]
      }
      onAccessibilityAction={event => {
        if (event.nativeEvent.actionName === 'decrement') {
          onMoveAccessible?.(-1);
        }
        if (event.nativeEvent.actionName === 'increment') {
          onMoveAccessible?.(1);
        }
      }}
      style={[
        styles.tab,
        active ? styles.tabActive : styles.tabInactive,
        hovered && styles.tabHovered,
        isDragging && styles.tabDragging,
      ]}
      onPress={onPress}
      onHoverIn={onHoverIn}
      onHoverOut={onHoverOut}
    >
      <SessionRequestStatusIndicator
        status={status}
        variant="dot"
        testID={`desktop-tab-request-status-${tab.tabId}`}
      />
      <View style={styles.tabTextContainer}>
        <Text
          style={[
            styles.tabTitle,
            active && styles.tabTitleActive,
            preview && styles.previewTitle,
          ]}
          numberOfLines={1}
        >
          {tab.title}
        </Text>
        <Text style={styles.tabMeta} numberOfLines={1}>
          {subtitle}
        </Text>
      </View>
      {showClose ? (
        <Pressable
          accessibilityLabel={`Close ${tab.title}`}
          style={styles.closeButton}
          onStartShouldSetResponder={() => true}
          onPress={(event: GestureResponderEvent) => {
            (event as any)?.stopPropagation?.();
            onClose();
          }}
        >
          <Text style={styles.closeButtonText}>×</Text>
        </Pressable>
      ) : null}
    </Pressable>
  );

  return (
    <Animated.View
      style={wrapperStyle}
      {...({ mouseDownCanMoveWindow: false } as any)}
      onLayout={!isDragging ? onLayout : undefined}
      {...(Platform.OS !== 'macos' && !preview ? panResponder.panHandlers : {})}
    >
      {Platform.OS === 'macos' ? (
        <MacDragView
          testID={`desktop-session-tab-pointer-${tab.tabId}`}
          dragEnabled={!preview}
          mouseDownCanMoveWindow={false}
          onDragStart={
            preview
              ? undefined
              : event => onDragStart?.(nativeDragGesture(event))
          }
          onDragMove={
            preview
              ? undefined
              : event => onDragMove?.(nativeDragGesture(event))
          }
          onDragEnd={
            preview
              ? undefined
              : event => onDragRelease?.(nativeDragGesture(event))
          }
          onDragCancel={preview ? undefined : () => onDragCancel?.()}
          onAuxiliaryClick={() => onClose()}
        >
          {tabContent}
        </MacDragView>
      ) : (
        tabContent
      )}
    </Animated.View>
  );
}

function createStyles(
  theme: ReturnType<typeof useTheme>,
  styleVariant: TabStripStyle,
) {
  const separatorWidth = 1;
  const toolbarTabs = styleVariant === 'toolbarTabs';
  const codeTabs = styleVariant === 'codeTabs';
  const underlineTabs = styleVariant === 'underlineTabs';
  const roundedPills = styleVariant === 'roundedPills';
  const codeLike = codeTabs || underlineTabs;
  const stripBackground = codeTabs ? theme.surfaceAlt : theme.backgroundAlt;
  const tabRadius = toolbarTabs ? 9 : roundedPills ? 12 : 0;
  const tabBackground = codeTabs
    ? theme.surfaceAlt
    : toolbarTabs
    ? stripBackground
    : underlineTabs
    ? stripBackground
    : theme.surface;
  const tabHoveredBackground = underlineTabs
    ? theme.surfaceAlt
    : toolbarTabs
    ? theme.surfaceAlt
    : codeTabs
    ? theme.surface
    : theme.surfaceAlt;

  return StyleSheet.create({
    root: {
      flexDirection: 'row',
      alignItems: 'stretch',
      gap: codeLike ? 0 : 8,
      paddingHorizontal: codeLike ? 0 : 10,
      paddingVertical: toolbarTabs ? 10 : codeLike ? 0 : 8,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
      backgroundColor: stripBackground,
      overflow: 'hidden',
    },
    homeTab: {
      width: 42,
      alignItems: 'center',
      justifyContent: 'center',
      borderWidth: codeLike ? 0 : 1,
      borderRightWidth: codeLike ? 1 : undefined,
      borderRightColor: theme.border,
      borderColor: theme.border,
      borderRadius: tabRadius,
      backgroundColor: tabBackground,
    },
    scrollView: {
      flex: 1,
      overflow: 'hidden',
    },
    tabsContainer: {
      alignItems: 'stretch',
      gap: codeLike ? 0 : 8,
      paddingRight: codeLike ? 0 : 8,
      paddingVertical: toolbarTabs ? 6 : 0,
      minHeight: 44,
    },
    tab: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      position: 'relative',
      borderWidth: codeLike ? 0 : separatorWidth,
      borderColor: toolbarTabs ? 'transparent' : theme.border,
      borderRightWidth: codeLike ? separatorWidth : 0,
      borderRightColor: codeLike ? theme.border : undefined,
      borderRadius: tabRadius,
      paddingLeft: codeLike ? 12 : 10,
      paddingRight: codeLike ? 34 : 32,
      paddingVertical: underlineTabs ? 8 : codeTabs ? 7 : 8,
      backgroundColor: tabBackground,
      minWidth: codeLike ? 140 : 160,
      maxWidth: codeLike ? 260 : 240,
      minHeight: 42,
    },
    tabInactive: {
      borderBottomWidth: underlineTabs ? 2 : undefined,
      borderBottomColor: underlineTabs ? 'transparent' : undefined,
    },
    tabActive: {
      backgroundColor: theme.surface,
      borderColor: toolbarTabs
        ? theme.border
        : roundedPills
        ? theme.primary
        : theme.border,
      borderBottomWidth: underlineTabs ? 2 : undefined,
      borderBottomColor: underlineTabs ? theme.primary : undefined,
      borderTopWidth: codeTabs ? 2 : undefined,
      borderTopColor: codeTabs ? theme.primary : undefined,
    },
    tabHovered: {
      backgroundColor: tabHoveredBackground,
    },
    tabDragging: {
      opacity: 0.96,
      shadowColor: '#000',
      shadowOpacity: 0.24,
      shadowRadius: 10,
      shadowOffset: { width: 0, height: 5 },
    },
    placeholder: {
      borderWidth: 1,
      borderStyle: 'dashed',
      borderColor: theme.primary,
      borderRadius: tabRadius,
      backgroundColor: theme.primaryMuted,
    },
    tabTextContainer: {
      flex: 1,
      gap: 1,
    },
    tabTitle: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: toolbarTabs ? '700' : '600',
      color: theme.text,
    },
    tabTitleActive: {
      color: theme.text,
    },
    previewTitle: {
      fontStyle: 'italic',
      fontWeight: '500',
    },
    tabMeta: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
    },
    closeButton: {
      position: 'absolute',
      right: codeLike ? 10 : 8,
      top: 0,
      bottom: 0,
      alignItems: 'center',
      justifyContent: 'center',
      width: 22,
      borderRadius: 8,
    },
    closeButtonText: {
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
      color: theme.textSecondary,
      lineHeight: theme.typography.lineHeight.normal,
    },
    menuButton: {
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 10,
      borderRadius: codeLike ? 0 : 10,
      borderWidth: codeLike ? 0 : separatorWidth,
      borderLeftWidth: separatorWidth,
      borderLeftColor: theme.border,
      backgroundColor: codeLike ? stripBackground : theme.surface,
    },
    menuButtonText: {
      fontSize: theme.typography.fontSize.title,
      lineHeight: theme.typography.lineHeight.title,
      fontWeight: '600',
      color: theme.text,
      marginTop: -2,
    },
  });
}

export function createSessionTabsStyles(
  theme: ReturnType<typeof useTheme>,
  styleVariant: TabStripStyle,
) {
  return createStyles(theme, styleVariant);
}
