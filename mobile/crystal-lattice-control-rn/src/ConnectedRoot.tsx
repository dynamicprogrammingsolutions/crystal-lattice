import React, { useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type {
  ConnectionAdapter,
  ConnectionRecord,
  SessionsCache,
  MessagesCache,
} from '../App';
import ConnectionScreen from './ConnectionScreen';
import ConnectionsScreen from './ConnectionsScreen';
import SessionsScreen from './SessionsScreen';
import type { SessionSummary, IndexedMessage } from './api';
import SessionChatScreen from './SessionChatScreen';

interface ConnectedRootProps {
  adapter: ConnectionAdapter | null;
  onDisconnect: () => void;
  connections: ConnectionRecord[];
  connectionsLoading: boolean;
  onSelectConnectionRecord: (record: ConnectionRecord) => void;
  onNewConnectionRequested: () => void;
  renderConnectionWizard: () => React.ReactNode;
  onDeleteConnectionRecord: (record: ConnectionRecord) => void;
  activeConnectionId: string | null;
  activeConnectionAdditionalInfo: string | null;
  sessionsCache: SessionsCache;
  onUpdateSessionsCache: (connectionId: string, sessions: SessionSummary[]) => void;
  messagesCache: MessagesCache;
  onUpdateMessagesCache: (
    connectionId: string,
    sessionId: string,
    messages: IndexedMessage[],
  ) => void;
  onUpdateMessagesUiState: (
    connectionId: string,
    sessionId: string,
    composeText: string,
    scrollOffset: number,
  ) => void;
}

const ConnectedRoot: React.FC<ConnectedRootProps> = ({
  adapter,
  onDisconnect,
  connections,
  connectionsLoading,
  onSelectConnectionRecord,
  onNewConnectionRequested,
  renderConnectionWizard,
  onDeleteConnectionRecord,
  activeConnectionId,
  activeConnectionAdditionalInfo,
  sessionsCache,
  onUpdateSessionsCache,
  messagesCache,
  onUpdateMessagesCache,
  onUpdateMessagesUiState,
}) => {
  const [tab, setTab] = useState<'connection' | 'sessions' | 'messages'>('connection');
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
          <View style={styles.connectionsTabContainer}>
            {(() => {
              const wizard = renderConnectionWizard();
              if (wizard) {
                return <View style={styles.wizardContainer}>{wizard}</View>;
              }

              return (
                <>
                  {adapter ? (
                    <ConnectionScreen
                      adapter={adapter}
                      onDisconnect={onDisconnect}
                      additionalInfo={activeConnectionAdditionalInfo}
                    />
                  ) : (
                    <View style={styles.placeholderContainer}>
                      <Text style={styles.placeholderText}>
                        No active connection. Select a saved connection below or create a new one.
                      </Text>
                    </View>
                  )}

                  <View style={styles.connectionsListSection}>
                    <ConnectionsScreen
                      connections={connections}
                      loading={connectionsLoading}
                      onSelectConnection={async (record) => {
                        await onSelectConnectionRecord(record);
                        setTab('sessions');
                      }}
                      onNewConnection={onNewConnectionRequested}
                      onDeleteConnection={onDeleteConnectionRecord}
                    />
                  </View>
                </>
              );
            })()}
          </View>
        )}
        {tab === 'sessions' && (
          (() => {
            const connectionId = activeConnectionId;
            const cacheEntry = connectionId
              ? sessionsCache[connectionId] ?? null
              : null;

            if (!adapter && !cacheEntry) {
              return (
                <View style={styles.placeholderContainer}>
                  <Text style={styles.placeholderText}>
                    No sessions loaded yet. Open the Connections tab to connect to a server.
                  </Text>
                </View>
              );
            }

            return (
              <SessionsScreen
                adapter={adapter}
                connectionId={connectionId}
                cachedSessions={cacheEntry?.sessions ?? null}
                lastLoadedAt={cacheEntry?.lastLoadedAt ?? null}
                onUpdateCache={(list: SessionSummary[]) => {
                  if (connectionId) {
                    onUpdateSessionsCache(connectionId, list);
                  }
                }}
                onSelectSession={handleSelectSession}
              />
            );
          })()
        )}
        {tab === 'messages' && (
          selectedSessionId ? (
            (() => {
              const connectionId = activeConnectionId;
              const bySession = connectionId
                ? messagesCache[connectionId] ?? {}
                : {};
              const cacheEntry =
                connectionId && selectedSessionId
                  ? bySession[selectedSessionId] ?? null
                  : null;

              if (!adapter && !cacheEntry) {
                return (
                  <View style={styles.placeholderContainer}>
                    <Text style={styles.placeholderText}>
                      No messages loaded yet. Connect to a server to load this session.
                    </Text>
                  </View>
                );
              }

              return (
                <SessionChatScreen
                  adapter={adapter}
                  connectionId={connectionId}
                  sessionId={selectedSessionId}
                  cachedMessages={cacheEntry?.messages ?? null}
                  lastLoadedAt={cacheEntry?.lastLoadedAt ?? null}
                  initialComposeText={cacheEntry?.composeText ?? ''}
                  initialScrollOffset={cacheEntry?.scrollOffset ?? 0}
                  onUpdateCache={(list: IndexedMessage[]) => {
                    if (connectionId) {
                      onUpdateMessagesCache(connectionId, selectedSessionId, list);
                    }
                  }}
                  onBack={() => {
                    setTab('sessions');
                  }}
                  onNavigateToSession={(sessionId) => {
                    setSelectedSessionId(sessionId);
                    setTab('messages');
                  }}
                  onUpdateUiState={(composeText, scrollOffset) => {
                    const connectionId = activeConnectionId;
                    if (connectionId) {
                      onUpdateMessagesUiState(
                        connectionId,
                        selectedSessionId,
                        composeText,
                        scrollOffset,
                      );
                    }
                  }}
                />
              );
            })()
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
          <Text style={tab === 'connection' ? styles.navTextActive : styles.navText}>Connections</Text>
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
  connectionsTabContainer: {
    flex: 1,
  },
  wizardContainer: {
    flex: 1,
    paddingHorizontal: 0,
  },
  connectionsListSection: {
    flex: 1,
    marginTop: 16,
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
