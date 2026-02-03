import React, { useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { DropdownMenuSurface, useTheme } from '@crystal-lattice/frontend-rn-components';

export interface KebabMenuItem {
  label: string;
  onPress?: () => void;
  variant?: 'default' | 'danger';
}

export interface KebabMenuProps {
  items: KebabMenuItem[];
}

export function KebabMenu({ items }: KebabMenuProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const anchorRef = useRef<any>(null);
  const [visible, setVisible] = useState(false);

  return (
    <>
      <Pressable
        ref={anchorRef}
        style={(state) => {
          const hovered = (state as any).hovered as boolean | undefined;
          return [styles.button, (hovered || state.pressed) && styles.buttonHovered];
        }}
        onPress={(event) => {
          (event as any)?.stopPropagation?.();
          setVisible(true);
        }}
      >
        <Text style={styles.buttonText}>⋯</Text>
      </Pressable>

      <DropdownMenuSurface
        visible={visible}
        onRequestClose={() => setVisible(false)}
        anchorRef={anchorRef}
        offset={{ y: 6 }}
        menuStyle={styles.menu}
      >
        <View style={styles.menuContent}>
          {items.map((item) => (
            <Pressable
              key={item.label}
              style={(state) => {
                const hovered = (state as any).hovered as boolean | undefined;
                return [styles.menuItem, (hovered || state.pressed) && styles.menuItemHovered];
              }}
              onPress={() => {
                setVisible(false);
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
          ))}
        </View>
      </DropdownMenuSurface>
    </>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    button: {
      paddingHorizontal: 8,
      paddingVertical: 6,
      borderRadius: 8,
    },
    buttonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    buttonText: {
      fontSize: 16,
      fontWeight: '700',
      color: theme.textSecondary,
      marginTop: -2,
    },
    menu: {
      minWidth: 180,
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
