import React, { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import type { ConnectionAdapter } from '../App';

interface ConnectionScreenProps {
  adapter: ConnectionAdapter;
  onDisconnect: () => void;
  additionalInfo?: string | null;
}

const ConnectionScreen: React.FC<ConnectionScreenProps> = ({
  adapter,
  onDisconnect,
  additionalInfo,
}) => {
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  const handleHealthCheck = async () => {
    setHealthLoading(true);
    setHealthStatus(null);
    try {
      const data = await adapter.get('/api/hello');
      const label = typeof data === 'object' ? JSON.stringify(data) : String(data);
      setHealthStatus(`OK: ${label}`);
    } catch (err: any) {
      const message = err?.message || 'Healthcheck failed';
      setHealthStatus(`Error: ${message}`);
    } finally {
      setHealthLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Connected to</Text>
      <Text style={styles.serverName}>{adapter.getDisplayName()}</Text>
      {additionalInfo ? (
        <Text style={styles.serverSubLabel}>{additionalInfo}</Text>
      ) : null}

      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={handleHealthCheck}
        disabled={healthLoading}
      >
        {healthLoading ? (
          <ActivityIndicator size="small" color="#FFFFFF" />
        ) : (
          <Text style={styles.buttonText}>Run Health Check</Text>
        )}
      </TouchableOpacity>

      {healthStatus && (
        <View style={styles.statusBox}>
          <Text style={styles.statusText}>{healthStatus}</Text>
        </View>
      )}

      <TouchableOpacity
        style={[styles.button, styles.secondaryButton]}
        onPress={onDisconnect}
      >
        <Text style={styles.secondaryButtonText}>Disconnect</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  label: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  serverName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 24,
  },
  serverSubLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 16,
  },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
    minWidth: 180,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#E5E5EA',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
  },
  statusBox: {
    marginTop: 16,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
  },
  statusText: {
    fontSize: 12,
    color: '#000000',
  },
});

export default ConnectionScreen;
