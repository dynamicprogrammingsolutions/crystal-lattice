import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

import { PanelHeader } from '../ui/PanelHeader';
import { KebabMenu } from '../ui/KebabMenu';

interface PlaceholderSession {
  sessionId: string;
  title: string;
}

export interface SessionsPanelPlaceholderProps {
  focusedConnectionId: string | null;
  focusedConnectionName: string | null;
  isFocusedConnectionOpen: boolean;
  onOpenSession: (params: { connectionId: string; sessionId: string; title: string }) => void;
}

function buildPlaceholderSessions(connectionId: string): PlaceholderSession[] {
  const prefix = connectionId.replace(/[^a-z0-9]/gi, '').slice(-4) || 'xxxx';
  return [
    { sessionId: `sess-${prefix}-a`, title: `Session ${prefix} A` },
    { sessionId: `sess-${prefix}-b`, title: `Session ${prefix} B` },
    { sessionId: `sess-${prefix}-c`, title: `Session ${prefix} C` },
  ];
}

export function SessionsPanelPlaceholder({
  focusedConnectionId,
  focusedConnectionName,
  isFocusedConnectionOpen,
  onOpenSession,
}: SessionsPanelPlaceholderProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const sessions = useMemo(() => {
    if (!focusedConnectionId) return [];
    return buildPlaceholderSessions(focusedConnectionId);
  }, [focusedConnectionId]);

  return (
    <View style={styles.root}>
      <PanelHeader
        title="Sessions"
        subtitle={focusedConnectionName ? `Focused: ${focusedConnectionName}` : 'No focused connection'}
        menuLabel="↻"
      />

      {!focusedConnectionId ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>Select a connection above.</Text>
        </View>
      ) : !isFocusedConnectionOpen ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>Connection is closed.</Text>
          <Text style={styles.emptyMeta}>Open it to load sessions (task 070).</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {sessions.map((session) => (
            <Pressable
              key={session.sessionId}
              style={(state) => {
                const hovered = (state as any).hovered as boolean | undefined;
                return [styles.row, (hovered || state.pressed) && styles.rowHovered];
              }}
              onPress={() =>
                onOpenSession({
                  connectionId: focusedConnectionId,
                  sessionId: session.sessionId,
                  title: session.title,
                })
              }
            >
              <View style={styles.rowMain}>
                <Text style={styles.rowTitle} numberOfLines={1}>
                  {session.title}
                </Text>
                <Text style={styles.rowMeta} numberOfLines={1}>
                  {session.sessionId}
                </Text>
              </View>
              <Text style={styles.openHint}>Open</Text>
              <KebabMenu items={[{ label: 'Session actions (placeholder)' }]} />
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    list: {
      paddingVertical: 6,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
    },
    rowHovered: {
      backgroundColor: theme.surfaceAlt,
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
    openHint: {
      fontSize: 11,
      color: theme.primary,
      fontWeight: '600',
    },
    empty: {
      padding: 12,
      gap: 4,
    },
    emptyText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    emptyMeta: {
      fontSize: 11,
      color: theme.textMuted,
    },
  });
}
