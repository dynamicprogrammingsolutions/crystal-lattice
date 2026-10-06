import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  ActionsMenuContent,
  actionsPopoverInvokeAction,
  actionsPopoverRequestClose,
  actionsPopoverTogglePinned,
  ThemeProvider,
  useActiveActionsPopoverMenu,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { buildDesktopCaptureTheme } from '../theme/buildDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';

function togglePinnedKey(pinned: readonly string[], key: string): string[] {
  if (pinned.includes(key)) {
    return pinned.filter((k) => k !== key);
  }
  return [...pinned, key];
}

export function ActionsPopoverView({
  captureAppearance,
}: { captureAppearance?: 'light' | 'dark' }): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  const theme = useMemo(
    () => captureAppearance ? buildDesktopCaptureTheme(captureAppearance) : systemTheme,
    [captureAppearance, systemTheme],
  );
  return (
    <ThemeProvider theme={theme}>
      <ActionsPopoverViewInner />
    </ThemeProvider>
  );
}

function ActionsPopoverViewInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const state = useActiveActionsPopoverMenu();
  const activeMenuId = state?.data.id;

  const [menuId, setMenuId] = useState<string | null>(null);
  const [pinnedLocal, setPinnedLocal] = useState<string[]>([]);
  const [headerHeight, setHeaderHeight] = useState(0);
  const [contentSize, setContentSize] = useState({ menuId: '', height: 0 });

  useEffect(() => {
    if (activeMenuId && contentSize.menuId === activeMenuId && headerHeight > 0) {
      DesktopWindowManager?.resizeActionsPopover?.({
        menuId: activeMenuId,
        height: headerHeight + contentSize.height,
      });
    }
  }, [activeMenuId, headerHeight, contentSize]);

  useEffect(() => {
    const nextId = state?.data.id ?? null;
    if (!nextId) {
      setMenuId(null);
      setPinnedLocal([]);
      return;
    }
    if (nextId !== menuId) {
      setMenuId(nextId);
      setPinnedLocal([...(state?.data.pinnedKeys ?? [])]);
    }
  }, [menuId, state?.data.id, state?.data.pinnedKeys]);

  if (!state) {
    return <View style={styles.root} />;
  }

  const disabledKeys = new Set(state.data.disabledKeys);

  return (
    <View style={styles.root}>
      <View
        style={styles.header}
        onLayout={(event) => setHeaderHeight(event.nativeEvent.layout.height)}
      >
        <Text style={styles.headerTitle} numberOfLines={2}>
          {state.data.title}
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Close ${state.data.title}`}
          testID="actions-popover-close"
          style={(pressState) => {
            const hovered = (pressState as any).hovered as boolean | undefined;
            return [styles.closeButton, (hovered || pressState.pressed) && styles.closeButtonHovered];
          }}
          onPress={() => actionsPopoverRequestClose()}
        >
          <Text style={styles.closeButtonText}>×</Text>
        </Pressable>
      </View>

      <ScrollView
        testID="actions-popover-scroll"
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        onContentSizeChange={(_width, height) =>
          setContentSize({ menuId: state.data.id, height })
        }
      >
        <ActionsMenuContent
          actions={state.data.actions}
          pinnedKeys={pinnedLocal}
          onAction={(key) => actionsPopoverInvokeAction(key)}
          onTogglePinned={(key) => {
            setPinnedLocal((prev) => togglePinnedKey(prev, key));
            actionsPopoverTogglePinned(key);
          }}
          isActionDisabled={(key) => disabledKeys.has(key)}
          getIconName={(action) =>
            typeof (action as any).iconName === 'string' ? (action as any).iconName : null
          }
          renderIcon={({ name, size, color }) => <Icon name={name} size={size} color={color} />}
          iconSize={16}
          pinIconSize={14}
          renderItem={state.data.renderItem}
        />
      </ScrollView>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.surface,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderBottomWidth: borderWidth,
      borderBottomColor: theme.border,
      backgroundColor: theme.surface,
    },
    headerTitle: {
      flex: 1,
      fontSize: 13,
      fontWeight: '800',
      color: theme.text,
    },
    closeButton: {
      borderWidth,
      borderColor: theme.border,
      borderRadius: 10,
      backgroundColor: theme.surface,
      width: 28,
      height: 28,
      alignItems: 'center',
      justifyContent: 'center',
    },
    closeButtonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    closeButtonText: {
      fontSize: 16,
      fontWeight: '900',
      color: theme.textSecondary,
      marginTop: -2,
    },
    scroll: {
      flex: 1,
    },
    scrollContent: {
      paddingVertical: 6,
    },
  });
}
