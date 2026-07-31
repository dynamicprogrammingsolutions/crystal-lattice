import React, { useState, useMemo } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import type { AgentBackend, ConnectionRecord, Transport } from '@crystal-lattice/frontend-sdk';
import type { SessionsCache } from '../App';
import type { DebugTimelineEntry } from './debugTimeline';
import type { MessagesCache } from './cache/types';
import ConnectionScreen from './ConnectionScreen';
import ConnectionsScreen from './ConnectionsScreen';
import SessionsScreen from './SessionsScreen';
import type { SessionSummary, IndexedMessage } from './api';
import SessionChatScreen from './SessionChatScreen';
import type { ChatScrollAnchor } from './chatScroll';
import { useTheme, type Theme } from './theme';
import { ApplicationPluginsProvider } from './ApplicationPluginsContext';
import { DEFAULT_MOBILE_TRANSCRIPT_RANGE } from './transcriptRange';
import GlobalDisplayLayer from './components/GlobalDisplayLayer';

interface ConnectedRootProps {
  backend: AgentBackend | null;
  transport: Transport | null;
  onDisconnect: () => void;
  connections: ConnectionRecord[];
  connectionsLoading: boolean;
  onSelectConnectionRecord: (record: ConnectionRecord) => void;
  onNewConnectionRequested: () => void;
  renderConnectionWizard: () => React.ReactNode;
  onDeleteConnectionRecord: (record: ConnectionRecord) => void;
  activeConnectionId: string | null;
  activeConnectionName: string | null;
  activeConnectionAdditionalInfo: string | null;
  sessionsCache: SessionsCache;
  onUpdateSessionsCache: (connectionId: string, sessions: SessionSummary[]) => void;
  messagesCache: MessagesCache;
  onUpdateMessagesCache: (
    connectionId: string,
    sessionId: string,
    messages: IndexedMessage[],
    eventsCursorId: string | null,
    activeRequestId: string | null,
  ) => void;
  onSaveMessagesComposeText: (
    connectionId: string,
    sessionId: string,
    composeText: string,
  ) => void;
  onSaveMessagesScrollAnchor: (
    connectionId: string,
    sessionId: string,
    scrollAnchor: ChatScrollAnchor,
  ) => void;
  onSaveMessagesHistoryRange: (
    connectionId: string,
    sessionId: string,
    rangeStartText: string,
    rangeEndText: string,
  ) => void;
  debugTimeline: DebugTimelineEntry[];
  onAppendDebugTimelineEntry: (
    entry: Omit<DebugTimelineEntry, 'id' | 'timestampMs'> & {
      detail?: string | null;
      meta?: Record<string, any> | null;
    },
  ) => void;
}

