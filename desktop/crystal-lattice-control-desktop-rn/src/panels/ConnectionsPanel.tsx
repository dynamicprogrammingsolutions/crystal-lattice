import React, { useMemo } from 'react';
import { Alert, Pressable, StyleSheet, Text, View } from 'react-native';

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';
import { useTheme } from '@crystal-lattice/frontend-rn-components';

import type { OpenConnectionsById, OpenConnectionStatus } from '../connections/useOpenConnections';
import { KebabMenu } from '../ui/KebabMenu';
import { PanelHeader } from '../ui/PanelHeader';

export type ConnectionRowClickBehavior = 'focusOnly' | 'focusAndOpen' | 'focusAndToggleOpen';

export interface ConnectionsPanelProps {
  connectionRecords: ConnectionRecord[];
  focusedConnectionId: string | null;
  openConnectionsById: OpenConnectionsById;
  rowClickBehavior: ConnectionRowClickBehavior;
  onFocusConnection: (connectionId: string) => void;
  onOpenConnection: (record: ConnectionRecord) => void;
  onCloseConnection: (connectionId: string) => void;
  onDeleteConnection: (connectionId: string) => void;
  onClearConnections: () => void;
  onOpenNewConnectionEditor: () => void;
  onOpenEditConnectionEditor: (record: ConnectionRecord) => void;
}

function getStatus(openConnectionsById: OpenConnectionsById, connectionId: string): {
  status: OpenConnectionStatus;
  errorMessage?: string;
} {
  const runtime = openConnectionsById[connectionId];
  if (!runtime) {
    return { status: 'closed' };
  }
  return { status: runtime.status, errorMessage: runtime.errorMessage };
}

function getManualSubtitle(record: ConnectionRecord): string {
  if (record.kind !== 'manual') {
    return record.id;
  }
  return `${record.host}:${record.port}`;
}

export function ConnectionsPanel({
  connectionRecords,
  focusedConnectionId,
  openConnectionsById,
  rowClickBehavior,
  onFocusConnection,
  onOpenConnection,
  onCloseConnection,
  onDeleteConnection,
  onClearConnections,
  onOpenNewConnectionEditor,
  onOpenEditConnectionEditor,
}: ConnectionsPanelProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const openCount = useMemo(() => {
    return Object.values(openConnectionsById).filter((c) => c.status === 'open').length;
  }, [openConnectionsById]);

  const menuItems = useMemo(() => {
    return [
      { label: 'New connection…', onPress: onOpenNewConnectionEditor },
      {
        label: 'Clear connections',
        variant: 'danger' as const,
        onPress: () => {
          if (connectionRecords.length === 0) {
            return;
          }
          Alert.alert(
            'Clear all connections?',
            'This removes saved connections and clears local caches.',
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Clear', style: 'destructive', onPress: onClearConnections },
            ],
          );
        },
      },
    ];
  }, [connectionRecords.length, onClearConnections, onOpenNewConnectionEditor]);

  return (
    <View style={styles.root}>
      <PanelHeader
        title="Connections"
        subtitle={`${connectionRecords.length} saved • ${openCount} open`}
        menuLabel="⋯"
        menuItems={menuItems}
      />

      <View style={styles.list}>
        {connectionRecords.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No saved connections.</Text>
            <Text style={styles.emptyMeta}>Use “New connection…” to add one.</Text>
          </View>
        ) : null}

        {connectionRecords.map((record) => {
          const isFocused = focusedConnectionId === record.id;
          const { status, errorMessage } = getStatus(openConnectionsById, record.id);
          const isConnecting = status === 'connecting';
          const isOpen = status === 'open';
          const statusColor =
            status === 'open'
              ? theme.success
              : status === 'error'
                ? theme.danger
                : theme.textSecondary;

          const handleRowPress = () => {
            onFocusConnection(record.id);
            if (rowClickBehavior === 'focusOnly') {
              return;
            }
            if (rowClickBehavior === 'focusAndToggleOpen') {
              if (isOpen || isConnecting) {
                onCloseConnection(record.id);
              } else {
                onOpenConnection(record);
              }
              return;
            }

            // focusAndOpen
            if (!isOpen && !isConnecting) {
              onOpenConnection(record);
            }
          };

          return (
            <Pressable
              key={record.id}
              style={(state) => {
                const hovered = (state as any).hovered as boolean | undefined;
                return [
                  styles.row,
                  isFocused && styles.rowFocused,
                  (hovered || state.pressed) && styles.rowHovered,
                ];
              }}
              onPress={handleRowPress}
            >
              <View style={styles.rowMain}>
                <View style={styles.rowTitleLine}>
                  <Text style={styles.rowTitle} numberOfLines={1}>
                    {record.name}
                  </Text>
                  <Text style={[styles.status, { color: statusColor }]} numberOfLines={1}>
                    {status === 'closed'
                      ? 'Closed'
                      : status === 'connecting'
                        ? 'Connecting'
                        : status === 'open'
                          ? 'Open'
                          : 'Error'}
                  </Text>
                </View>
                <Text style={styles.rowMeta} numberOfLines={1}>
                  {getManualSubtitle(record)}
                </Text>
                {status === 'error' && errorMessage ? (
                  <Text style={styles.rowError} numberOfLines={1}>
                    {errorMessage}
                  </Text>
                ) : null}
              </View>

              <Pressable
                style={({ pressed }) => [styles.openButton, pressed && styles.openButtonPressed]}
                disabled={isConnecting}
                onPress={(event) => {
                  (event as any)?.stopPropagation?.();
                  if (isOpen) {
                    onCloseConnection(record.id);
                  } else {
                    onOpenConnection(record);
                  }
                }}
              >
                <Text
                  style={[
                    styles.openButtonText,
                    { color: isOpen ? theme.textSecondary : theme.primary },
                  ]}
                >
                  {isConnecting ? '…' : isOpen ? 'Close' : status === 'error' ? 'Retry' : 'Open'}
                </Text>
              </Pressable>

              <KebabMenu
                items={[
                  { label: 'Edit…', onPress: () => onOpenEditConnectionEditor(record) },
                  {
                    label: 'Delete',
                    variant: 'danger',
                    onPress: () => {
                      Alert.alert(
                        'Delete connection?',
                        `“${record.name}” will be removed from saved connections.`,
                        [
                          { text: 'Cancel', style: 'cancel' },
                          {
                            text: 'Delete',
                            style: 'destructive',
                            onPress: () => {
                              onCloseConnection(record.id);
                              onDeleteConnection(record.id);
                            },
                          },
                        ],
                      );
                    },
                  },
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
      paddingVertical: 10,
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
    rowTitleLine: {
      flexDirection: 'row',
      alignItems: 'baseline',
      justifyContent: 'space-between',
      gap: 10,
    },
    rowTitle: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
      flex: 1,
    },
    status: {
      fontSize: 11,
      fontWeight: '700',
    },
    rowMeta: {
      fontSize: 11,
      color: theme.textSecondary,
    },
    rowError: {
      fontSize: 10,
      color: theme.danger,
    },
    openButton: {
      paddingHorizontal: 10,
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
      fontWeight: '800',
    },
  });
}
