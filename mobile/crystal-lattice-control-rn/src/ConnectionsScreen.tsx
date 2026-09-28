import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type {
  ConnectionRecord,
  Transport,
} from '@crystal-lattice/frontend-sdk';
import {
  ActionsMenuBar,
  type ActionDefinition,
} from '@crystal-lattice/frontend-rn-components';
import { getConnectionAdditionalInfo } from './connectionInfo';
import { useTheme, type Theme } from './theme';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import PanelModalFrame from './components/PanelModalFrame';

interface ConnectionsScreenProps {
  connections: ConnectionRecord[];
  loading?: boolean;
  activeConnectionId: string | null;
  transport: Transport | null;
  onConnectionCardPress: (record: ConnectionRecord) => void;
  onOpenConnection: (record: ConnectionRecord) => void | Promise<void>;
  onNewConnection: () => void;
  onOpenGlobalSettings: () => void;
  onOpenServerSettings: () => void;
  onDisconnect: () => void;
  onDeleteConnection: (record: ConnectionRecord) => void;
}

const HEADER_ACTIONS: ActionDefinition[] = [
  {
    key: 'globalSettings',
    label: 'Settings',
    iconName: 'settings',
    testID: 'connections-global-settings',
  },
  {
    key: 'newConnection',
    label: 'New connection',
    iconName: 'plus',
    testID: 'connections-new-connection',
  },
];
const CARD_ACTIONS: ActionDefinition[] = [
  { key: 'delete', label: 'Delete', iconName: 'trash-2' },
  {
    key: 'healthCheck',
    label: 'Health check',
    iconName: 'activity',
    testID: 'connection-health-check',
  },
  { key: 'open', label: 'Open', iconName: 'log-in', testID: 'connection-open' },
  {
    key: 'disconnect',
    label: 'Disconnect',
    iconName: 'log-out',
    testID: 'connection-disconnect',
  },
  {
    key: 'serverSettings',
    label: 'Settings',
    iconName: 'settings',
    testID: 'connection-server-settings',
  },
];

