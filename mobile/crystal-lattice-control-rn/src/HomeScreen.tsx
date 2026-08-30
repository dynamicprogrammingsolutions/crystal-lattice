import React, { useMemo, useRef, useState } from 'react';
import {
  Animated,
  Modal,
  PanResponder,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type {
  ConnectionRecord,
  SessionRequestStatus,
} from '@crystal-lattice/frontend-sdk';
import {
  ActionsMenuBar,
  type ActionDefinition,
} from '@crystal-lattice/frontend-rn-components';

import type { SessionsCache } from '../App';
import { useHomeWorkspace } from './HomeWorkspaceContext';
import {
  deriveHomeSessionCollections,
  type HomeSessionItem,
} from './homeWorkspaceState';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import { useTheme, type Theme } from './theme';
import SessionNoteModal from './components/SessionNoteModal';
import SessionRequestStatusBadge from './components/SessionRequestStatusBadge';

interface HomeActionDefinition extends ActionDefinition {
  iconName: string;
}

const HOME_ACTIONS: HomeActionDefinition[] = [
  { key: 'settings', label: 'Global settings', iconName: 'settings' },
  { key: 'newConnection', label: 'New connection', iconName: 'wifi' },
  { key: 'newSession', label: 'New session', iconName: 'plus' },
];

interface HomeScreenProps {
  connections: readonly ConnectionRecord[];
  sessionsCache: SessionsCache;
  statusesByConnection: Readonly<
    Record<string, Readonly<Record<string, SessionRequestStatus>>>
  >;
  hasActiveBackend: boolean;
  isActive: boolean;
  onOpenGlobalSettings: () => void;
  onNewConnection: () => void;
  onNewSession: () => void;
  onSelectSession: (connectionId: string, sessionId: string) => void;
}

function sessionTitle(item: HomeSessionItem): string {
  return (
    item.summary.presentation?.title ||
    item.summary.preview?.split('\n')[0]?.trim() ||
    item.sessionId
  );
}

function relativeModified(modified: number): string {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - modified));
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

