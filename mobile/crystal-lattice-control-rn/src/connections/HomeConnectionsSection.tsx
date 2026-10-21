import React, { useMemo, useState } from "react";
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Icon from "react-native-vector-icons/Feather";
import type { ConnectionRecord } from "@crystal-lattice/frontend-sdk";
import {
  ActionsMenuBar,
  type ActionDefinition,
} from "@crystal-lattice/frontend-rn-components";
import PanelModalFrame from "../components/PanelModalFrame";
import { useTheme, type Theme } from "../theme";
import ConnectionCard, { createConnectionCardStyles } from "./ConnectionCard";
import {
  useConnectionActions,
  type ConnectionActionsProps,
} from "./useConnectionActions";

interface HomeConnectionsSectionProps extends ConnectionActionsProps {
  connections: readonly ConnectionRecord[];
  loading?: boolean;
  onConnectionCardPress: (record: ConnectionRecord) => void;
  onNewConnection: () => void;
  onCollapse?: () => void;
}

const HEADER_ACTIONS: ActionDefinition[] = [
  {
    key: "newConnection",
    label: "New connection",
    iconName: "plus",
    testID: "connections-new-connection",
  },
];

export default function HomeConnectionsSection(
  props: HomeConnectionsSectionProps
) {
  const theme = useTheme();
  const styles = useMemo(
    () => createHomeConnectionsSectionStyles(theme),
    [theme]
  );
  const [expanded, setExpanded] = useState(false);
  const sorted = [...props.connections].sort(
    (a, b) => b.lastUsedAt - a.lastUsedAt
  );
  const visible = expanded ? sorted : sorted.slice(0, 3);
  const actions = useConnectionActions(props);
  const toggleLabel = expanded
    ? "Show fewer"
    : `Show all ${sorted.length} connections`;
  return (
    <View style={styles.container} testID="home-connections-section">
      <View style={styles.headerRow}>
        <Text style={styles.title} testID="connections-screen-title">
          Connections
        </Text>
        <ActionsMenuBar
          title="Connections actions"
          baseActions={HEADER_ACTIONS}
          pinned={["newConnection"]}
          onChangePinned={() => {}}
          showMenuButton={false}
          menuButtonTestID="connections-actions-menu"
          renderIcon={({ name, size, color }) => (
            <Icon name={name} size={size} color={color} />
          )}
          renderPinIcon={({ size, color }) => (
            <Icon name="star" size={size} color={color} />
          )}
          renderCloseIcon={({ size, color, renderIcon }) =>
            renderIcon ? renderIcon({ name: "x", size, color }) : null
          }
          onAction={(key) => {
            if (key === "newConnection") props.onNewConnection();
          }}
        />
      </View>
      {props.loading ? (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={theme.primary} />
          <Text style={styles.loadingText}>Loading saved connections...</Text>
        </View>
      ) : null}
      {sorted.length === 0 && !props.loading ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No saved connections yet</Text>
          <Text style={styles.emptySubtitle}>
            Create a new connection to your server and it will appear here for
            quick access.
          </Text>
        </View>
      ) : null}
      {visible.map((record) => (
        <ConnectionCard
          key={record.id}
          record={record}
          isOpen={
            record.id === props.activeConnectionId && props.transport !== null
          }
          busy={actions.busyConnectionId === record.id}
          pinned={actions.pinned}
          onChangePinned={actions.setPinned}
          onPress={() => props.onConnectionCardPress(record)}
          onAction={(key) => actions.execute(record, key)}
        />
      ))}
      {sorted.length > 3 ? (
        <TouchableOpacity
          testID="home-connections-toggle"
          accessibilityRole="button"
          accessibilityLabel={toggleLabel}
          accessibilityState={{ expanded }}
          style={styles.toggle}
          onPress={() => {
            setExpanded(!expanded);
            if (expanded) props.onCollapse?.();
          }}
        >
          <Text style={styles.toggleText}>{toggleLabel}</Text>
          <Icon
            name={expanded ? "chevron-up" : "chevron-down"}
            size={18}
            color={theme.primary}
          />
        </TouchableOpacity>
      ) : null}
      <PanelModalFrame
        visible={actions.healthResult !== null}
        title={actions.healthResult?.title ?? "Health Check"}
        onRequestClose={() => actions.setHealthResult(null)}
        statusTone={actions.healthResult?.error ? "error" : "success"}
        testID="health-check-modal"
      >
        <Text testID="health-check-result" style={styles.healthText}>
          {actions.healthResult?.body ?? ""}
        </Text>
      </PanelModalFrame>
    </View>
  );
}

export const createHomeConnectionsSectionStyles = (theme: Theme) =>
  StyleSheet.create({
    ...createConnectionCardStyles(theme),
    container: { marginBottom: 16 },
    headerRow: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 12,
    },
    title: {
      marginLeft: 13,
      fontSize: 20,
      fontWeight: "600",
      color: theme.text,
    },
    loadingRow: {
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
      marginBottom: 12,
    },
    loadingText: { color: theme.textSecondary },
    emptyContainer: { padding: 16 },
    emptyTitle: { color: theme.text, fontWeight: "600", marginBottom: 8 },
    emptySubtitle: { color: theme.textSecondary },
    toggle: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 8,
      paddingVertical: 12,
    },
    toggleText: {
      color: theme.primary,
      fontSize: theme.typography.fontSize.normal,
    },
    healthText: { color: theme.text, padding: 16 },
  });
