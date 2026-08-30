import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type LayoutChangeEvent,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';
import {
  useTheme,
  type Theme,
} from '@crystal-lattice/frontend-rn-components';

import type { OpenConnectionsById, OpenConnectionStatus } from '../connections/useOpenConnections';
import { KebabMenu } from '../ui/KebabMenu';
import { PanelHeader } from '../ui/PanelHeader';

export type ConnectionRowClickBehavior = 'focusOnly' | 'focusAndOpen' | 'focusAndToggleOpen';

const MAX_NATURAL_CONNECTION_ROWS = 3;
const LIST_VERTICAL_PADDING = 6;
const ROW_VERTICAL_PADDING = 8;
const ROW_TEXT_GAP = 2;
const OPEN_BUTTON_VERTICAL_PADDING = 6;
const BORDER_WIDTH = 1;
const BOTTOM_EPSILON = 1;

export function getConnectionsListMaxHeight(theme: Theme): number {
  const textColumnHeight =
    theme.typography.lineHeight.secondary +
    ROW_TEXT_GAP +
    theme.typography.lineHeight.tiny;
  const openButtonHeight =
    theme.typography.lineHeight.tiny +
    OPEN_BUTTON_VERTICAL_PADDING * 2 +
    BORDER_WIDTH * 2;
  const standardRowHeight =
    Math.max(textColumnHeight, openButtonHeight) + ROW_VERTICAL_PADDING * 2;
  return (
    LIST_VERTICAL_PADDING * 2 +
    standardRowHeight * MAX_NATURAL_CONNECTION_ROWS
  );
}

