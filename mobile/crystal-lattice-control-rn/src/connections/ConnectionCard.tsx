import React, { useMemo } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import Icon from "react-native-vector-icons/Feather";
import type { ConnectionRecord } from "@crystal-lattice/frontend-sdk";
import {
  ActionsMenuBar,
  type ActionDefinition,
} from "@crystal-lattice/frontend-rn-components";
import { getConnectionAdditionalInfo } from "../connectionInfo";
import { useTheme, type Theme } from "../theme";

const CARD_ACTIONS: ActionDefinition[] = [
  { key: "delete", label: "Delete", iconName: "trash-2" },
  {
    key: "healthCheck",
    label: "Health check",
    iconName: "activity",
    testID: "connection-health-check",
  },
  { key: "open", label: "Open", iconName: "log-in", testID: "connection-open" },
  {
    key: "disconnect",
    label: "Disconnect",
    iconName: "log-out",
    testID: "connection-disconnect",
  },
  {
    key: "serverSettings",
    label: "Settings",
    iconName: "settings",
    testID: "connection-server-settings",
  },
];

interface ConnectionCardProps {
  record: ConnectionRecord;
  isOpen: boolean;
  busy: boolean;
  pinned: readonly string[];
  onChangePinned: (keys: string[]) => void;
  onPress: () => void;
  onAction: (key: string) => void;
}

function methodLabel(kind: ConnectionRecord["kind"]): string {
  if (kind === "embedded") return "On device";
  if (kind === "manual") return "Manual";
  if (kind === "discovery") return "Discovery";
  if (kind === "cloud") return "Cloud";
  return "Bridge";
}

export default function ConnectionCard({
  record,
  isOpen,
  busy,
  pinned,
  onChangePinned,
  onPress,
  onAction,
}: ConnectionCardProps) {
  const theme = useTheme();
  const styles = useMemo(() => createConnectionCardStyles(theme), [theme]);
  return (
    <TouchableOpacity
      testID={`connection-card-${record.id}`}
      style={styles.item}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.itemHeaderRow}>
        <Text
          style={styles.itemTitle}
          numberOfLines={1}
          testID={`connection-title-${record.id}`}
        >
          {record.name}
        </Text>
        <View style={styles.methodBadge}>
          <Text style={styles.methodBadgeText}>{methodLabel(record.kind)}</Text>
        </View>
      </View>
      <Text
        testID={`connection-info-${record.id}`}
        style={styles.itemSubLabel}
        numberOfLines={1}
      >
        {getConnectionAdditionalInfo(record)}
      </Text>
      <View style={styles.cardFooter}>
        <Text
          testID={`connection-status-${record.id}`}
          style={[
            styles.status,
            { color: isOpen ? theme.success : theme.textSecondary },
          ]}
        >
          {isOpen ? "Open" : "Closed"}
        </Text>
        <View style={styles.cardActions}>
          <TouchableOpacity
            testID={`connection-new-session-${record.id}`}
            accessibilityRole="button"
            accessibilityLabel={`New session on ${record.name}`}
            accessibilityActions={[{ name: "activate", label: "New session" }]}
            onAccessibilityAction={(event) => {
              if (event.nativeEvent.actionName === "activate")
                onAction("newSession");
            }}
            style={styles.newSessionButton}
            disabled={busy}
            onPress={() => onAction("newSession")}
          >
            <Icon name="plus" size={18} color={theme.primary} />
          </TouchableOpacity>
          <ActionsMenuBar
            title={`${record.name} actions`}
            baseActions={CARD_ACTIONS}
            availableActions={
              isOpen
                ? ["delete", "healthCheck", "disconnect", "serverSettings"]
                : ["delete", "open"]
            }
            pinned={pinned}
            onChangePinned={onChangePinned}
            menuButtonTestID={`connection-actions-menu-${record.id}`}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            renderPinIcon={({ size, color }) => (
              <Icon name="star" size={size} color={color} />
            )}
            renderCloseIcon={({ size, color, renderIcon }) =>
              renderIcon ? renderIcon({ name: "x", size, color }) : null
            }
            isActionDisabled={() => busy}
            onAction={onAction}
          />
        </View>
      </View>
    </TouchableOpacity>
  );
}

export const createConnectionCardStyles = (theme: Theme) =>
  StyleSheet.create({
    item: {
      padding: 12,
      backgroundColor: theme.surface,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    itemHeaderRow: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 4,
    },
    itemTitle: {
      flex: 1,
      fontSize: 16,
      fontWeight: "600",
      marginRight: 8,
      color: theme.text,
    },
    methodBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 12,
      backgroundColor: theme.surfaceAlt,
    },
    methodBadgeText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      fontWeight: "600",
      color: theme.text,
    },
    itemSubLabel: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      marginTop: 2,
    },
    cardFooter: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      marginTop: 8,
      minHeight: 32,
    },
    cardActions: {
      flexDirection: "row",
      alignItems: "center",
      flexShrink: 1,
    },
    newSessionButton: {
      width: 44,
      height: 40,
      alignItems: "center",
      justifyContent: "center",
    },
    status: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: "600",
    },
  });
