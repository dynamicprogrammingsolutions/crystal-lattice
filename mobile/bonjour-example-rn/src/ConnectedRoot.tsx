import React, { useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import type { ConnectionAdapter } from '../App';
import SessionsScreen from './SessionsScreen';
import SessionChatScreen from './SessionChatScreen';

interface ConnectedRootProps {
  adapter: ConnectionAdapter;
  onDisconnect: () => void;
}

type ConnectedTab = 'sessions' | 'demo';

const ConnectedRoot: React.FC<ConnectedRootProps> = ({ adapter, onDisconnect }) => {
  const [tab, setTab] = useState<ConnectedTab>('sessions');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoResponse, setDemoResponse] = useState('');

  const executeDemoRequest = async (type: 'GET' | 'PUT') => {
    setDemoLoading(true);
    setDemoResponse('');

    try {
      let data;
      if (type === 'GET') {
        data = await adapter.get('/api/data');
      } else {
        data = await adapter.put('/api/data', {
          message: 'Hello from React Native',
          timestamp: new Date().toISOString(),
        });
      }
      setDemoResponse(JSON.stringify(data, null, 2));
    } catch (err: any) {
      const message = err?.message || 'Demo request failed';
      setDemoResponse(`Error: ${message}`);
    } finally {
      setDemoLoading(false);
    }
  };

  const renderSessionsArea = () => {
    if (selectedSessionId == null) {
      return (
        <SessionsScreen
          adapter={adapter}
          onSelectSession={setSelectedSessionId}
        />
      );
    }

    return (
      <SessionChatScreen
        adapter={adapter}
        sessionId={selectedSessionId}
        onBack={() => setSelectedSessionId(null)}
      />
    );
  };

  const renderDemoArea = () => (
    <View style={styles.demoContainer}>
      <Text style={styles.sectionTitle}>Demo /api/data</Text>

      <View style={styles.demoButtonsRow}>
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={() => executeDemoRequest('GET')}
          disabled={demoLoading}
        >
          <Text style={styles.buttonText}>GET /api/data</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={() => executeDemoRequest('PUT')}
          disabled={demoLoading}
        >
          <Text style={styles.buttonTextSecondary}>PUT /api/data</Text>
        </TouchableOpacity>
      </View>

      {demoLoading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.loadingText}>Running demo request...</Text>
        </View>
      )}

      {demoResponse !== '' && (
        <ScrollView style={styles.demoResponseContainer}>
          <Text style={styles.demoResponseText}>{demoResponse}</Text>
        </ScrollView>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Connected</Text>

      <View style={[styles.statusContainer, styles.statusConnected]}>
        <View style={[styles.statusDot, styles.statusConnectedDot]} />
        <Text style={styles.statusText}>{adapter.getDisplayName()}</Text>
      </View>

      <View style={styles.tabRow}>
        <TouchableOpacity
          style={[styles.tabButton, tab === 'sessions' && styles.tabButtonActive]}
          onPress={() => setTab('sessions')}
        >
          <Text style={tab === 'sessions' ? styles.tabButtonTextActive : styles.tabButtonText}>
            Chat Sessions
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, tab === 'demo' && styles.tabButtonActive]}
          onPress={() => setTab('demo')}
        >
          <Text style={tab === 'demo' ? styles.tabButtonTextActive : styles.tabButtonText}>
            Demo /api/data
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.contentArea}>
        {tab === 'sessions' ? renderSessionsArea() : renderDemoArea()}
      </View>

      <TouchableOpacity
        style={[styles.disconnectButton, styles.secondaryButton]}
        onPress={onDisconnect}
      >
        <Text style={styles.buttonTextSecondary}>Disconnect</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
    borderRadius: 8,
    marginBottom: 16,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusConnectedDot: {
    backgroundColor: '#34C759',
  },
  statusConnected: {
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
  },
  tabRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 10,
    marginHorizontal: 4,
    borderRadius: 8,
    backgroundColor: '#E5E5EA',
    alignItems: 'center',
  },
  tabButtonActive: {
    backgroundColor: '#007AFF',
  },
  tabButtonText: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
  },
  tabButtonTextActive: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  contentArea: {
    flex: 1,
  },
  disconnectButton: {
    marginTop: 12,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  secondaryButton: {
    backgroundColor: '#E5E5EA',
  },
  buttonTextSecondary: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
  },
  button: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  demoContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  demoButtonsRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#8E8E93',
  },
  demoResponseContainer: {
    marginTop: 8,
    backgroundColor: 'rgba(128, 128, 128, 0.1)',
    borderRadius: 8,
    padding: 10,
    maxHeight: 220,
  },
  demoResponseText: {
    fontSize: 12,
    fontFamily: 'Courier',
  },
});

export default ConnectedRoot;
