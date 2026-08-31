import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import {
  useTheme,
  type HomeSessionCollections,
} from '@crystal-lattice/frontend-rn-components';
import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import type { SessionOpenMode } from '../settings/desktopGlobalSettings';
import { DesktopSessionCollectionItem } from './DesktopSessionCollectionItem';
import { DesktopWatchlistGrid } from './DesktopWatchlistGrid';

export function DesktopHomeView({
  collections,
  statuses,
  doubleClickAction,
  onOpenSession,
  onToggleWatch,
  onEditNote,
  onMoveWatchlistItem,
}: {
  collections: HomeSessionCollections;
  statuses: Readonly<
    Record<string, Readonly<Record<string, SessionRequestStatus>>>
  >;
  doubleClickAction: SessionOpenMode;
  onOpenSession: (
    item: HomeSessionCollections['watchlist'][number],
    mode: SessionOpenMode,
  ) => void;
  onToggleWatch: (
    item: HomeSessionCollections['watchlist'][number],
    watched: boolean,
  ) => void;
  onEditNote: (item: HomeSessionCollections['watchlist'][number]) => void;
  onMoveWatchlistItem: (fromIndex: number, toIndex: number) => void;
}): React.JSX.Element {
  const theme = useTheme();
  const styles = createStyles(theme);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  return (
    <ScrollView
      testID="desktop-home-view"
      style={styles.root}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.screenTitle}>Home</Text>
        <Text style={styles.screenSubtitle}>
          Watched and recent sessions across saved connections
        </Text>
      </View>
      <Text style={styles.sectionTitle}>Watchlist</Text>
      {collections.watchlist.length === 0 ? (
        <Text style={styles.empty}>
          Add a recent session to build your local Watchlist.
        </Text>
      ) : (
        <DesktopWatchlistGrid
          items={collections.watchlist}
          statuses={statuses}
          selectedKey={selectedKey}
          doubleClickAction={doubleClickAction}
          onSelect={setSelectedKey}
          onOpen={onOpenSession}
          onRemove={item => onToggleWatch(item, true)}
          onEditNote={onEditNote}
          onMove={onMoveWatchlistItem}
        />
      )}

      <Text style={[styles.sectionTitle, styles.recentTitle]}>
        Recent Sessions
      </Text>
      {collections.recent.length === 0 ? (
        <Text style={styles.empty}>
          No cached sessions were modified in this timeframe.
        </Text>
      ) : (
        <View style={styles.historyList} testID="desktop-home-history">
          {collections.recent.map(item => {
            const watched = collections.watchlist.some(
              candidate => candidate.key === item.key,
            );
            return (
              <DesktopSessionCollectionItem
                key={item.key}
                item={item}
                variant="history"
                selected={selectedKey === item.key}
                status={statuses[item.connectionId]?.[item.sessionId] ?? null}
                doubleClickAction={doubleClickAction}
                watched={watched}
                onSelect={() => setSelectedKey(item.key)}
                onOpen={mode => onOpenSession(item, mode)}
                onToggleWatch={() => onToggleWatch(item, watched)}
                onEditNote={() => onEditNote(item)}
              />
            );
          })}
        </View>
      )}
    </ScrollView>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.backgroundAlt,
    },
    content: {
      padding: 20,
      gap: 10,
    },
    header: {
      gap: 3,
      marginBottom: 6,
    },
    screenTitle: {
      fontSize: theme.typography.fontSize.screenTitle,
      lineHeight: theme.typography.lineHeight.screenTitle,
      fontWeight: '700',
      color: theme.text,
    },
    screenSubtitle: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
    },
    sectionTitle: {
      fontSize: theme.typography.fontSize.title,
      lineHeight: theme.typography.lineHeight.title,
      fontWeight: '700',
      color: theme.text,
    },
    recentTitle: {
      marginTop: 12,
    },
    historyList: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 12,
      overflow: 'hidden',
    },
    empty: {
      paddingVertical: 18,
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
  });
}
