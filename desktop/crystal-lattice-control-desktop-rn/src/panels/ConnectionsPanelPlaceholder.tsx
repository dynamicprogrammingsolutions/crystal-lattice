import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

import { PanelHeader } from '../ui/PanelHeader';
import { KebabMenu } from '../ui/KebabMenu';

export interface DesktopConnectionStub {
  id: string;
  name: string;
}

export interface ConnectionsPanelPlaceholderProps {
  connections: DesktopConnectionStub[];
  focusedConnectionId: string | null;
  openConnectionIds: string[];
  onFocusConnection: (connectionId: string) => void;
  onToggleOpenConnection: (connectionId: string) => void;
  onAddDemoConnection?: () => void;
  onClearConnections?: () => void;
}

export function ConnectionsPanelPlaceholder({
  connections,
  focusedConnectionId,
  openConnectionIds,
  onFocusConnection,
  onToggleOpenConnection,
  onAddDemoConnection,
  onClearConnections,
}: ConnectionsPanelPlaceholderProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const menuItems = useMemo(() => {
    const items: Array<{ label: string; onPress?: () => void; variant?: 'default' | 'danger' }> = [];
    if (onAddDemoConnection) {
      items.push({ label: 'Add demo connection', onPress: onAddDemoConnection });
    }
    if (onClearConnections) {
      items.push({ label: 'Clear connections', onPress: onClearConnections, variant: 'danger' });
    }
    return items;
  }, [onAddDemoConnection, onClearConnections]);

  return (
    <View style={styles.root}>
      <PanelHeader
        title="Connections"
        subtitle="Placeholder"
        menuLabel="⋯"
        menuItems={menuItems}
      />

      <View style={styles.list}>
        {connections.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No saved connections.</Text>
            <Text style={styles.emptyMeta}>Use the menu to add a demo connection.</Text>
          </View>
        ) : null}

        {connections.map((connection) => {
          const isFocused = focusedConnectionId === connection.id;
          const isOpen = openConnectionIds.includes(connection.id);
          return (
            <Pressable
              key={connection.id}
              style={(state) => {
                const hovered = (state as any).hovered as boolean | undefined;
                return [
                  styles.row,
                  isFocused && styles.rowFocused,
                  (hovered || state.pressed) && styles.rowHovered,
                ];
              }}
              onPress={() => onFocusConnection(connection.id)}
            >
              <View style={styles.rowMain}>
                <Text style={styles.rowTitle} numberOfLines={1}>
                  {connection.name}
                </Text>
                <Text style={styles.rowMeta} numberOfLines={1}>
                  {connection.id}
                </Text>
              </View>
              <Pressable
                style={({ pressed }) => [styles.openButton, pressed && styles.openButtonPressed]}
                onPress={(event) => {
                  (event as any)?.stopPropagation?.();
                  onToggleOpenConnection(connection.id);
                }}
              >
                <Text style={[styles.openButtonText, { color: isOpen ? theme.success : theme.textSecondary }]}>
                  {isOpen ? 'Open' : 'Closed'}
                </Text>
              </Pressable>

              <KebabMenu
                items={[
                  { label: 'Rename (placeholder)' },
                  { label: 'Delete (placeholder)', variant: 'danger' },
                ]}
              />
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;

  return StyleSheet.create({
    root: {
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    list: {
      paddingVertical: 6,
    },
    empty: {
      paddingHorizontal: 10,
      paddingVertical: 8,
      gap: 2,
    },
    emptyText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    emptyMeta: {
      fontSize: 11,
      color: theme.textMuted,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
    },
    rowHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    rowFocused: {
      backgroundColor: theme.primaryMuted,
    },
    rowMain: {
      flex: 1,
      gap: 2,
    },
    rowTitle: {
      fontSize: 13,
      fontWeight: '600',
      color: theme.text,
    },
    rowMeta: {
      fontSize: 11,
      color: theme.textSecondary,
    },
    openButton: {
      paddingHorizontal: 8,
      paddingVertical: 6,
      borderRadius: 8,
      borderWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    openButtonPressed: {
      opacity: 0.8,
    },
    openButtonText: {
      fontSize: 11,
      fontWeight: '600',
    },
  });
}
