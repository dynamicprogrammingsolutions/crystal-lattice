import AsyncStorage from '@react-native-async-storage/async-storage';
import * as React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import {
  CONNECTIONS_STORAGE_KEY,
  loadConnections,
  type ConnectionRecord,
  type KeyValueStore,
  saveConnections,
} from '@crystal-lattice/frontend-sdk';

function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    const v = c === 'x' ? r : (r % 4) + 8;
    return v.toString(16);
  });
}

const connectionsStore: KeyValueStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};

export default function App() {
  const [connections, setConnections] = React.useState<ConnectionRecord[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const loadSavedConnections = async () => {
      setLoading(true);
      setError(null);
      try {
        const records = await loadConnections(connectionsStore);
        setConnections(records);
      } catch (err: any) {
        setError(err?.message || 'Failed to load saved connections');
      } finally {
        setLoading(false);
      }
    };

    loadSavedConnections();
  }, []);

  React.useEffect(() => {
    const save = async () => {
      try {
        await saveConnections(connectionsStore, connections);
      } catch {}
    };

    save();
  }, [connections]);

  const handleAddDemoConnection = () => {
    const now = Date.now();
    const record: ConnectionRecord = {
      id: generateId(),
      kind: 'manual',
      name: `Local (${connections.length + 1})`,
      lastUsedAt: now,
      host: '127.0.0.1',
      port: 8080,
    };

    setConnections((prev) => [record, ...prev]);
  };

  const handleClearConnections = () => {
    setError(null);
    setConnections([]);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Crystal Lattice Control (Desktop)</Text>
      <Text style={styles.subtitle}>Connections persistence smoke test</Text>

      <View style={styles.row}>
        <Pressable
          style={[styles.button, styles.primaryButton]}
          onPress={handleAddDemoConnection}
        >
          <Text style={styles.primaryButtonText}>Add demo manual connection</Text>
        </Pressable>
        <Pressable style={[styles.button, styles.dangerButton]} onPress={handleClearConnections}>
          <Text style={styles.dangerButtonText}>Clear</Text>
        </Pressable>
      </View>

      <Text style={styles.meta}>
        {loading
          ? 'Loading…'
          : `Saved connections: ${connections.length} (key: ${CONNECTIONS_STORAGE_KEY})`}
      </Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
        {connections.map((record) => (
          <View key={record.id} style={styles.item}>
            <Text style={styles.itemTitle} numberOfLines={1}>
              {record.name}
            </Text>
            <Text style={styles.itemSubtle} numberOfLines={1}>
              {record.kind} • {record.id}
            </Text>
            {record.kind === 'manual' ? (
              <Text style={styles.itemSubtle} numberOfLines={1}>
                {record.host}:{record.port}
              </Text>
            ) : null}
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    gap: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: '600',
  },
  subtitle: {
    fontSize: 14,
    opacity: 0.7,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  button: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
  },
  primaryButton: {
    backgroundColor: '#0A84FF',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  dangerButton: {
    backgroundColor: '#FF3B30',
  },
  dangerButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  meta: {
    fontSize: 12,
    opacity: 0.7,
  },
  error: {
    fontSize: 12,
    color: '#FF3B30',
  },
  list: {
    flex: 1,
  },
  listContent: {
    gap: 8,
    paddingBottom: 24,
  },
  item: {
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.12)',
    borderRadius: 10,
    padding: 12,
    gap: 4,
  },
  itemTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  itemSubtle: {
    fontSize: 12,
    opacity: 0.7,
  },
});
