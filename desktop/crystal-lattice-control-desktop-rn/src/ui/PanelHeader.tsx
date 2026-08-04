import React, { useMemo, useRef, useState } from 'react';
import { ActionSheetIOS, Pressable, StyleSheet, Text, View, findNodeHandle, Platform } from 'react-native';

import { DropdownMenuSurface, useTheme } from '@crystal-lattice/frontend-rn-components';

export interface PanelHeaderProps {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  menuLabel?: string;
  onPressMenu?: () => void;
  menuItems?: Array<{ label: string; onPress?: () => void; variant?: 'default' | 'danger' }>;
}

export function PanelHeader({
  title,
  subtitle,
  right,
  menuLabel,
  onPressMenu,
  menuItems,
}: PanelHeaderProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const anchorRef = useRef<any>(null);
  const [menuVisible, setMenuVisible] = useState(false);
  const showMenu = !!menuLabel;

  const openNativeMenu = () => {
    const items = menuItems && menuItems.length > 0 ? menuItems : [{ label: 'Menu placeholder' }];
    const options = items.map((item) => item.label).concat(['Cancel']);
    const cancelButtonIndex = options.length - 1;
    const destructiveButtonIndices = items
      .map((item, index) => (item.variant === 'danger' ? index : -1))
      .filter((index) => index >= 0);
    let anchor: number | null = null;
    if (anchorRef.current) {
      try {
        anchor = findNodeHandle(anchorRef.current) as any;
      } catch {
        anchor = null;
      }
    }

    ActionSheetIOS.showActionSheetWithOptions(
      {
        options,
        cancelButtonIndex,
        destructiveButtonIndex:
          destructiveButtonIndices.length > 0 ? destructiveButtonIndices : undefined,
        anchor: anchor ?? undefined,
      },
      (buttonIndex) => {
        if (buttonIndex === cancelButtonIndex) {
          return;
        }
        items[buttonIndex]?.onPress?.();
      },
    );
  };

  return (
    <View style={styles.root}>
      <View style={styles.textColumn}>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>
        {subtitle ? (
          <Text style={styles.subtitle} numberOfLines={1}>
            {subtitle}
          </Text>
        ) : null}
      </View>

      {right}
      {showMenu ? (
        <View ref={anchorRef} collapsable={false}>
          <Pressable
            style={(state) => {
              const hovered = (state as any).hovered as boolean | undefined;
              return [
                styles.menuButton,
                (hovered || state.pressed) && styles.menuButtonHovered,
              ];
            }}
            onPress={() => {
              if (onPressMenu) {
                onPressMenu();
                return;
              }
              if (Platform.OS === 'macos') {
                openNativeMenu();
                return;
              }
              setMenuVisible(true);
            }}
          >
            <Text style={styles.menuButtonText}>{menuLabel}</Text>
          </Pressable>
        </View>
      ) : null}

      {Platform.OS !== 'macos' ? (
        <DropdownMenuSurface
          visible={menuVisible}
          onRequestClose={() => setMenuVisible(false)}
          anchorRef={anchorRef}
          offset={{ y: 6 }}
        >
          <View style={styles.menuContent}>
            {(menuItems && menuItems.length > 0 ? menuItems : [{ label: 'Menu placeholder' }]).map(
              (item) => (
                <Pressable
                  key={item.label}
                  style={(state) => {
                    const hovered = (state as any).hovered as boolean | undefined;
                    return [styles.menuItem, (hovered || state.pressed) && styles.menuItemHovered];
                  }}
                  onPress={() => {
                    setMenuVisible(false);
                    item.onPress?.();
                  }}
                >
                  <Text
                    style={[
                      styles.menuItemText,
                      item.variant === 'danger' && { color: theme.danger },
                    ]}
                  >
                    {item.label}
                  </Text>
                </Pressable>
              ),
            )}
          </View>
        </DropdownMenuSurface>
      ) : null}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const separatorWidth = 1;

  return StyleSheet.create({
    root: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10,
      paddingHorizontal: 10,
      paddingVertical: 10,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
    },
    textColumn: {
      flex: 1,
      gap: 2,
    },
    title: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    subtitle: {
      fontSize: 11,
      color: theme.textSecondary,
    },
    menuButton: {
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    menuButtonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    menuButtonText: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.text,
    },
    menuContent: {
      paddingVertical: 4,
    },
    menuItem: {
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    menuItemHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    menuItemText: {
      fontSize: 12,
      color: theme.text,
    },
  });
}