const ConnectionsScreen: React.FC<ConnectionsScreenProps> = ({
  connections,
  loading = false,
  activeConnectionId,
  transport,
  onConnectionCardPress,
  onOpenConnection,
  onNewConnection,
  onOpenGlobalSettings,
  onOpenServerSettings,
  onDisconnect,
  onDeleteConnection,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sorted = [...connections].sort((a, b) => b.lastUsedAt - a.lastUsedAt);
  const { pinned: headerPinned, setPinned: setHeaderPinned } =
    usePersistentPinnedActions<string>(
      'clc_pinned_connections_header_actions_v1',
      ['globalSettings', 'newConnection'],
    );
  const { pinned: cardPinned, setPinned: setCardPinned } =
    usePersistentPinnedActions<string>(
      'clc_pinned_connection_card_actions_v1',
      ['open', 'disconnect', 'healthCheck', 'serverSettings'],
    );
  const [busyConnectionId, setBusyConnectionId] = useState<string | null>(null);
  const [healthResult, setHealthResult] = useState<{
    title: string;
    body: string;
    error: boolean;
  } | null>(null);

  const methodLabel = (kind: ConnectionRecord['kind']) => {
    if (kind === 'embedded') return 'On device';
    if (kind === 'manual') return 'Manual';
    if (kind === 'discovery') return 'Discovery';
    if (kind === 'cloud') return 'Cloud';
    return 'Bridge';
  };

  const confirmDelete = (record: ConnectionRecord) => {
    Alert.alert(
      'Delete Connection',
      'Remove this saved connection from the list? This does not delete any data on the server.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => onDeleteConnection(record),
        },
      ],
    );
  };

  const runHealthCheck = async (record: ConnectionRecord) => {
    if (!transport || record.id !== activeConnectionId) return;
    setBusyConnectionId(record.id);
    try {
      const response = await transport.request({ method: 'GET', path: '/api/hello' });
      const body =
        typeof response.data === 'object'
          ? JSON.stringify(response.data, null, 2)
          : String(response.data);
      setHealthResult({ title: 'Health Check', body: `OK: ${body}`, error: false });
    } catch (error: any) {
      setHealthResult({
        title: 'Health Check',
        body: error?.message || 'Health check failed',
        error: true,
      });
    } finally {
      setBusyConnectionId(null);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text
          style={styles.title}
          testID="connections-screen-title"
        >
          Connections
        </Text>
        <ActionsMenuBar
          title="Connections actions"
          baseActions={HEADER_ACTIONS}
          pinned={headerPinned}
          onChangePinned={setHeaderPinned}
          menuButtonTestID="connections-actions-menu"
          renderIcon={({ name, size, color }) => (
            <Icon name={name} size={size} color={color} />
          )}
          renderPinIcon={({ size, color }) => (
            <Icon name="star" size={size} color={color} />
          )}
          renderCloseIcon={({ size, color, renderIcon }) =>
            renderIcon ? renderIcon({ name: 'x', size, color }) : null
          }
          onAction={(key) => {
            if (key === 'globalSettings') onOpenGlobalSettings();
            if (key === 'newConnection') onNewConnection();
          }}
        />
      </View>

      {loading ? (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={theme.primary} />
          <Text style={styles.loadingText}>Loading saved connections...</Text>
        </View>
      ) : null}

      {sorted.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No saved connections yet</Text>
          <Text style={styles.emptySubtitle}>
            Create a new connection to your server and it will appear here for quick access.
          </Text>
        </View>
      ) : (
        <ScrollView style={styles.list}>
          {sorted.map((record) => {
            const isOpen = record.id === activeConnectionId && transport !== null;
            const busy = busyConnectionId === record.id;
            const availableActions = isOpen
              ? ['delete', 'healthCheck', 'disconnect', 'serverSettings']
              : ['delete', 'open'];
            return (
              <TouchableOpacity
                key={record.id}
                testID={`connection-card-${record.id}`}
                style={styles.item}
                onPress={() => onConnectionCardPress(record)}
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
                <Text style={styles.itemSubLabel} numberOfLines={1}>
                  {getConnectionAdditionalInfo(record)}
                </Text>
                <View style={styles.cardFooter}>
                  <Text
                    testID={`connection-status-${record.id}`}
                    style={[styles.status, { color: isOpen ? theme.success : theme.textSecondary }]}
                  >
                    {isOpen ? 'Open' : 'Closed'}
                  </Text>
                  <ActionsMenuBar
                    title={`${record.name} actions`}
                    baseActions={CARD_ACTIONS}
                    availableActions={availableActions}
                    pinned={cardPinned}
                    onChangePinned={setCardPinned}
                    menuButtonTestID={`connection-actions-menu-${record.id}`}
                    renderIcon={({ name, size, color }) => (
                      <Icon name={name} size={size} color={color} />
                    )}
                    renderPinIcon={({ size, color }) => (
                      <Icon name="star" size={size} color={color} />
                    )}
                    renderCloseIcon={({ size, color, renderIcon }) =>
                      renderIcon ? renderIcon({ name: 'x', size, color }) : null
                    }
                    isActionDisabled={() => busy}
                    onAction={(key) => {
                      if (key === 'delete') confirmDelete(record);
                      if (key === 'open') void onOpenConnection(record);
                      if (key === 'disconnect') onDisconnect();
                      if (key === 'serverSettings') onOpenServerSettings();
                      if (key === 'healthCheck') void runHealthCheck(record);
                    }}
                  />
                </View>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      )}

      <PanelModalFrame
        visible={healthResult !== null}
        title={healthResult?.title ?? 'Health Check'}
        onRequestClose={() => setHealthResult(null)}
        statusTone={healthResult?.error ? 'error' : 'success'}
        contentStyle={styles.healthModal}
        testID="health-check-modal"
      >
        <Text testID="health-check-result" style={styles.healthText}>
          {healthResult?.body ?? ''}
        </Text>
      </PanelModalFrame>
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 12,
    },
    title: {
      marginLeft: 13,
      fontSize: 16,
      fontWeight: '700',
      color: theme.text,
    },
    loadingRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
    loadingText: {
      marginLeft: 8,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
    },
    list: { flex: 1 },
    item: {
      padding: 12,
      backgroundColor: theme.surface,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    itemHeaderRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 4,
    },
    itemTitle: {
      flex: 1,
      fontSize: 16,
      fontWeight: '600',
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
      fontWeight: '600',
      color: theme.text,
    },
    itemSubLabel: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      marginTop: 2,
    },
    cardFooter: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginTop: 8,
      minHeight: 32,
    },
    status: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '600',
    },
    emptyContainer: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 16,
    },
    emptyTitle: { fontSize: 18, fontWeight: '600', marginBottom: 8, color: theme.text },
    emptySubtitle: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
      textAlign: 'center',
    },
    healthModal: { width: '88%', maxWidth: 440 },
    healthText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontFamily: 'Courier',
    },
  });

export { createStyles as createConnectionsScreenStyles };
export default ConnectionsScreen;