export function hasMoreConnectionListContent({
  offsetY,
  viewportHeight,
  contentHeight,
}: {
  offsetY: number;
  viewportHeight: number;
  contentHeight: number;
}): boolean {
  return (
    contentHeight > viewportHeight + BOTTOM_EPSILON &&
    offsetY + viewportHeight < contentHeight - BOTTOM_EPSILON
  );
}

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
  const [expanded, setExpanded] = useState(true);
  const hasBoundedList =
    connectionRecords.length > MAX_NATURAL_CONNECTION_ROWS;
  const [showBottomFade, setShowBottomFade] = useState(hasBoundedList);
  const scrollMetricsRef = useRef({
    offsetY: 0,
    viewportHeight: 0,
    contentHeight: 0,
  });

  const updateBottomFade = useCallback(
    (nextMetrics: Partial<typeof scrollMetricsRef.current>) => {
      const metrics = {
        ...scrollMetricsRef.current,
        ...nextMetrics,
      };
      scrollMetricsRef.current = metrics;
      setShowBottomFade(
        expanded &&
          hasBoundedList &&
          hasMoreConnectionListContent(metrics),
      );
    },
    [expanded, hasBoundedList],
  );

  useEffect(() => {
    scrollMetricsRef.current = {
      ...scrollMetricsRef.current,
      offsetY: 0,
    };
    setShowBottomFade(expanded && hasBoundedList);
  }, [connectionRecords.length, expanded, hasBoundedList]);

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

  const connectionRows = connectionRecords.map((record) => {
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

      if (!isOpen && !isConnecting) {
        onOpenConnection(record);
      }
    };

    return (
      <Pressable
        key={record.id}
        testID={`connection-row-${record.id}`}
        accessibilityLabel={`Connection ${record.name}`}
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
          accessibilityLabel={`${isOpen ? 'Close' : 'Open'} ${record.name}`}
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
  });

  const listContent = (
    <>
      {connectionRecords.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No saved connections.</Text>
          <Text style={styles.emptyMeta}>Use “New connection…” to add one.</Text>
        </View>
      ) : null}
      {connectionRows}
    </>
  );

  const handleScroll = (
    event: NativeSyntheticEvent<NativeScrollEvent>,
  ) => {
    const nativeEvent = event.nativeEvent;
    updateBottomFade({
      offsetY: nativeEvent.contentOffset.y,
      viewportHeight: nativeEvent.layoutMeasurement.height,
      contentHeight: nativeEvent.contentSize.height,
    });
  };

  const handleListLayout = (event: LayoutChangeEvent) => {
    updateBottomFade({
      viewportHeight: event.nativeEvent.layout.height,
    });
  };

  return (
    <View style={styles.root} testID="connections-panel">
      <PanelHeader
        title="Connections"
        subtitle={`${connectionRecords.length} saved • ${openCount} open`}
        right={(
          <Pressable
            testID="connections-collapse-toggle"
            accessibilityRole="button"
            accessibilityLabel={
              expanded ? 'Collapse connections' : 'Expand connections'
            }
            accessibilityState={{ expanded }}
            style={(state) => {
              const hovered = (state as any).hovered as boolean | undefined;
              return [
                styles.disclosureButton,
                (hovered || state.pressed) && styles.disclosureButtonHovered,
              ];
            }}
            onPress={() => setExpanded((current) => !current)}
          >
            <Icon
              name={expanded ? 'chevron-up' : 'chevron-down'}
              size={16}
              color={theme.textSecondary}
            />
          </Pressable>
        )}
        menuLabel="⋯"
        menuItems={menuItems}
      />

      {expanded ? (
        hasBoundedList ? (
          <View style={styles.listViewport} testID="connections-list-viewport">
            <ScrollView
              testID="connections-list-scroll"
              accessibilityLabel="Saved connections"
              accessibilityValue={{
                text: showBottomFade
                  ? 'More connections below'
                  : 'Bottom reached',
              }}
              style={styles.boundedList}
              contentContainerStyle={styles.list}
              showsVerticalScrollIndicator
              scrollEventThrottle={16}
              onLayout={handleListLayout}
              onContentSizeChange={(_width, height) =>
                updateBottomFade({ contentHeight: height })
              }
              onScroll={handleScroll}
            >
              {listContent}
            </ScrollView>
            {showBottomFade ? (
              <View
                testID="connections-list-bottom-fade"
                style={styles.bottomFade}
                pointerEvents="none"
                accessible
                accessibilityLabel="More connections below"
              >
                <View style={[styles.fadeBand, styles.fadeBandLight]} />
                <View style={[styles.fadeBand, styles.fadeBandMedium]} />
                <View style={[styles.fadeBand, styles.fadeBandStrong]} />
                <View style={[styles.fadeBand, styles.fadeBandSolid]} />
              </View>
            ) : null}
          </View>
        ) : (
          <View style={styles.list} testID="connections-list-static">
            {listContent}
          </View>
        )
      ) : null}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = BORDER_WIDTH;

  return StyleSheet.create({
    root: {
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    disclosureButton: {
      width: 30,
      height: 30,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 8,
    },
    disclosureButtonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    listViewport: {
      position: 'relative',
    },
    boundedList: {
      maxHeight: getConnectionsListMaxHeight(theme),
    },
    list: {
      paddingVertical: LIST_VERTICAL_PADDING,
    },
    bottomFade: {
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      height: theme.typography.lineHeight.normal,
    },
    fadeBand: {
      flex: 1,
      backgroundColor: theme.surface,
    },
    fadeBandLight: {
      opacity: 0.18,
    },
    fadeBandMedium: {
      opacity: 0.42,
    },
    fadeBandStrong: {
      opacity: 0.72,
    },
    fadeBandSolid: {
      opacity: 0.96,
    },
    empty: {
      paddingHorizontal: 10,
      paddingVertical: 10,
      gap: 2,
    },
    emptyText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    emptyMeta: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      paddingHorizontal: 10,
      paddingVertical: ROW_VERTICAL_PADDING,
    },
    rowHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    rowFocused: {
      backgroundColor: theme.primaryMuted,
    },
    rowMain: {
      flex: 1,
      gap: ROW_TEXT_GAP,
    },
    rowTitleLine: {
      flexDirection: 'row',
      alignItems: 'baseline',
      justifyContent: 'space-between',
      gap: 10,
    },
    rowTitle: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '700',
      color: theme.text,
      flex: 1,
    },
    status: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      fontWeight: '700',
    },
    rowMeta: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
    },
    rowError: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.danger,
    },
    openButton: {
      paddingHorizontal: 10,
      paddingVertical: OPEN_BUTTON_VERTICAL_PADDING,
      borderRadius: 8,
      borderWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    openButtonPressed: {
      opacity: 0.8,
    },
    openButtonText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      fontWeight: '800',
    },
  });
}

export { createStyles as createConnectionsPanelStyles };