const WatchlistTile: React.FC<{
  item: HomeSessionItem;
  index: number;
  itemCount: number;
  status: SessionRequestStatus | null;
  onPress: () => void;
  onMove: (fromIndex: number, toIndex: number) => void;
  onEditNote: () => void;
  onRemove: () => void;
}> = ({
  item,
  index,
  itemCount,
  status,
  onPress,
  onMove,
  onEditNote,
  onRemove,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const drag = useRef(new Animated.ValueXY()).current;
  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: (_event, gesture) =>
          Math.abs(gesture.dx) > 4 || Math.abs(gesture.dy) > 4,
        onPanResponderMove: Animated.event(
          [null, { dx: drag.x, dy: drag.y }],
          { useNativeDriver: false },
        ),
        onPanResponderRelease: (_event, gesture) => {
          const rowDelta = Math.round(gesture.dy / 120) * 2;
          const columnDelta =
            gesture.dx > 45 ? 1 : gesture.dx < -45 ? -1 : 0;
          const target = Math.max(
            0,
            Math.min(itemCount - 1, index + rowDelta + columnDelta),
          );
          drag.setValue({ x: 0, y: 0 });
          if (target !== index) onMove(index, target);
        },
        onPanResponderTerminate: () => {
          drag.setValue({ x: 0, y: 0 });
        },
      }),
    [drag, index, itemCount, onMove],
  );

  return (
    <Animated.View
      testID={`home-watchlist-tile-${item.connectionId}-${item.sessionId}`}
      style={[
        styles.watchTile,
        { transform: drag.getTranslateTransform() },
      ]}
    >
      <View style={styles.tileTopRow}>
        <View
          testID={`home-watchlist-drag-${item.connectionId}-${item.sessionId}`}
          accessibilityRole="adjustable"
          accessibilityLabel={`Reorder ${sessionTitle(item)}`}
          accessibilityActions={[
            { name: 'increment', label: 'Move later' },
            { name: 'decrement', label: 'Move earlier' },
          ]}
          onAccessibilityAction={(event) => {
            if (event.nativeEvent.actionName === 'increment') {
              onMove(index, Math.min(itemCount - 1, index + 1));
            } else if (event.nativeEvent.actionName === 'decrement') {
              onMove(index, Math.max(0, index - 1));
            }
          }}
          style={styles.dragHandle}
          {...panResponder.panHandlers}
        >
          <Icon name="move" size={17} color={theme.textSecondary} />
        </View>
        <View style={styles.tileActions}>
          <TouchableOpacity
            testID={`home-watchlist-note-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={item.note ? 'Edit session note' : 'Add session note'}
            style={styles.iconButton}
            onPress={onEditNote}
          >
            <Icon
              name={item.note ? 'edit-3' : 'file-plus'}
              size={16}
              color={theme.primary}
            />
          </TouchableOpacity>
          <TouchableOpacity
            testID={`home-watchlist-remove-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel="Remove from Watchlist"
            style={styles.iconButton}
            onPress={onRemove}
          >
            <Icon name="bookmark" size={16} color={theme.primary} />
          </TouchableOpacity>
        </View>
      </View>
      <TouchableOpacity
        testID={`home-watchlist-open-${item.connectionId}-${item.sessionId}`}
        style={styles.tileBody}
        onPress={onPress}
      >
        <Text style={styles.watchTitle} numberOfLines={2}>
          {sessionTitle(item)}
        </Text>
        <Text style={styles.connectionName} numberOfLines={1}>
          {item.connection.name}
        </Text>
        <SessionRequestStatusBadge
          status={status}
          testID={`home-watchlist-status-${item.connectionId}-${item.sessionId}`}
        />
        {item.note ? (
          <Text
            testID={`home-watchlist-note-preview-${item.connectionId}-${item.sessionId}`}
            style={styles.notePreview}
            numberOfLines={2}
          >
            {item.note}
          </Text>
        ) : null}
        <Text style={styles.relativeTime}>
          {relativeModified(item.summary.modified)}
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
};

const HomeScreen: React.FC<HomeScreenProps> = ({
  connections,
  sessionsCache,
  statusesByConnection,
  hasActiveBackend,
  isActive,
  onOpenGlobalSettings,
  onNewConnection,
  onNewSession,
  onSelectSession,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const {
    hydrated,
    watchlist,
    notes,
    recentSessionsWindow,
    addToWatchlist,
    removeFromWatchlist,
    moveWatchlistItem,
    setSessionNote,
    removeSessionNote,
  } = useHomeWorkspace();
  const { pinned, setPinned } = usePersistentPinnedActions<string>(
    'clc_pinned_home_actions_v1',
    ['settings', 'newConnection'],
  );
  const [menuVisible, setMenuVisible] = useState(false);
  const [noteSessionId, setNoteSessionId] = useState<string | null>(null);
  const collections = useMemo(
    () =>
      deriveHomeSessionCollections({
        connections,
        sessionsCache,
        watchlist,
        notes,
        recentSessionsWindow,
      }),
    [
      connections,
      notes,
      recentSessionsWindow,
      sessionsCache,
      watchlist,
    ],
  );
  const recentWindowLabel =
    recentSessionsWindow === '24h'
      ? 'Last 24 hours'
      : recentSessionsWindow === '1w'
        ? 'Last week'
        : 'Last 3 days';

  if (!hydrated) {
    return (
      <View style={styles.centered}>
        <Text style={styles.emptyText}>Loading Home…</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header} testID="home-screen-header">
        <TouchableOpacity
          testID="home-menu"
          accessibilityLabel="Open Home menu"
          style={styles.headerIcon}
          onPress={() => setMenuVisible(true)}
        >
          <Icon name="menu" size={21} color={theme.text} />
        </TouchableOpacity>
        <Text style={styles.screenTitle}>Home</Text>
        <View style={styles.homeActions}>
          <ActionsMenuBar<HomeActionDefinition>
            title="Home actions"
            baseActions={HOME_ACTIONS}
            pinned={pinned}
            onChangePinned={setPinned}
            isActive={isActive}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            renderPinIcon={({ size, color }) => (
              <Icon name="star" size={size} color={color} />
            )}
            menuButtonTestID="home-actions-menu"
            isActionDisabled={(key) =>
              key === 'newSession' && !hasActiveBackend
            }
            onAction={(key) => {
              if (key === 'settings') onOpenGlobalSettings();
              if (key === 'newConnection') onNewConnection();
              if (key === 'newSession') onNewSession();
            }}
          />
        </View>
      </View>

      <ScrollView
        testID="home-scroll"
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Watchlist</Text>
          <Text style={styles.sectionHint}>Stored on this device</Text>
        </View>
        {collections.watchlist.length === 0 ? (
          <Text style={styles.emptyText}>
            Add recent sessions to your Watchlist for quick access.
          </Text>
        ) : (
          <View style={styles.watchGrid} testID="home-watchlist-grid">
            {collections.watchlist.map((item, index) => (
              <WatchlistTile
                key={item.key}
                item={item}
                index={index}
                itemCount={collections.watchlist.length}
                status={
                  statusesByConnection[item.connectionId]?.[item.sessionId] ??
                  null
                }
                onPress={() =>
                  onSelectSession(item.connectionId, item.sessionId)
                }
                onMove={moveWatchlistItem}
                onEditNote={() => setNoteSessionId(item.sessionId)}
                onRemove={() =>
                  removeFromWatchlist(item.connectionId, item.sessionId)
                }
              />
            ))}
          </View>
        )}

        <View style={[styles.sectionHeader, styles.recentHeader]}>
          <Text style={styles.sectionTitle}>Recent Sessions</Text>
          <Text style={styles.sectionHint}>{recentWindowLabel}</Text>
        </View>
        {collections.recent.length === 0 ? (
          <Text style={styles.emptyText}>
            No cached sessions were modified in this timeframe.
          </Text>
        ) : (
          <View testID="home-recent-timeline">
            {collections.recent.map((item, index) => (
              <View
                key={item.key}
                style={styles.timelineRow}
                testID={`home-recent-${item.connectionId}-${item.sessionId}`}
              >
                <View style={styles.timelineRail}>
                  <View style={styles.timelineDot} />
                  {index < collections.recent.length - 1 ? (
                    <View style={styles.timelineLine} />
                  ) : null}
                </View>
                <TouchableOpacity
                  testID={`home-recent-open-${item.connectionId}-${item.sessionId}`}
                  style={styles.timelineBody}
                  onPress={() =>
                    onSelectSession(item.connectionId, item.sessionId)
                  }
                >
                  <Text style={styles.recentTitle} numberOfLines={2}>
                    {sessionTitle(item)}
                  </Text>
                  <Text style={styles.connectionName} numberOfLines={1}>
                    {item.connection.name} · {relativeModified(item.summary.modified)}
                  </Text>
                  <SessionRequestStatusBadge
                    status={
                      statusesByConnection[item.connectionId]?.[
                        item.sessionId
                      ] ?? null
                    }
                    testID={`home-recent-status-${item.connectionId}-${item.sessionId}`}
                  />
                  {item.note ? (
                    <Text style={styles.notePreview} numberOfLines={2}>
                      {item.note}
                    </Text>
                  ) : null}
                </TouchableOpacity>
                <View style={styles.timelineActions}>
                  <TouchableOpacity
                    testID={`home-recent-note-${item.connectionId}-${item.sessionId}`}
                    accessibilityLabel={
                      item.note ? 'Edit session note' : 'Add session note'
                    }
                    style={styles.iconButton}
                    onPress={() => setNoteSessionId(item.sessionId)}
                  >
                    <Icon
                      name={item.note ? 'edit-3' : 'file-plus'}
                      size={17}
                      color={theme.primary}
                    />
                  </TouchableOpacity>
                  <TouchableOpacity
                    testID={`home-recent-watch-${item.connectionId}-${item.sessionId}`}
                    accessibilityLabel="Add to Watchlist"
                    style={styles.iconButton}
                    onPress={() =>
                      addToWatchlist(item.connectionId, item.sessionId)
                    }
                  >
                    <Icon name="bookmark" size={17} color={theme.primary} />
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      <Modal
        visible={menuVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setMenuVisible(false)}
      >
        <TouchableOpacity
          style={styles.menuOverlay}
          activeOpacity={1}
          onPress={() => setMenuVisible(false)}
        >
          <View style={styles.menuPanel}>
            <Text style={styles.menuTitle}>Home menu</Text>
            <TouchableOpacity
              testID="home-menu-global-settings"
              style={styles.menuItem}
              onPress={() => {
                setMenuVisible(false);
                onOpenGlobalSettings();
              }}
            >
              <Icon name="settings" size={18} color={theme.text} />
              <Text style={styles.menuItemText}>Global Settings</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      <SessionNoteModal
        visible={noteSessionId !== null}
        sessionId={noteSessionId}
        note={noteSessionId ? notes[noteSessionId] ?? null : null}
        onSave={(note) => {
          if (noteSessionId) setSessionNote(noteSessionId, note);
        }}
        onRemove={() => {
          if (noteSessionId) removeSessionNote(noteSessionId);
        }}
        onRequestClose={() => setNoteSessionId(null)}
      />
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    container: {
      flex: 1,
    },
    centered: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
    },
    header: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    headerIcon: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
    },
    screenTitle: {
      flex: 1,
      color: theme.text,
      fontSize: theme.typography.fontSize.title,
      lineHeight: theme.typography.lineHeight.title,
      fontWeight: '700',
      marginLeft: 4,
    },
    homeActions: {
      flexShrink: 1,
    },
    scroll: {
      flex: 1,
    },
    scrollContent: {
      paddingBottom: 24,
    },
    sectionHeader: {
      flexDirection: 'row',
      alignItems: 'baseline',
      justifyContent: 'space-between',
      gap: 12,
      marginBottom: 8,
    },
    recentHeader: {
      marginTop: 22,
    },
    sectionTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.large,
      lineHeight: theme.typography.lineHeight.large,
      fontWeight: '700',
    },
    sectionHint: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
    },
    watchGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      rowGap: 10,
    },
    watchTile: {
      width: '48.5%',
      minHeight: 172,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 14,
      backgroundColor: theme.surface,
      padding: 10,
      zIndex: 1,
    },
    tileTopRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 4,
    },
    dragHandle: {
      width: 36,
      height: 32,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    tileActions: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    iconButton: {
      width: 36,
      height: 36,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 8,
    },
    tileBody: {
      flex: 1,
    },
    watchTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '700',
      marginBottom: 3,
    },
    recentTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.large,
      lineHeight: theme.typography.lineHeight.large,
      fontWeight: '600',
    },
    connectionName: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      marginBottom: 6,
    },
    notePreview: {
      color: theme.text,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontStyle: 'italic',
      marginTop: 7,
    },
    relativeTime: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      marginTop: 'auto',
      paddingTop: 6,
    },
    emptyText: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      paddingVertical: 14,
    },
    timelineRow: {
      flexDirection: 'row',
      minHeight: 96,
    },
    timelineRail: {
      width: 24,
      alignItems: 'center',
    },
    timelineDot: {
      width: 10,
      height: 10,
      marginTop: 7,
      borderRadius: 5,
      backgroundColor: theme.primary,
    },
    timelineLine: {
      width: 2,
      flex: 1,
      marginVertical: 4,
      backgroundColor: theme.border,
    },
    timelineBody: {
      flex: 1,
      paddingBottom: 18,
      paddingHorizontal: 8,
    },
    timelineActions: {
      flexDirection: 'row',
      alignSelf: 'flex-start',
    },
    menuOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      paddingTop: 58,
      paddingHorizontal: 16,
    },
    menuPanel: {
      width: 260,
      borderRadius: 12,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      padding: 10,
    },
    menuTitle: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '600',
      paddingHorizontal: 8,
      paddingBottom: 6,
    },
    menuItem: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      paddingHorizontal: 8,
    },
    menuItemText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
  });

export default HomeScreen;