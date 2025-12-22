import React, { useMemo } from 'react';
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
import type { ConnectionRecord } from '../App';
import { getConnectionAdditionalInfo } from './connectionInfo';
import { useTheme, type Theme } from './theme';

interface ConnectionsScreenProps {
  connections: ConnectionRecord[];
  loading?: boolean;
  onSelectConnection: (record: ConnectionRecord) => void;
  onNewConnection: () => void;
  onDeleteConnection: (record: ConnectionRecord) => void;
}

const ConnectionsScreen: React.FC<ConnectionsScreenProps> = ({
  connections,
  loading = false,
  onSelectConnection,
  onNewConnection,
  onDeleteConnection,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sorted = [...connections].sort((a, b) => b.lastUsedAt - a.lastUsedAt);

  const renderMethodLabel = (kind: ConnectionRecord['kind']) => {
    if (kind === 'manual') return 'Manual';
    if (kind === 'discovery') return 'Discovery';
    return 'Bridge';
  };

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyTitle}>No saved connections yet</Text>
      <Text style={styles.emptySubtitle}>
        Create a new connection to your server and it will appear here for
        quick access.
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Connections</Text>
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={onNewConnection}
        >
          <Icon
            name="plus"
            size={16}
            color="#FFFFFF"
            style={styles.buttonIcon}
          />
          <Text style={styles.buttonText}>New Connection</Text>
        </TouchableOpacity>
      </View>

      {loading && (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={theme.primary} />
          <Text style={styles.loadingText}>Loading saved connections...</Text>
        </View>
      )}

      {sorted.length === 0 ? (
        renderEmptyState()
      ) : (
        <ScrollView style={styles.list}>
          {sorted.map((record) => {
            const lastUsedLabel = new Date(
              record.lastUsedAt,
            ).toLocaleString();
            const additionalInfo = getConnectionAdditionalInfo(record);

            return (
              <View key={record.id} style={styles.item}>
                <TouchableOpacity
                  style={styles.itemContent}
                  onPress={() => onSelectConnection(record)}
                >
                  <View style={styles.itemHeaderRow}>
                    <Text style={styles.itemTitle} numberOfLines={1}>
                      {record.name}
                    </Text>
                    <View style={styles.methodBadge}>
                      <Text style={styles.methodBadgeText}>
                        {renderMethodLabel(record.kind)}
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.itemSubLabel} numberOfLines={1}>
                    {additionalInfo}
                  </Text>
                  <Text style={styles.itemMeta} numberOfLines={1}>
                    Last used: {lastUsedLabel}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => {
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
                  }}
                  accessibilityLabel={`Delete connection ${record.name}`}
                >
                  <Icon name="trash-2" size={18} color={theme.danger} />
                </TouchableOpacity>
              </View>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    container: {
      flex: 1,
      padding: 16,
      backgroundColor: theme.background,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 16,
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.text,
    },
    button: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 8,
      backgroundColor: theme.primary,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    buttonIcon: {
      marginRight: 6,
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: 14,
      fontWeight: '600',
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    loadingText: {
      marginLeft: 8,
      fontSize: 14,
      color: theme.textSecondary,
    },
    list: {
      flex: 1,
    },
    item: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      backgroundColor: theme.surface,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    itemContent: {
      flex: 1,
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
      fontSize: 11,
      fontWeight: '600',
      color: theme.text,
    },
    itemMeta: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    itemSubLabel: {
      fontSize: 12,
      color: theme.textSecondary,
      marginTop: 2,
    },
    deleteButton: {
      paddingLeft: 8,
      paddingVertical: 4,
    },
    emptyContainer: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 16,
    },
    emptyTitle: {
      fontSize: 18,
      fontWeight: '600',
      marginBottom: 8,
      color: theme.text,
    },
    emptySubtitle: {
      fontSize: 14,
      color: theme.textSecondary,
      textAlign: 'center',
    },
  });

export default ConnectionsScreen;
