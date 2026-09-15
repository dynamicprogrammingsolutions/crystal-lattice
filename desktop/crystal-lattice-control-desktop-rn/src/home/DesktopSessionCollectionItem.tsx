import React, { useMemo } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
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
  sessionOpenModeLabel,
  type SessionOpenMode,
} from '../settings/desktopGlobalSettings';
import {
  resolveExplicitSessionOpenMode,
  useSessionItemPress,
} from '../sessions/sessionItemInteraction';
import type { DesktopSessionTabKind } from '../tabs/desktopWorkspaceState';
import { resolveDesktopHomeSessionPresentation } from './homeSessionPresentation';

export function DesktopSessionCollectionItem({
  item,
  variant,
  selected,
  status,
  doubleClickAction,
  tabKind = null,
  watched,
  onSelect,
  onOpen,
  onToggleWatch,
  onEditNote,
  onMoveEarlier,
  onMoveLater,
  dragHandleProps,
  isLast = false,
  presentationScope,
}: {
  item: HomeSessionItem;
  variant: 'tile' | 'history';
  selected: boolean;
  status: SessionRequestStatus | null;
  doubleClickAction: SessionOpenMode;
  tabKind?: DesktopSessionTabKind | null;
  watched: boolean;
  onSelect: () => void;
  onOpen: (mode: SessionOpenMode) => void;
  onToggleWatch: () => void;
  onEditNote: () => void;
  onMoveEarlier?: () => void;
  onMoveLater?: () => void;
  dragHandleProps?: ViewProps;
  isLast?: boolean;
  presentationScope?: string;
}): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const presentation = resolveDesktopHomeSessionPresentation(item);
  const fieldScope = presentationScope ?? variant;
  const explicitMode = resolveExplicitSessionOpenMode(
    doubleClickAction,
    tabKind,
  );
  const handlePress = useSessionItemPress({
    key: item.key,
    doubleClickAction,
    onSelect,
    onOpen,
  });

  const details = (
    <>
      <View style={styles.headingRow}>
        <AccessibleField
          testID={`desktop-${fieldScope}-title-${item.connectionId}-${item.sessionId}`}
          label={presentation.title}
          style={styles.titleField}
        >
          <Text
            testID={`desktop-${fieldScope}-title-${item.connectionId}-${item.sessionId}`}
            style={styles.title}
            numberOfLines={2}
          >
            {presentation.title}
          </Text>
        </AccessibleField>
        {variant === 'tile' && dragHandleProps ? (
          <View
            testID={`desktop-watchlist-drag-${item.connectionId}-${item.sessionId}`}
            accessibilityLabel={`Reorder ${presentation.title}`}
            style={styles.dragHandle}
            {...dragHandleProps}
          >
            <Icon name="move" size={14} color={theme.textMuted} />
          </View>
        ) : null}
      </View>
      {presentation.subtitle ? (
        <AccessibleField
          testID={`desktop-${fieldScope}-subtitle-${item.connectionId}-${item.sessionId}`}
          label={presentation.subtitle}
        >
          <Text
            testID={`desktop-${fieldScope}-subtitle-${item.connectionId}-${item.sessionId}`}
            style={styles.subtitle}
            numberOfLines={2}
          >
            {presentation.subtitle}
          </Text>
        </AccessibleField>
      ) : null}
      <AccessibleField
        testID={`desktop-${fieldScope}-session-id-${item.connectionId}-${item.sessionId}`}
        label={`Session ID ${presentation.sessionId}`}
      >
        <Text
          testID={`desktop-${fieldScope}-session-id-${item.connectionId}-${item.sessionId}`}
          style={styles.sessionId}
          numberOfLines={1}
          ellipsizeMode="tail"
        >
          {presentation.sessionId}
        </Text>
      </AccessibleField>
      {status ? (
        <View style={styles.statusRow}>
          <SessionRequestStatusIndicator
            status={status}
            variant={variant === 'tile' ? 'badge' : 'inline'}
            testID={
              variant === 'tile'
                ? `desktop-session-status-${item.connectionId}-${item.sessionId}`
                : `desktop-${fieldScope}-status-${item.connectionId}-${item.sessionId}`
            }
          />
        </View>
      ) : null}
      {item.note ? (
        <Text
          testID={`desktop-${fieldScope}-note-${item.connectionId}-${item.sessionId}`}
          style={styles.note}
          numberOfLines={2}
        >
          {item.note}
        </Text>
      ) : null}
      <View
        testID={`desktop-${fieldScope}-metadata-${item.connectionId}-${item.sessionId}`}
        style={[
          styles.metadataRow,
          variant === 'tile' && styles.tileMetadataRow,
        ]}
      >
        <AccessibleField
          testID={`desktop-${fieldScope}-connection-${item.connectionId}-${item.sessionId}`}
          label={`Connection ${presentation.connectionName}`}
          style={styles.metadataConnectionField}
        >
          <Text
            testID={`desktop-${fieldScope}-connection-${item.connectionId}-${item.sessionId}`}
            style={styles.metadataConnection}
            numberOfLines={1}
            ellipsizeMode="tail"
          >
            {presentation.connectionName}
          </Text>
        </AccessibleField>
        <AccessibleField
          testID={`desktop-${fieldScope}-time-${item.connectionId}-${item.sessionId}`}
          label={`Modified ${presentation.relativeTime}`}
          style={styles.metadataTimeField}
        >
          <Text
            testID={`desktop-${fieldScope}-time-${item.connectionId}-${item.sessionId}`}
            style={styles.metadataTime}
            numberOfLines={1}
          >
            {presentation.relativeTime}
          </Text>
        </AccessibleField>
      </View>
    </>
  );

  const actions = (
    <>
      {onMoveEarlier ? (
        <SmallIconButton
          testID={`desktop-${fieldScope}-move-earlier-${item.connectionId}-${item.sessionId}`}
          icon="arrow-left"
          label="Move earlier"
          onPress={onMoveEarlier}
        />
      ) : null}
      {onMoveLater ? (
        <SmallIconButton
          testID={`desktop-${fieldScope}-move-later-${item.connectionId}-${item.sessionId}`}
          icon="arrow-right"
          label="Move later"
          onPress={onMoveLater}
        />
      ) : null}
      <SmallIconButton
        testID={`desktop-${fieldScope}-note-action-${item.connectionId}-${item.sessionId}`}
        icon="edit-3"
        label="Edit local note"
        onPress={onEditNote}
      />
      <SmallIconButton
        testID={`desktop-${fieldScope}-watch-action-${item.connectionId}-${item.sessionId}`}
        icon={watched ? 'x' : 'bookmark'}
        label={watched ? 'Remove from Watchlist' : 'Add to Watchlist'}
        onPress={onToggleWatch}
      />
      <Pressable
        testID={`desktop-session-${explicitMode}-${item.connectionId}-${item.sessionId}`}
        accessibilityLabel={`${sessionOpenModeLabel(explicitMode)} ${
          presentation.title
        }`}
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
    </>
  );

  const body = (
    <Pressable
      testID={`desktop-${variant}-session-${item.connectionId}-${item.sessionId}`}
      accessibilityLabel={`${presentation.title}, ${presentation.connectionName}`}
      accessibilityState={{ selected }}
      style={state => [
        variant === 'tile' ? styles.tile : styles.history,
        selected && styles.selected,
        (((state as any).hovered as boolean | undefined) || state.pressed) &&
          styles.hovered,
      ]}
      onPress={handlePress}
    >
      {details}
      {variant === 'tile' ? (
        <View
          testID={`desktop-${fieldScope}-actions-${item.connectionId}-${item.sessionId}`}
          style={styles.tileActions}
        >
          {actions}
        </View>
      ) : null}
    </Pressable>
  );

  if (variant === 'tile') {
    return body;
  }

  return (
    <View style={styles.timelineRow}>
      <View style={styles.timelineRail}>
        <View
          testID={`desktop-${fieldScope}-dot-${item.connectionId}-${item.sessionId}`}
          accessible
          accessibilityLabel="Timeline event"
          style={styles.timelineDot}
        />
        {!isLast ? (
          <View
            testID={`desktop-${fieldScope}-line-${item.connectionId}-${item.sessionId}`}
            style={styles.timelineLine}
          />
        ) : null}
      </View>
      {body}
      <View
        testID={`desktop-${fieldScope}-actions-${item.connectionId}-${item.sessionId}`}
        style={styles.timelineActions}
      >
        {actions}
      </View>
    </View>
  );
}

