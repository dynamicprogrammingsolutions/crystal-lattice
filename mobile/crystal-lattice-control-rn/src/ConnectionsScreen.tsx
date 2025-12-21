import React from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { ConnectionRecord } from '../App';

interface ConnectionsScreenProps {
  connections: ConnectionRecord[];
  loading?: boolean;
  onSelectConnection: (record: ConnectionRecord) => void;
  onNewConnection: () => void;
}

const ConnectionsScreen: React.FC<ConnectionsScreenProps> = ({
  connections,
  loading = false,
  onSelectConnection,
  onNewConnection,
}) => {
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
          <ActivityIndicator size="small" color="#007AFF" />
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

            return (
              <TouchableOpacity
                key={record.id}
                style={styles.item}
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
                <Text style={styles.itemMeta} numberOfLines={1}>
                  Last used: {lastUsedLabel}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
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
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  buttonIcon: {
    marginRight: 6,
  },
  buttonText: {
    color: '#FFFFFF',
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
    color: '#8E8E93',
  },
  list: {
    flex: 1,
  },
  item: {
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
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
  },
  methodBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    backgroundColor: '#E5E5EA',
  },
  methodBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#000000',
  },
  itemMeta: {
    fontSize: 12,
    color: '#8E8E93',
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
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
});

export default ConnectionsScreen;
