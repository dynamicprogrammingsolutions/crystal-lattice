import React, { useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { ConnectionAdapter } from '../App';
import ConnectionScreen from './ConnectionScreen';
import SessionsScreen from './SessionsScreen';
import SessionChatScreen from './SessionChatScreen';

interface ConnectedRootProps {
  adapter: ConnectionAdapter;
  onDisconnect: () => void;
}

const ConnectedRoot: React.FC<ConnectedRootProps> = ({ adapter, onDisconnect }) => {
  const [tab, setTab] = useState<'connection' | 'sessions' | 'messages'>('sessions');
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

  const handleSelectSession = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setTab('messages');
  };

  return (
    <View style={styles.container}>
      <View style={styles.contentArea}>
        {tab === 'connection' && (
          <ConnectionScreen adapter={adapter} onDisconnect={onDisconnect} />
        )}
        {tab === 'sessions' && (
          <SessionsScreen
            adapter={adapter}
            onSelectSession={handleSelectSession}
          />
        )}
        {tab === 'messages' && (
          selectedSessionId ? (
            <SessionChatScreen
              adapter={adapter}
              sessionId={selectedSessionId}
              onBack={() => {
                setTab('sessions');
              }}
              onNavigateToSession={(sessionId) => {
                setSelectedSessionId(sessionId);
                setTab('messages');
              }}
            />
          ) : (
            <View style={styles.placeholderContainer}>
              <Text style={styles.placeholderText}>Select a session from the Sessions tab.</Text>
            </View>
          )
        )}
      </View>

      <View style={styles.navBar}>
        <TouchableOpacity
          style={[styles.navItem, tab === 'connection' && styles.navItemActive]}
          onPress={() => setTab('connection')}
        >
          <Icon
            name="wifi"
            size={20}
            color={tab === 'connection' ? '#007AFF' : '#8E8E93'}
          />
          <Text style={tab === 'connection' ? styles.navTextActive : styles.navText}>Connection</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.navItem, tab === 'sessions' && styles.navItemActive]}
          onPress={() => setTab('sessions')}
        >
          <Icon
            name="list"
            size={20}
            color={tab === 'sessions' ? '#007AFF' : '#8E8E93'}
          />
          <Text style={tab === 'sessions' ? styles.navTextActive : styles.navText}>Sessions</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.navItem, tab === 'messages' && styles.navItemActive]}
          onPress={() => setTab('messages')}
        >
          <Icon
            name="message-circle"
            size={20}
            color={tab === 'messages' ? '#007AFF' : '#8E8E93'}
          />
          <Text style={tab === 'messages' ? styles.navTextActive : styles.navText}>Messages</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentArea: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
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
  navBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    paddingVertical: 6,
    backgroundColor: '#FFFFFF',
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
  },
  navItemActive: {
    borderTopWidth: 2,
    borderTopColor: '#007AFF',
  },
  navText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  navTextActive: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
  },
  placeholderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
});

export default ConnectedRoot;