function AccessibleField({
  testID,
  label,
  style,
  children,
}: {
  testID: string;
  label: string;
  style?: StyleProp<ViewStyle>;
  children: React.ReactNode;
}) {
  return (
    <View
      testID={`${testID}-native`}
      accessible
      accessibilityLabel={label}
      style={style}
    >
      {children}
    </View>
  );
}

function SmallIconButton({
  testID,
  icon,
  label,
  onPress,
}: {
  testID?: string;
  icon: string;
  label: string;
  onPress: () => void;
}) {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  return (
    <Pressable
      testID={testID}
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

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    tile: {
      width: '100%',
      minHeight: 180,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 12,
      padding: 12,
      gap: 5,
      backgroundColor: theme.surface,
    },
    history: {
      flex: 1,
      minWidth: 0,
      paddingBottom: 16,
      paddingHorizontal: 8,
      gap: 4,
      backgroundColor: theme.surface,
      borderRadius: 8,
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
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '700',
      color: theme.text,
    },
    titleField: {
      minWidth: 0,
      flex: 1,
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
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      color: theme.textSecondary,
      fontStyle: 'italic',
    },
    statusRow: {
      alignItems: 'flex-start',
      paddingTop: 1,
    },
    metadataRow: {
      minWidth: 0,
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      paddingTop: 3,
    },
    tileMetadataRow: {
      marginTop: 'auto',
    },
    metadataConnectionField: {
      minWidth: 0,
      flex: 1,
    },
    metadataConnection: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    metadataTimeField: {
      flexShrink: 0,
    },
    metadataTime: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    tileActions: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'flex-end',
      gap: 4,
      flexShrink: 0,
    },
    timelineRow: {
      minWidth: 0,
      minHeight: 104,
      flexDirection: 'row',
      backgroundColor: theme.surface,
    },
    timelineRail: {
      width: 24,
      flexShrink: 0,
      alignItems: 'center',
    },
    timelineDot: {
      width: 8,
      height: 8,
      marginTop: 7,
      borderRadius: 4,
      backgroundColor: theme.textMuted,
    },
    timelineLine: {
      width: 2,
      flex: 1,
      marginVertical: 4,
      backgroundColor: theme.divider,
    },
    timelineActions: {
      flexDirection: 'row',
      alignSelf: 'flex-start',
      alignItems: 'center',
      gap: 2,
      flexShrink: 0,
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
