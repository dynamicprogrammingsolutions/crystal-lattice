import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

import type { SessionSummary } from '@crystal-lattice/frontend-sdk';

import { PanelHeader } from '../ui/PanelHeader';
import { KebabMenu } from '../ui/KebabMenu';

export interface SessionsPanelPlaceholderProps {
  focusedConnectionId: string | null;
  focusedConnectionName: string | null;
  isFocusedConnectionOpen: boolean;
  cachedSessions: SessionSummary[];
  cachedLastLoadedAt: number | null;
  onOpenSession: (params: { connectionId: string; sessionId: string; title: string }) => void;
}

export function SessionsPanelPlaceholder({
  focusedConnectionId,
  focusedConnectionName,
  isFocusedConnectionOpen,
  cachedSessions,
  cachedLastLoadedAt,
  onOpenSession,
}: SessionsPanelPlaceholderProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const subtitle = useMemo(() => {
    if (!focusedConnectionName) {
      return 'No focused connection';
    }
    const cachedLabel =
      cachedLastLoadedAt ? `cached ${new Date(cachedLastLoadedAt).toLocaleTimeString()}` : 'no cache';
    const liveLabel = isFocusedConnectionOpen ? 'online' : 'offline';
    return `Focused: ${focusedConnectionName} • ${liveLabel} • ${cachedLabel}`;
  }, [cachedLastLoadedAt, focusedConnectionName, isFocusedConnectionOpen]);

  return (
    <View style={styles.root}>
      <PanelHeader
        title="Sessions"
        subtitle={subtitle}
        menuLabel="↻"
      />

      {!focusedConnectionId ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>Select a connection above.</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {cachedSessions.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>No cached sessions.</Text>
              <Text style={styles.emptyMeta}>
                {isFocusedConnectionOpen
                  ? 'Connect and refresh to populate cache (task 070).'
                  : 'Open the connection to refresh (task 070).'}
              </Text>
            </View>
          ) : null}

          {cachedSessions.map((session) => (
            <Pressable
              key={session.session_id}
              style={(state) => {
                const hovered = (state as any).hovered as boolean | undefined;
                return [styles.row, (hovered || state.pressed) && styles.rowHovered];
              }}
              onPress={() =>
                onOpenSession({
                  connectionId: focusedConnectionId,
                  sessionId: session.session_id,
                  title: session.preview ? session.preview.slice(0, 48) : session.session_id,
                })
              }
            >
              <View style={styles.rowMain}>
                <Text style={styles.rowTitle} numberOfLines={1}>
                  {session.preview ? session.preview.slice(0, 64) : session.session_id}
                </Text>
                <Text style={styles.rowMeta} numberOfLines={1}>
                  {session.session_id}
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
