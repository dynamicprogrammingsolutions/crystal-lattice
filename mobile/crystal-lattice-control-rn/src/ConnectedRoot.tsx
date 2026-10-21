import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  useMemo,
} from "react";
import {
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Icon from "react-native-vector-icons/Feather";
import type {
  AgentBackend,
  ConnectionRecord,
  Transport,
} from "@crystal-lattice/frontend-sdk";
import type { SessionsCache } from "../App";
import type { DebugTimelineEntry } from "./debugTimeline";
import type { MessagesCache } from "./cache/types";
import HomeConnectionsSection from "./connections/HomeConnectionsSection";
import ConnectionWizardModal from "./connections/ConnectionWizardModal";
import SessionsScreen from "./SessionsScreen";
import type { SessionSummary, IndexedMessage } from "./api";
import SessionChatScreen from "./SessionChatScreen";
import type { ChatScrollAnchor } from "./chatScroll";
import { useTheme, type Theme } from "./theme";
import { ApplicationPluginsProvider } from "./ApplicationPluginsContext";
import { DEFAULT_MOBILE_TRANSCRIPT_RANGE } from "./transcriptRange";
import GlobalDisplayLayer from "./components/GlobalDisplayLayer";
import GlobalSettingsModal from "./components/GlobalSettingsModal";
import DevelopmentSettingsModal from "./components/DevelopmentSettingsModal";
import type { DevelopmentSettingsState } from "./settings/useDevelopmentSettings";
import ServerSettingsModal from "./components/ServerSettingsModal";
import HomeScreen from "./HomeScreen";
import { useHomeWorkspace } from "./HomeWorkspaceContext";
import { deriveHomeSessionCollections } from "./homeWorkspaceState";
import { MobileConnectionSessionStatusReader } from "./connectionSessionStatusReader";
import { useSessionRequestStatuses } from "./useSessionRequestStatuses";
import { HumanTimeTelemetryProvider } from "./humanTimeTelemetry/HumanTimeTelemetryProvider";
import EmbeddedRuntimeSettingsModal from "./embeddedRuntime/EmbeddedRuntimeSettingsModal";
import type { EmbeddedRuntimePublicConfiguration } from "./embeddedRuntime/embeddedPythonRuntime";
import { ChatWorkspaceProvider } from "@crystal-lattice/frontend-sdk-react";
import { DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY } from "./transcriptAnchorStrategy";

interface ConnectedRootProps {
  developmentSettings?: DevelopmentSettingsState;
  backend: AgentBackend | null;
  transport: Transport | null;
  onDisconnect: () => void;
  connections: ConnectionRecord[];
  connectionsLoading: boolean;
  onSelectConnectionRecord: (
    record: ConnectionRecord
  ) => void | boolean | Promise<void | boolean>;
  onNewConnectionRequested: () => void;
  renderConnectionWizard: () => React.ReactNode;
  onCloseConnectionWizard: () => void;
  onDeleteConnectionRecord: (record: ConnectionRecord) => void;
  activeConnectionId: string | null;
  sessionsCache: SessionsCache;
  onUpdateSessionsCache: (
    connectionId: string,
    sessions: SessionSummary[]
  ) => void;
  messagesCache: MessagesCache;
  onUpdateMessagesCache: (
    connectionId: string,
    sessionId: string,
    messages: IndexedMessage[],
    eventsCursorId: string | null,
    activeRequestId: string | null
  ) => void;
  onSaveMessagesComposeText: (
    connectionId: string,
    sessionId: string,
    composeText: string
  ) => void;
  onSaveMessagesScrollAnchor: (
    connectionId: string,
    sessionId: string,
    scrollAnchor: ChatScrollAnchor
  ) => void;
  onSaveMessagesHistoryRange: (
    connectionId: string,
    sessionId: string,
    rangeStartText: string,
    rangeEndText: string
  ) => void;
  debugTimeline: DebugTimelineEntry[];
  onAppendDebugTimelineEntry: (
    entry: Omit<DebugTimelineEntry, "id" | "timestampMs"> & {
      detail?: string | null;
      meta?: Record<string, any> | null;
    }
  ) => void;
  onEmbeddedSettingsChanged?: (
    configuration: EmbeddedRuntimePublicConfiguration
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
  onCloseConnectionWizard,
  onDeleteConnectionRecord,
  activeConnectionId,
  sessionsCache,
  onUpdateSessionsCache,
  messagesCache,
  onUpdateMessagesCache,
  onSaveMessagesComposeText,
  onSaveMessagesScrollAnchor,
  onSaveMessagesHistoryRange,
  debugTimeline,
  onAppendDebugTimelineEntry,
  onEmbeddedSettingsChanged,
  developmentSettings,
}) => {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const styles = useMemo(() => createStyles(theme, insets), [theme, insets]);
  const [tab, setTab] = useState<"home" | "sessions" | "messages">("home");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null
  );
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoResponse, setDemoResponse] = useState("");
  const [globalSettingsVisible, setGlobalSettingsVisible] = useState(false);
  const [developmentSettingsVisible, setDevelopmentSettingsVisible] =
    useState(false);
  const [serverSettingsVisible, setServerSettingsVisible] = useState(false);
  const [embeddedSettingsVisible, setEmbeddedSettingsVisible] = useState(false);
  const [newSessionRequestToken, setNewSessionRequestToken] = useState(0);
  const newSessionRequestSequenceRef = useRef(0);
  const navigationIntentRef = useRef(0);
  const {
    hydrated: homeWorkspaceHydrated,
    watchlist,
    notes,
    recentSessionsWindow,
    removeFromWatchlist,
  } = useHomeWorkspace();
  const activeConnectionName = useMemo(
    () =>
      connections.find((record) => record.id === activeConnectionId)?.name ??
      "Sessions",
    [activeConnectionId, connections]
  );
  const homeCollections = useMemo(
    () =>
      deriveHomeSessionCollections({
        connections,
        sessionsCache,
        watchlist,
        notes,
        recentSessionsWindow,
      }),
    [connections, notes, recentSessionsWindow, sessionsCache, watchlist]
  );
  const statusSessionIdsByConnection = useMemo(() => {
    const groups: Record<string, string[]> = {};
    if (tab === "home") {
      for (const item of [
        ...homeCollections.watchlist,
        ...homeCollections.recent,
      ]) {
        const values = groups[item.connectionId] ?? [];
        values.push(item.sessionId);
        groups[item.connectionId] = values;
      }
    }
    if (tab === "sessions" && activeConnectionId) {
      groups[activeConnectionId] =
        sessionsCache[activeConnectionId]?.sessions.map(
          (session) => session.session_id
        ) ?? [];
    }
    return groups;
  }, [activeConnectionId, homeCollections, sessionsCache, tab]);
  const statusReader = useMemo(
    () => new MobileConnectionSessionStatusReader(activeConnectionId, backend),
    [activeConnectionId, backend]
  );
  const handleMissingSessionIds = useCallback(
    (connectionId: string, sessionIds: readonly string[]) => {
      for (const sessionId of sessionIds) {
        removeFromWatchlist(connectionId, sessionId);
      }
    },
    [removeFromWatchlist]
  );
  const statusesByConnection = useSessionRequestStatuses({
    enabled: tab === "home" || tab === "sessions",
    connections,
    sessionIdsByConnection: statusSessionIdsByConnection,
    reader: statusReader,
    onMissingSessionIds: handleMissingSessionIds,
  });

  useEffect(() => {
    if (!homeWorkspaceHydrated || connectionsLoading) return;
    const savedConnectionIds = new Set(
      connections.map((connection) => connection.id)
    );
    for (const watched of watchlist) {
      if (!savedConnectionIds.has(watched.connectionId)) {
        removeFromWatchlist(watched.connectionId, watched.sessionId);
      }
    }
  }, [
    connections,
    connectionsLoading,
    homeWorkspaceHydrated,
    removeFromWatchlist,
    watchlist,
  ]);

  const executeDemoRequest = async (type: "GET" | "PUT") => {
    setDemoLoading(true);
    setDemoResponse("");

    try {
      if (!transport) {
        throw new Error("No active connection");
      }

      const payload =
        type === "PUT"
          ? {
              message: "Hello from React Native",
              timestamp: new Date().toISOString(),
            }
          : undefined;
      const resp = await transport.request({
        method: type,
        path: "/api/data",
        body: payload,
      });

      setDemoResponse(JSON.stringify(resp.data, null, 2));
    } catch (err: any) {
      const message = err?.message || "Demo request failed";
      setDemoResponse(`Error: ${message}`);
    } finally {
      setDemoLoading(false);
    }
  };

  const handleSelectSession = (sessionId: string) => {
    navigationIntentRef.current += 1;
    setSelectedSessionId(sessionId);
    setTab("messages");
  };

  const handleSelectHomeSession = async (
    connectionId: string,
    sessionId: string
  ) => {
    const record = connections.find(
      (connection) => connection.id === connectionId
    );
    if (!record) return;
    const intent = navigationIntentRef.current + 1;
    navigationIntentRef.current = intent;
    const isOpen =
      connectionId === activeConnectionId &&
      backend !== null &&
      transport !== null;
    if (!isOpen) {
      const opened = await onSelectConnectionRecord(record);
      if (opened === false || navigationIntentRef.current !== intent) return;
    }
    if (navigationIntentRef.current !== intent) return;
    setSelectedSessionId(sessionId);
    setTab("messages");
  };

  const handleNewConnectionSession = async (record: ConnectionRecord) => {
    const intent = navigationIntentRef.current + 1;
    navigationIntentRef.current = intent;
    const isOpen =
      record.id === activeConnectionId &&
      backend !== null &&
      transport !== null;
    if (!isOpen) {
      const opened = await onSelectConnectionRecord(record);
      if (opened === false || navigationIntentRef.current !== intent) return;
    }
    if (navigationIntentRef.current !== intent) return;
    newSessionRequestSequenceRef.current += 1;
    setNewSessionRequestToken(newSessionRequestSequenceRef.current);
    setTab("sessions");
  };

  // Stable cache-update callbacks: SessionChatScreen derives reload
  // callbacks from these props, so inline arrows here would change the
  // identity of its session-refresh subscriptions on every render.
  const handleUpdateMessagesCache = useCallback(
    (
      list: IndexedMessage[],
      eventsCursorId: string | null,
      activeRequestId: string | null
    ) => {
      if (activeConnectionId && selectedSessionId) {
        onUpdateMessagesCache(
          activeConnectionId,
          selectedSessionId,
          list,
          eventsCursorId,
          activeRequestId
        );
      }
    },
    [activeConnectionId, onUpdateMessagesCache, selectedSessionId]
  );

  const handleUpdateSessionSummaries = useCallback(
    (sessions: SessionSummary[]) => {
      if (activeConnectionId) {
        onUpdateSessionsCache(activeConnectionId, sessions);
      }
    },
    [activeConnectionId, onUpdateSessionsCache]
  );

  return (
    <View style={styles.container}>
      <ApplicationPluginsProvider
        backend={backend}
        connectionId={activeConnectionId}
      >
        <GlobalDisplayLayer backend={backend} connectionId={activeConnectionId}>
          <HumanTimeTelemetryProvider
            backend={backend}
            connectionId={activeConnectionId}
            activeSessionId={tab === "messages" ? selectedSessionId : null}
          >
            <View style={styles.contentArea} testID="connected-root-content">
              <View
                testID="home-tab-content"
                style={[
                  styles.connectionsTabContainer,
                  tab !== "home" && { display: "none" },
                ]}
              >
                <HomeScreen
                  renderConnectionSection={(onCollapse) => (
                    <HomeConnectionsSection
                      connections={connections}
                      loading={connectionsLoading}
                      activeConnectionId={activeConnectionId}
                      transport={transport}
                      onConnectionCardPress={(record) => {
                        navigationIntentRef.current += 1;
                        setTab("sessions");
                        if (
                          record.id !== activeConnectionId ||
                          transport === null
                        ) {
                          void onSelectConnectionRecord(record);
                        }
                      }}
                      onOpenConnection={(record) => {
                        void onSelectConnectionRecord(record);
                      }}
                      onNewSession={(record) => {
                        void handleNewConnectionSession(record);
                      }}
                      onNewConnection={onNewConnectionRequested}
                      onOpenServerSettings={() =>
                        setServerSettingsVisible(true)
                      }
                      onDisconnect={onDisconnect}
                      onDeleteConnection={onDeleteConnectionRecord}
                      onCollapse={onCollapse}
                    />
                  )}
                  connections={connections}
                  sessionsCache={sessionsCache}
                  statusesByConnection={statusesByConnection}
                  onOpenGlobalSettings={() => setGlobalSettingsVisible(true)}
                  onOpenDevelopmentSettings={
                    developmentSettings
                      ? () => setDevelopmentSettingsVisible(true)
                      : undefined
                  }
                  onOpenEmbeddedSettings={
                    Platform.OS === "ios"
                      ? () => setEmbeddedSettingsVisible(true)
                      : undefined
                  }
                  onNewConnection={() => {
                    navigationIntentRef.current += 1;
                    onNewConnectionRequested();
                  }}
                  onSelectSession={(connectionId, sessionId) => {
                    void handleSelectHomeSession(connectionId, sessionId);
                  }}
                />
              </View>

              {/* Sessions tab content (kept mounted, visibility toggled) */}
              <View
                testID="sessions-tab-content"
                style={[
                  styles.connectionsTabContainer,
                  tab !== "sessions" && { display: "none" },
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
                          No sessions loaded yet. Open a connection from Home to
                          connect to a server.
                        </Text>
                      </View>
                    );
                  }

                  return (
                    <SessionsScreen
                      backend={backend}
                      connectionId={connectionId}
                      connectionName={activeConnectionName}
                      cachedSessions={cacheEntry?.sessions ?? null}
                      lastLoadedAt={cacheEntry?.lastLoadedAt ?? null}
                      isActive={tab === "sessions"}
                      onUpdateCache={handleUpdateSessionSummaries}
                      onSelectSession={handleSelectSession}
                      requestStatuses={
                        connectionId
                          ? statusesByConnection[connectionId] ?? {}
                          : {}
                      }
                      newSessionRequestToken={newSessionRequestToken}
                      onNewSessionRequestHandled={(token) => {
                        setNewSessionRequestToken((current) =>
                          current === token ? 0 : current
                        );
                      }}
                    />
                  );
                })()}
              </View>

              {/* Messages tab content (kept mounted, visibility toggled) */}
              <View
                testID="messages-tab-content"
                style={[
                  styles.connectionsTabContainer,
                  tab !== "messages" && { display: "none" },
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
                    const sessionSummary: SessionSummary | null =
                      sessionsEntry?.sessions
                        ? sessionsEntry.sessions.find(
                            (s) => s.session_id === selectedSessionId
                          ) ?? null
                        : null;

                    if (!backend && !cacheEntry) {
                      return (
                        <View style={styles.placeholderContainer}>
                          <Text style={styles.placeholderText}>
                            No messages loaded yet. Connect to a server to load
                            this session.
                          </Text>
                        </View>
                      );
                    }

                    return (
                      <SessionChatScreen
                        key={selectedSessionId}
                        backend={backend}
                        connectionId={connectionId}
                        isActive={tab === "messages"}
                        sessionId={selectedSessionId}
                        sessionSummary={sessionSummary}
                        cachedMessages={cacheEntry?.messages ?? null}
                        lastLoadedAt={cacheEntry?.lastLoadedAt ?? null}
                        cachedEventsCursorId={
                          cacheEntry?.eventsCursorId ??
                          cacheEntry?.cursorEventId ??
                          null
                        }
                        cachedActiveRequestId={
                          cacheEntry?.activeRequestId ?? null
                        }
                        initialComposeText={cacheEntry?.composeText ?? ""}
                        initialScrollAnchor={cacheEntry?.scrollAnchor ?? null}
                        initialRangeStartText={
                          cacheEntry?.rangeStartText ??
                          DEFAULT_MOBILE_TRANSCRIPT_RANGE.startText
                        }
                        initialRangeEndText={
                          cacheEntry?.rangeEndText ??
                          DEFAULT_MOBILE_TRANSCRIPT_RANGE.endText
                        }
                        transcriptAnchorStrategy={
                          developmentSettings?.transcriptAnchorStrategy ??
                          DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY
                        }
                        onUpdateCache={handleUpdateMessagesCache}
                        onUpdateSessionSummaries={(sessions) => {
                          if (connectionId) {
                            onUpdateSessionsCache(connectionId, sessions);
                          }
                        }}
                        onBack={() => {
                          navigationIntentRef.current += 1;
                          setTab("sessions");
                        }}
                        onNavigateToSession={(sessionId) => {
                          navigationIntentRef.current += 1;
                          setSelectedSessionId(sessionId);
                          setTab("messages");
                        }}
                        onSaveComposeText={(composeText) => {
                          const connectionId = activeConnectionId;
                          if (connectionId) {
                            onSaveMessagesComposeText(
                              connectionId,
                              selectedSessionId,
                              composeText
                            );
                          }
                        }}
                        onSaveScrollAnchor={(scrollAnchor) => {
                          const connectionId = activeConnectionId;
                          if (connectionId) {
                            onSaveMessagesScrollAnchor(
                              connectionId,
                              selectedSessionId,
                              scrollAnchor
                            );
                          }
                        }}
                        onSaveHistoryRange={(rangeStartText, rangeEndText) => {
                          const connectionId = activeConnectionId;
                          if (connectionId) {
                            onSaveMessagesHistoryRange(
                              connectionId,
                              selectedSessionId,
                              rangeStartText,
                              rangeEndText
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
                    <Text style={styles.placeholderText}>
                      Select a session from the Sessions tab.
                    </Text>
                  </View>
                )}
              </View>
            </View>
            <GlobalSettingsModal
              visible={globalSettingsVisible}
              onRequestClose={() => setGlobalSettingsVisible(false)}
              onEmbeddedSettingsChanged={onEmbeddedSettingsChanged}
            />
          </HumanTimeTelemetryProvider>
        </GlobalDisplayLayer>
      </ApplicationPluginsProvider>

      <ServerSettingsModal
        backend={backend}
        cacheKey={activeConnectionId ?? "default"}
        visible={serverSettingsVisible}
        onRequestClose={() => setServerSettingsVisible(false)}
      />
      {developmentSettings ? (
        <DevelopmentSettingsModal
          visible={developmentSettingsVisible}
          onRequestClose={() => setDevelopmentSettingsVisible(false)}
          preferences={developmentSettings}
        />
      ) : null}
      <EmbeddedRuntimeSettingsModal
        visible={embeddedSettingsVisible}
        onRequestClose={() => setEmbeddedSettingsVisible(false)}
        onSaved={onEmbeddedSettingsChanged}
      />
      <ConnectionWizardModal
        content={renderConnectionWizard()}
        onCancel={onCloseConnectionWizard}
      />

      <View style={styles.navBar}>
        <TouchableOpacity
          testID="home-tab"
          style={[styles.navItem, tab === "home" && styles.navItemActive]}
          onPress={() => {
            navigationIntentRef.current += 1;
            setTab("home");
          }}
        >
          <Icon
            name="home"
            size={20}
            color={tab === "home" ? theme.navIconActive : theme.navIconInactive}
          />
          <Text style={tab === "home" ? styles.navTextActive : styles.navText}>
            Home
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="sessions-tab"
          style={[styles.navItem, tab === "sessions" && styles.navItemActive]}
          onPress={() => {
            navigationIntentRef.current += 1;
            setTab("sessions");
          }}
        >
          <Icon
            name="list"
            size={20}
            color={
              tab === "sessions" ? theme.navIconActive : theme.navIconInactive
            }
          />
          <Text
            style={tab === "sessions" ? styles.navTextActive : styles.navText}
          >
            Sessions
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="messages-tab"
          style={[styles.navItem, tab === "messages" && styles.navItemActive]}
          onPress={() => {
            navigationIntentRef.current += 1;
            setTab("messages");
          }}
        >
          <Icon
            name="message-circle"
            size={20}
            color={
              tab === "messages" ? theme.navIconActive : theme.navIconInactive
            }
          />
          <Text
            style={tab === "messages" ? styles.navTextActive : styles.navText}
          >
            Messages
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};
const createStyles = (
  theme: Theme,
  insets: { top: number; bottom: number; left: number; right: number }
) =>
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
      fontWeight: "600",
    },
    demoContainer: {
      flex: 1,
    },
    demoButtonsRow: {
      flexDirection: "row",
      marginBottom: 8,
    },
    loadingContainer: {
      flexDirection: "row",
      alignItems: "center",
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
      fontFamily: "Courier",
      color: theme.text,
    },
    navBar: {
      flexDirection: "row",
      borderTopWidth: 1,
      borderTopColor: theme.navBarBorder,
      paddingVertical: 6,
      paddingBottom: Math.max(6, insets.bottom),
      backgroundColor: theme.navBarBg,
    },
    navItem: {
      flex: 1,
      alignItems: "center",
      justifyContent: "center",
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
      fontWeight: "600",
    },
    placeholderContainer: {
      flex: 1,
      justifyContent: "center",
      alignItems: "center",
    },
    placeholderText: {
      fontSize: 14,
      color: theme.textSecondary,
      textAlign: "center",
    },
  });

export default function ConnectedChatWorkspace(props: ConnectedRootProps) {
  return (
    <ChatWorkspaceProvider>
      <ConnectedRoot {...props} />
    </ChatWorkspaceProvider>
  );
}