const ConnectedRoot: React.FC<ConnectedRootProps> = ({
  backend,
  transport,
  onDisconnect,
  connections,
  connectionsLoading,
  onSelectConnectionRecord,
  onNewConnectionRequested,
  renderConnectionWizard,
  onDeleteConnectionRecord,
  activeConnectionId,
  activeConnectionName,
  activeConnectionAdditionalInfo,
  sessionsCache,
  onUpdateSessionsCache,
  messagesCache,
  onUpdateMessagesCache,
  onSaveMessagesComposeText,
  onSaveMessagesScrollAnchor,
  onSaveMessagesHistoryRange,
  debugTimeline,
  onAppendDebugTimelineEntry,
}) => {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const styles = useMemo(() => createStyles(theme, insets), [theme, insets]);
  const [tab, setTab] = useState<'connection' | 'sessions' | 'messages'>('connection');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoResponse, setDemoResponse] = useState('');

  const executeDemoRequest = async (type: 'GET' | 'PUT') => {
    setDemoLoading(true);
    setDemoResponse('');

    try {
      if (!transport) {
        throw new Error('No active connection');
      }

      const payload =
        type === 'PUT'
          ? {
              message: 'Hello from React Native',
              timestamp: new Date().toISOString(),
            }
          : undefined;
      const resp = await transport.request({
        method: type,
        path: '/api/data',
        body: payload,
      });

      setDemoResponse(JSON.stringify(resp.data, null, 2));
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
      <ApplicationPluginsProvider backend={backend} connectionId={activeConnectionId}>
        <GlobalDisplayLayer
          backend={backend}
          connectionId={activeConnectionId}
        >
        <View style={styles.contentArea} testID="connected-root-content">
        {/* Connection tab content (kept mounted, visibility toggled) */}
        <View
          style={[
            styles.connectionsTabContainer,
            tab !== 'connection' && { display: 'none' },
          ]}
        >
          {(() => {
            const wizard = renderConnectionWizard();
            if (wizard) {
              return <View style={styles.wizardContainer}>{wizard}</View>;
            }

            return (
              <>
                {backend && transport ? (
                  <ConnectionScreen
                    transport={transport}
                    displayName={activeConnectionName || 'Connected'}
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

        {/* Sessions tab content (kept mounted, visibility toggled) */}
        <View
          style={[
            styles.connectionsTabContainer,
            tab !== 'sessions' && { display: 'none' },
          ]}
        >
          {(() => {
            const connectionId = activeConnectionId;
            const cacheEntry = connectionId
              ? sessionsCache[connectionId] ?? null
              : null;

            if (!backend && !cacheEntry) {
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
                backend={backend}
                connectionId={connectionId}
                cachedSessions={cacheEntry?.sessions ?? null}
                lastLoadedAt={cacheEntry?.lastLoadedAt ?? null}
                isActive={tab === 'sessions'}
                onUpdateCache={(list: SessionSummary[]) => {
                  if (connectionId) {
                    onUpdateSessionsCache(connectionId, list);
                  }
                }}
                onSelectSession={handleSelectSession}
              />
            );
          })()}
        </View>

        {/* Messages tab content (kept mounted, visibility toggled) */}
        <View
          style={[
            styles.connectionsTabContainer,
            tab !== 'messages' && { display: 'none' },
          ]}
        >
          {selectedSessionId ? (
            (() => {
              const connectionId = activeConnectionId;
              const bySession = connectionId
                ? messagesCache[connectionId] ?? {}
                : {};
              const cacheEntry =
                connectionId && selectedSessionId
                  ? bySession[selectedSessionId] ?? null
                  : null;

              const sessionsEntry = connectionId
                ? sessionsCache[connectionId] ?? null
                : null;
              const sessionSummary: SessionSummary | null = sessionsEntry?.sessions
                ? sessionsEntry.sessions.find((s) => s.session_id === selectedSessionId) ?? null
                : null;

              if (!backend && !cacheEntry) {
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
                  key={selectedSessionId}
                  backend={backend}
                  connectionId={connectionId}
                  isActive={tab === 'messages'}
                  sessionId={selectedSessionId}
                  sessionSummary={sessionSummary}
                  cachedMessages={cacheEntry?.messages ?? null}
                  lastLoadedAt={cacheEntry?.lastLoadedAt ?? null}
                  cachedEventsCursorId={
                    cacheEntry?.eventsCursorId ??
                    cacheEntry?.cursorEventId ??
                    null
                  }
                  cachedActiveRequestId={cacheEntry?.activeRequestId ?? null}
                  initialComposeText={cacheEntry?.composeText ?? ''}
                  initialScrollAnchor={cacheEntry?.scrollAnchor ?? null}
                  initialRangeStartText={
                    cacheEntry?.rangeStartText ??
                    DEFAULT_MOBILE_TRANSCRIPT_RANGE.startText
                  }
                  initialRangeEndText={
                    cacheEntry?.rangeEndText ??
                    DEFAULT_MOBILE_TRANSCRIPT_RANGE.endText
                  }
                  onUpdateCache={(
                    list: IndexedMessage[],
                    eventsCursorId: string | null,
                    activeRequestId: string | null,
                  ) => {
                    if (connectionId) {
                      onUpdateMessagesCache(
                        connectionId,
                        selectedSessionId,
                        list,
                        eventsCursorId,
                        activeRequestId,
                      );
                    }
                  }}
                  onUpdateSessionSummaries={(sessions) => {
                    if (connectionId) {
                      onUpdateSessionsCache(connectionId, sessions);
                    }
                  }}
                  onBack={() => {
                    setTab('sessions');
                  }}
                  onNavigateToSession={(sessionId) => {
                    setSelectedSessionId(sessionId);
                    setTab('messages');
                  }}
                  onSaveComposeText={(composeText) => {
                    const connectionId = activeConnectionId;
                    if (connectionId) {
                      onSaveMessagesComposeText(connectionId, selectedSessionId, composeText);
                    }
                  }}
                  onSaveScrollAnchor={(scrollAnchor) => {
                    const connectionId = activeConnectionId;
                    if (connectionId) {
                      onSaveMessagesScrollAnchor(connectionId, selectedSessionId, scrollAnchor);
                    }
                  }}
                  onSaveHistoryRange={(rangeStartText, rangeEndText) => {
                    const connectionId = activeConnectionId;
                    if (connectionId) {
                      onSaveMessagesHistoryRange(
                        connectionId,
                        selectedSessionId,
                        rangeStartText,
                        rangeEndText,
                      );
                    }
                  }}
                  debugTimeline={debugTimeline}
                  onAppendDebugTimelineEntry={onAppendDebugTimelineEntry}
                />
              );
            })()
          ) : (
            <View style={styles.placeholderContainer}>
              <Text style={styles.placeholderText}>Select a session from the Sessions tab.</Text>
            </View>
          )}
        </View>
        </View>
        </GlobalDisplayLayer>
      </ApplicationPluginsProvider>

      <View style={styles.navBar}>
        <TouchableOpacity
          style={[styles.navItem, tab === 'connection' && styles.navItemActive]}
          onPress={() => setTab('connection')}
        >
          <Icon
            name="wifi"
            size={20}
            color={tab === 'connection' ? theme.navIconActive : theme.navIconInactive}
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
            color={tab === 'sessions' ? theme.navIconActive : theme.navIconInactive}
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
            color={tab === 'messages' ? theme.navIconActive : theme.navIconInactive}
          />
          <Text style={tab === 'messages' ? styles.navTextActive : styles.navText}>Messages</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};
const createStyles = (theme: Theme, insets: { top: number; bottom: number; left: number; right: number }) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.background,
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
      backgroundColor: theme.primary,
    },
    buttonText: {
      color: theme.textOnPrimary,
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
      color: theme.textSecondary,
    },
    demoResponseContainer: {
      marginTop: 8,
      backgroundColor: theme.surfaceAlt,
      borderRadius: 8,
      padding: 10,
      maxHeight: 220,
    },
    demoResponseText: {
      fontSize: 12,
      fontFamily: 'Courier',
      color: theme.text,
    },
    navBar: {
      flexDirection: 'row',
      borderTopWidth: 1,
      borderTopColor: theme.navBarBorder,
      paddingVertical: 6,
      paddingBottom: Math.max(6, insets.bottom),
      backgroundColor: theme.navBarBg,
    },
    navItem: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      gap: 2,
    },
    navItemActive: {
      borderTopWidth: 2,
      borderTopColor: theme.primary,
    },
    navText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    navTextActive: {
      fontSize: 12,
      color: theme.primary,
      fontWeight: '600',
    },
    placeholderContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    placeholderText: {
      fontSize: 14,
      color: theme.textSecondary,
      textAlign: 'center',
    },
  });

export default ConnectedRoot;
