import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { StyleSheet, View, type LayoutChangeEvent } from 'react-native';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import { useTheme } from '@crystal-lattice/frontend-rn-components';

import { MacDragView, type MacDragEvent } from '../native/MacDragView';
import { asyncStorageKeyValueStore } from '../storage/asyncStorageKeyValueStore';
import {
  DESKTOP_SIDEBAR_WIDTH_POLICY,
  DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY,
  adjustDesktopSidebarWidth,
  getDesktopSidebarWidthBounds,
  parsePersistedDesktopSidebarWidth,
  resolveDesktopSidebarWidth,
  serializeDesktopSidebarWidth,
} from './desktopSidebarWidth';

export interface DesktopSidebarMetrics {
  width: number;
  minimumWidth: number;
  maximumWidth: number;
  minimumMainWidth: number;
  adjustmentStep: number;
  mainWidth: number | null;
}

export interface DesktopShellProps {
  activityRail: React.ReactNode;
  panel: React.ReactNode;
  main: React.ReactNode;
  sidebarWidthStore?: KeyValueStore;
  onSidebarMetricsChange?: (metrics: DesktopSidebarMetrics) => void;
}

export function DesktopShell({
  activityRail,
  panel,
  main,
  sidebarWidthStore = asyncStorageKeyValueStore,
  onSidebarMetricsChange,
}: DesktopShellProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [shellWidth, setShellWidth] = useState<number | null>(null);
  const [preferredSidebarWidth, setPreferredSidebarWidth] = useState<number>(
    DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth,
  );
  const userAdjustedRef = useRef(false);
  const dragOriginWidthRef = useRef<number | null>(null);
  const dragInitialWidthRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    sidebarWidthStore
      .get(DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY)
      .then(raw => {
        if (cancelled || userAdjustedRef.current || raw === null) {
          return;
        }
        const parsed = parsePersistedDesktopSidebarWidth(raw);
        setPreferredSidebarWidth(parsed);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [sidebarWidthStore]);

  const sidebarWidth = resolveDesktopSidebarWidth(
    preferredSidebarWidth,
    shellWidth,
  );
  const sidebarBounds = getDesktopSidebarWidthBounds(shellWidth);
  const fixedShellWidth =
    DESKTOP_SIDEBAR_WIDTH_POLICY.activityRailWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.activityPanelSeparatorWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.resizeHandleWidth;
  const mainWidth =
    shellWidth === null
      ? null
      : Math.max(0, shellWidth - fixedShellWidth - sidebarWidth);

  useEffect(() => {
    onSidebarMetricsChange?.({
      width: sidebarWidth,
      minimumWidth: sidebarBounds.minimumWidth,
      maximumWidth: sidebarBounds.maximumWidth,
      minimumMainWidth: DESKTOP_SIDEBAR_WIDTH_POLICY.minimumMainWidth,
      adjustmentStep: DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep,
      mainWidth,
    });
  }, [
    mainWidth,
    onSidebarMetricsChange,
    sidebarBounds.maximumWidth,
    sidebarBounds.minimumWidth,
    sidebarWidth,
  ]);

  const setLiveSidebarWidth = useCallback(
    (requestedWidth: number) => {
      const next = resolveDesktopSidebarWidth(requestedWidth, shellWidth);
      userAdjustedRef.current = true;
      setPreferredSidebarWidth(next);
      return next;
    },
    [shellWidth],
  );

  const persistSidebarWidth = useCallback(
    (width: number) => {
      sidebarWidthStore
        .set(
          DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY,
          serializeDesktopSidebarWidth(width),
        )
        .catch(() => {});
    },
    [sidebarWidthStore],
  );

  const startResize = useCallback(
    (event: MacDragEvent) => {
      dragInitialWidthRef.current = sidebarWidth;
      dragOriginWidthRef.current = sidebarWidth - event.translationX;
    },
    [sidebarWidth],
  );

  const moveResize = useCallback(
    (event: MacDragEvent) => {
      const origin = dragOriginWidthRef.current;
      if (origin === null) {
        return;
      }
      setLiveSidebarWidth(origin + event.translationX);
    },
    [setLiveSidebarWidth],
  );

  const endResize = useCallback(
    (event: MacDragEvent) => {
      const origin = dragOriginWidthRef.current;
      dragOriginWidthRef.current = null;
      dragInitialWidthRef.current = null;
      const finalWidth =
        origin === null
          ? sidebarWidth
          : setLiveSidebarWidth(origin + event.translationX);
      persistSidebarWidth(finalWidth);
    },
    [persistSidebarWidth, setLiveSidebarWidth, sidebarWidth],
  );

  const cancelResize = useCallback(() => {
    const initialWidth = dragInitialWidthRef.current;
    dragOriginWidthRef.current = null;
    dragInitialWidthRef.current = null;
    if (initialWidth !== null) {
      setLiveSidebarWidth(initialWidth);
    }
  }, [setLiveSidebarWidth]);

  const adjustSidebar = useCallback(
    (direction: -1 | 1) => {
      const next = adjustDesktopSidebarWidth(
        sidebarWidth,
        direction,
        shellWidth,
      );
      setLiveSidebarWidth(next);
      persistSidebarWidth(next);
    },
    [persistSidebarWidth, setLiveSidebarWidth, shellWidth, sidebarWidth],
  );

  const handleShellLayout = useCallback((event: LayoutChangeEvent) => {
    setShellWidth(event.nativeEvent.layout.width);
  }, []);

  return (
    <View
      style={styles.root}
      testID="desktop-shell"
      onLayout={handleShellLayout}
    >
      <View style={styles.activityRail} testID="desktop-shell-activity-rail">
        {activityRail}
      </View>
      <View
        style={styles.separator}
        testID="desktop-activity-panel-separator"
      />
      <View
        style={[styles.panel, { width: sidebarWidth }]}
        testID="desktop-sidebar-panel"
      >
        {panel}
      </View>
      <MacDragView
        testID="desktop-sidebar-resize-handle"
        style={styles.resizeHandle}
        dragEnabled
        keyboardAdjustable
        mouseDownCanMoveWindow={false}
        accessible
        focusable
        accessibilityRole="adjustable"
        accessibilityLabel="Resize sidebar"
        accessibilityHint="Drag, or use the left and right arrow keys."
        accessibilityValue={{
          min: sidebarBounds.minimumWidth,
          max: sidebarBounds.maximumWidth,
          now: sidebarWidth,
          text: `${sidebarWidth} points`,
        }}
        accessibilityActions={[
          { name: 'decrement', label: 'Make sidebar narrower' },
          { name: 'increment', label: 'Make sidebar wider' },
        ]}
        onAccessibilityAction={event => {
          if (event.nativeEvent.actionName === 'decrement') {
            adjustSidebar(-1);
          }
          if (event.nativeEvent.actionName === 'increment') {
            adjustSidebar(1);
          }
        }}
        onKeyDecrement={() => adjustSidebar(-1)}
        onKeyIncrement={() => adjustSidebar(1)}
        onDragStart={startResize}
        onDragMove={moveResize}
        onDragEnd={endResize}
        onDragCancel={cancelResize}
      >
        <View
          pointerEvents="none"
          style={styles.resizeSeparator}
          testID="desktop-sidebar-main-separator"
        />
      </MacDragView>
      <View style={styles.main} testID="desktop-main-workspace">
        {main}
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const separatorWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      flexDirection: 'row',
    },
    activityRail: {
      width: DESKTOP_SIDEBAR_WIDTH_POLICY.activityRailWidth,
      backgroundColor: theme.surfaceAlt,
    },
    separator: {
      width: DESKTOP_SIDEBAR_WIDTH_POLICY.activityPanelSeparatorWidth,
      backgroundColor: theme.border,
    },
    panel: {
      backgroundColor: theme.backgroundAlt,
    },
    resizeHandle: {
      width: DESKTOP_SIDEBAR_WIDTH_POLICY.resizeHandleWidth,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.backgroundAlt,
    },
    resizeSeparator: {
      width: separatorWidth,
      height: '100%',
      backgroundColor: theme.border,
    },
    main: {
      flex: 1,
      backgroundColor: theme.background,
    },
  });
}

export { createStyles as createDesktopShellStyles };
