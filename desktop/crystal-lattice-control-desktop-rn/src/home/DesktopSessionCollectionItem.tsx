import React, { useMemo } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  type ViewProps,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  SessionRequestStatusIndicator,
  useTheme,
  type HomeSessionItem,
} from '@crystal-lattice/frontend-rn-components';
import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import {
  complementarySessionOpenMode,
  sessionOpenModeLabel,
  type SessionOpenMode,
} from '../settings/desktopGlobalSettings';
import { useSessionItemPress } from '../sessions/sessionItemInteraction';

export function DesktopSessionCollectionItem({
  item,
  variant,
  selected,
  status,
  doubleClickAction,
  watched,
  onSelect,
  onOpen,
  onToggleWatch,
  onEditNote,
  onMoveEarlier,
  onMoveLater,
  dragHandleProps,
}: {
  item: HomeSessionItem;
  variant: 'tile' | 'history';
  selected: boolean;
  status: SessionRequestStatus | null;
  doubleClickAction: SessionOpenMode;
  watched: boolean;
  onSelect: () => void;
  onOpen: (mode: SessionOpenMode) => void;
  onToggleWatch: () => void;
  onEditNote: () => void;
  onMoveEarlier?: () => void;
  onMoveLater?: () => void;
  dragHandleProps?: ViewProps;
}): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const presentation = item.summary.presentation;
  const title =
    presentation?.title || item.summary.preview || item.summary.session_id;
  const subtitle = presentation?.subtitle || item.connection.name;
  const explicitMode = complementarySessionOpenMode(doubleClickAction);
  const handlePress = useSessionItemPress({
    key: item.key,
    doubleClickAction,
    onSelect,
    onOpen,
  });

  return (
    <Pressable
      testID={`desktop-${variant}-session-${item.connectionId}-${item.sessionId}`}
      accessibilityLabel={`${title}, ${item.connection.name}`}
      accessibilityState={{ selected }}
      style={state => [
        variant === 'tile' ? styles.tile : styles.history,
        selected && styles.selected,
        (((state as any).hovered as boolean | undefined) || state.pressed) &&
          styles.hovered,
      ]}
      onPress={handlePress}
    >
      <View style={styles.headingRow}>
        <Text style={styles.title} numberOfLines={2}>
          {title}
        </Text>
        {variant === 'tile' && dragHandleProps ? (
          <View
            testID={`desktop-watchlist-drag-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={`Reorder ${title}`}
            style={styles.dragHandle}
            {...dragHandleProps}
          >
            <Icon name="move" size={14} color={theme.textMuted} />
          </View>
        ) : null}
        <SessionRequestStatusIndicator
          status={status}
          variant={variant === 'tile' ? 'badge' : 'inline'}
          testID={`desktop-session-status-${item.connectionId}-${item.sessionId}`}
        />
      </View>
      <Text style={styles.subtitle} numberOfLines={1}>
        {subtitle}
      </Text>
      <Text style={styles.sessionId} numberOfLines={1}>
        {item.sessionId}
      </Text>
      {item.note ? (
        <Text style={styles.note} numberOfLines={variant === 'tile' ? 2 : 1}>
          {item.note}
        </Text>
      ) : null}
      <View style={styles.footer}>
        <Text style={styles.modified}>
          {formatRelativeTime(item.summary.modified)}
        </Text>
        <View style={styles.actions}>
          {onMoveEarlier ? (
            <SmallIconButton
              icon="arrow-left"
              label="Move earlier"
              onPress={onMoveEarlier}
            />
          ) : null}
          {onMoveLater ? (
            <SmallIconButton
              icon="arrow-right"
              label="Move later"
              onPress={onMoveLater}
            />
          ) : null}
          <SmallIconButton
            icon="edit-3"
            label="Edit local note"
            onPress={onEditNote}
          />
          <SmallIconButton
            icon={watched ? 'x' : 'bookmark'}
            label={watched ? 'Remove from Watchlist' : 'Add to Watchlist'}
            onPress={onToggleWatch}
          />
          <Pressable
            testID={`desktop-session-${explicitMode}-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={`${sessionOpenModeLabel(
              explicitMode,
            )} ${title}`}
            style={styles.openButton}
            onPress={event => {
              (event as any)?.stopPropagation?.();
              onOpen(explicitMode);
            }}
          >
            <Text style={styles.openButtonText}>
              {sessionOpenModeLabel(explicitMode)}
            </Text>
          </Pressable>
        </View>
      </View>
    </Pressable>
  );
}

function SmallIconButton({
  icon,
  label,
  onPress,
}: {
  icon: string;
  label: string;
  onPress: () => void;
}) {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  return (
    <Pressable
      accessibilityLabel={label}
      style={styles.iconButton}
      onPress={event => {
        (event as any)?.stopPropagation?.();
        onPress();
      }}
    >
      <Icon name={icon} size={13} color={theme.textSecondary} />
    </Pressable>
  );
}

function formatRelativeTime(modifiedSeconds: number): string {
  const deltaSeconds = Math.max(
    0,
    Math.round(Date.now() / 1000 - modifiedSeconds),
  );
  if (deltaSeconds < 60) return 'Just now';
  const minutes = Math.floor(deltaSeconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    tile: {
      width: '100%',
      minHeight: 160,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 12,
      padding: 12,
      gap: 5,
      backgroundColor: theme.surface,
    },
    history: {
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
      paddingVertical: 10,
      paddingHorizontal: 10,
      gap: 4,
      backgroundColor: theme.surface,
    },
    selected: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    hovered: {
      backgroundColor: theme.surfaceAlt,
    },
    headingRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 8,
    },
    title: {
      flex: 1,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '700',
      color: theme.text,
    },
    subtitle: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      color: theme.textSecondary,
    },
    sessionId: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    note: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      fontStyle: 'italic',
      flexGrow: 1,
    },
    footer: {
      marginTop: 'auto',
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 8,
    },
    modified: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    actions: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 4,
    },
    iconButton: {
      width: 26,
      height: 26,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 6,
    },
    dragHandle: {
      width: 26,
      height: 26,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 6,
    },
    openButton: {
      minHeight: 26,
      paddingHorizontal: 9,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 7,
      borderWidth: 1,
      borderColor: theme.primary,
      backgroundColor: theme.surface,
    },
    openButtonText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.primary,
      fontWeight: '700',
    },
  });
}
