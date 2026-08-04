import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { closeDesktopPopover, useActiveDesktopPopover } from './desktopPopoverCoordinator';

export function MessageLimitPopoverView(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <MessageLimitPopoverViewInner />
    </ThemeProvider>
  );
}

function MessageLimitPopoverViewInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveDesktopPopover();

  if (!active) {
    return <View style={styles.root} />;
  }

  const close = () => {
    closeDesktopPopover(active.id);
    active.onRequestClose?.();
  };

  return (
    <View
      style={styles.root}
      testID="desktop-popover-root"
      accessibilityLabel={active.title ? `${active.title} popover` : 'Desktop popover'}
    >
      {active.title ? (
        <View style={styles.header}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {active.title}
          </Text>
          <Pressable
            testID="desktop-popover-close"
            accessibilityRole="button"
            accessibilityLabel={`Close ${active.title}`}
            style={(pressState) => {
              const hovered = (pressState as any).hovered as boolean | undefined;
              return [
                styles.closeButton,
                (hovered || pressState.pressed) && styles.closeButtonHovered,
              ];
            }}
            onPress={() => {
              close();
            }}
          >
            <Text style={styles.closeButtonText}>×</Text>
          </Pressable>
        </View>
      ) : null}

      <View style={styles.body}>{active.content}</View>
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
    body: {
      flex: 1,
    },
  });
}
