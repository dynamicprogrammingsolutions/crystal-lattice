import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import {
  useTheme,
  type HomeSessionCollections,
} from '@crystal-lattice/frontend-rn-components';
import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import { DesktopSessionCollectionItem } from '../home/DesktopSessionCollectionItem';
import type { SessionOpenMode } from '../settings/desktopGlobalSettings';
import type { DesktopSessionTabKind } from '../tabs/desktopWorkspaceState';
import { PanelHeader } from '../ui/PanelHeader';

export function HistoryPanel({
  collections,
  statuses,
  doubleClickAction,
  onOpenSession,
  onToggleWatch,
  onEditNote,
  getSessionTabKind,
}: {
  collections: HomeSessionCollections;
  statuses: Readonly<
    Record<string, Readonly<Record<string, SessionRequestStatus>>>
  >;
  doubleClickAction: SessionOpenMode;
  onOpenSession: (
    item: HomeSessionCollections['recent'][number],
    mode: SessionOpenMode,
  ) => void;
  onToggleWatch: (
    item: HomeSessionCollections['recent'][number],
    watched: boolean,
  ) => void;
  onEditNote: (item: HomeSessionCollections['recent'][number]) => void;
  getSessionTabKind?: (
    connectionId: string,
    sessionId: string,
  ) => DesktopSessionTabKind | null;
}): React.JSX.Element {
  const theme = useTheme();
  const styles = createStyles(theme);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  return (
    <View style={styles.root} testID="desktop-history-panel">
      <PanelHeader
        title="History"
        subtitle="Recent sessions across connections"
      />
      <ScrollView style={styles.list}>
        {collections.recent.length === 0 ? (
          <Text style={styles.empty}>No recent cached sessions.</Text>
        ) : (
          collections.recent.map((item, index) => {
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
                tabKind={getSessionTabKind?.(item.connectionId, item.sessionId)}
                watched={watched}
                onSelect={() => setSelectedKey(item.key)}
                onOpen={mode => onOpenSession(item, mode)}
                onToggleWatch={() => onToggleWatch(item, watched)}
                onEditNote={() => onEditNote(item)}
                isLast={index === collections.recent.length - 1}
                presentationScope="panel-history"
              />
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.surface,
    },
    list: {
      flex: 1,
    },
    empty: {
      padding: 16,
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
    },
  });
}
