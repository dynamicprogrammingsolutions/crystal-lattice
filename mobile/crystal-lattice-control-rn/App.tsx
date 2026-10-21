import 'react-native-url-polyfill/auto';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  AppState,
  Linking,
  Platform,
  StatusBar,
  StyleSheet,
  useColorScheme,
  Alert,
  Keyboard,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Zeroconf from 'react-native-zeroconf';
import {
  CloudTransport,
  FetchTransport,
  createBridgeConnectionTransport,
  deriveBridgeHttpBaseUrl,
  normalizeBridgeAddress,
  invalidateAgentsCache,
  parseCloudConnectionLink,
  type KeyValueStore,
  loadConnections,
  RestAgentBackend,
  saveConnections,
  type AgentBackend,
  type BridgeServer,
  type BridgeConnectionRecord,
  type BridgeConnectionTransport,
  type BridgeTransportMode,
  type CloudConnectionRecord,
  type ConnectionRecord,
  type DiscoveryConnectionRecord,
  type EmbeddedConnectionRecord,
  type ManualConnectionRecord,
  type Transport,
  type TransportTimeoutRule,
  type ParsedActionDeepLink,
} from '@crystal-lattice/frontend-sdk';
import {
  MarkdownDisplayPreferencesProvider,
  applyDisplayTypographyPreset,
} from '@crystal-lattice/frontend-rn-components';
import ConnectedRoot from './src/ConnectedRoot';
import { useMessagesCache } from './src/cache/useMessagesCache';
import type { SessionSummary } from './src/api';
import {
  appendDebugTimelineEntry,
  createDebugTimelineEntry,
  type DebugTimelineEntry,
} from './src/debugTimeline';
import { ThemeProvider, lightTheme, darkTheme, type Theme } from './src/theme';
import { PinnedActionsProvider } from './src/PinnedActionsContext';
import { AnimatedSplashScreen } from './src/components/AnimatedSplashScreen';
import { createActionDeepLinkHandler } from './src/actionDeepLinkRouting';
import {
  DEFAULT_BRIDGE_TRANSPORT_MODE,
  getSavedBridgeTransportOptions,
  resolveBridgeTransportMode,
} from './src/bridgeConnection';
import { usePersistedMarkdownDisplayPreferences } from './src/useMarkdownDisplayPreferences';
import { HomeWorkspaceProvider } from './src/HomeWorkspaceContext';
import { createEmbeddedRuntimeBackend } from './src/embeddedRuntime/createEmbeddedRuntimeBackend';
import {
  configureEmbeddedPythonRuntime,
  getEmbeddedPythonRuntimeConfiguration,
  noteEmbeddedPythonRuntimeAppState,
  type EmbeddedRuntimePublicConfiguration,
} from './src/embeddedRuntime/embeddedPythonRuntime';
import {
  CloudConnectionStep, ConnectionMethodStep, DiscoveryConnectionStep,
  EmbeddedConnectionStep, ManualConnectionStep,
  type ConnectionMethod, type DiscoveredService as Service,
} from './src/connections/ConnectionWizardSteps';
import BridgeConnectionStep from './src/connections/BridgeConnectionStep';
import { useConnectionSetup } from './src/connections/useConnectionSetup';
import { useSavedBridgeUrls } from './src/connections/useSavedBridgeUrls';
import { useDevelopmentSettings } from './src/settings/useDevelopmentSettings';
import { bridgeConnectionErrorMessage } from './src/connections/bridgeErrors';

const connectionsStore: KeyValueStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};
const STORAGE_KEY_SESSIONS_CACHE = 'clc_sessions_cache_v1';
const EMBEDDED_CONNECTION_ID = 'embedded-ios-runtime';

function embeddedConnectionRecord(
  configuration: EmbeddedRuntimePublicConfiguration,
  lastUsedAt = Date.now(),
): EmbeddedConnectionRecord {
  const selectedProfile = configuration.selectedProfileId
    ? configuration.providers[configuration.selectedProfileId]
    : undefined;
  return {
    id: EMBEDDED_CONNECTION_ID,
    kind: 'embedded',
    name: 'Local agent',
    proxyUrl: selectedProfile?.baseUrl ?? configuration.proxyUrl,
    model: selectedProfile?.model ?? configuration.model,
    lastUsedAt,
  };
}

export interface SessionsCacheEntry {
  connectionId: string;
  sessions: SessionSummary[];
  lastLoadedAt: number | null;
}

export type SessionsCache = Record<string, SessionsCacheEntry>;

function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    // eslint-disable-next-line no-bitwise
    const r = (Math.random() * 16) | 0;
    // eslint-disable-next-line no-bitwise
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

const DEFAULT_REQUEST_TIMEOUT_MS = 30_000;
const LONG_RUNNING_REQUEST_TIMEOUT_MS = 120_000;
const EVENTS_TIMEOUT_MS = 10_000;
const BRIDGE_CONNECT_TIMEOUT_MS = 10_000;
const BRIDGE_HEARTBEAT_INTERVAL_MS = 15_000;
const BRIDGE_HEARTBEAT_TIMEOUT_MS = 5_000;
const TRANSPORT_TIMEOUT_RULES: TransportTimeoutRule[] = [
  { method: 'GET', pathPrefix: '/events', timeoutMs: EVENTS_TIMEOUT_MS },
  {
    method: 'POST',
    pathRegex: /^\/sessions\/[^/]+\/messages(?:\?|$)/,
    timeoutMs: LONG_RUNNING_REQUEST_TIMEOUT_MS,
  },
  {
    method: 'POST',
    pathRegex: /^\/sessions\/[^/]+\/send_message(?:\?|$)/,
    timeoutMs: LONG_RUNNING_REQUEST_TIMEOUT_MS,
  },
  { method: 'POST', pathPrefix: '/actions', timeoutMs: LONG_RUNNING_REQUEST_TIMEOUT_MS },
];

function createHttpTransport(baseUrl: string): FetchTransport {
  return new FetchTransport({
    baseUrl,
    defaultRequestTimeoutMs: DEFAULT_REQUEST_TIMEOUT_MS,
    timeoutRules: TRANSPORT_TIMEOUT_RULES,
  });
}

function createBridgeTransport(options: {
  bridgeUrl: string;
  mode?: BridgeTransportMode;
  serverId?: string | null;
  pairingToken?: string | null;
  debug?: boolean;
}): BridgeConnectionTransport {
  return createBridgeConnectionTransport({
    bridgeUrl: options.bridgeUrl,
    mode: options.mode ?? DEFAULT_BRIDGE_TRANSPORT_MODE,
    serverId: options.serverId,
    pairingToken: options.pairingToken,
    debug: options.debug ?? true,
    defaultRequestTimeoutMs: DEFAULT_REQUEST_TIMEOUT_MS,
    connectTimeoutMs: BRIDGE_CONNECT_TIMEOUT_MS,
    heartbeatIntervalMs: BRIDGE_HEARTBEAT_INTERVAL_MS,
    heartbeatTimeoutMs: BRIDGE_HEARTBEAT_TIMEOUT_MS,
    timeoutRules: TRANSPORT_TIMEOUT_RULES,
  });
}

function createCloudTransport(record: Pick<CloudConnectionRecord, 'orchestratorUrl' | 'connectionId' | 'instanceId' | 'token'>): CloudTransport {
  return new CloudTransport({
    orchestratorUrl: record.orchestratorUrl,
    connectionId: record.connectionId,
    instanceId: record.instanceId,
    token: record.token,
    defaultRequestTimeoutMs: DEFAULT_REQUEST_TIMEOUT_MS,
    timeoutRules: TRANSPORT_TIMEOUT_RULES,
  });
}

function getBridgeReconnectErrorCode(error: unknown): 'invalid_pairing_token' | 'server_not_found' | 'server_mismatch' | null {
  const message =
    error instanceof Error ? error.message : typeof error === 'string' ? error : '';
  if (message.includes('invalid_pairing_token')) {
    return 'invalid_pairing_token';
  }
  if (message.includes('server_not_found')) {
    return 'server_not_found';
  }
  if (message.includes('server_mismatch')) {
    return 'server_mismatch';
  }
  return null;
}

function disconnectIfPossible(candidate: unknown): void {
  if (
    candidate &&
    typeof candidate === 'object' &&
    'disconnect' in candidate &&
    typeof (candidate as any).disconnect === 'function'
  ) {
    (candidate as any).disconnect();
  }
}

function isBridgeConnectionTransport(
  candidate: unknown,
): candidate is BridgeConnectionTransport {
  return (
    candidate != null &&
    typeof candidate === 'object' &&
    'connect' in candidate &&
    typeof (candidate as any).connect === 'function' &&
    'prepareForResume' in candidate &&
    typeof (candidate as any).prepareForResume === 'function' &&
    'getPairingToken' in candidate &&
    typeof (candidate as any).getPairingToken === 'function'
  );
}

function App(): React.JSX.Element {
  const colorScheme = useColorScheme();
  const baseTheme = colorScheme === 'dark' ? darkTheme : lightTheme;

  const [connectionMethod, setConnectionMethod] = useState<ConnectionMethod | null>(null);
  const [showConnectionWizard, setShowConnectionWizard] = useState(false);
  const [transport, setTransport] = useState<Transport | null>(null);
  const [backend, setBackend] = useState<AgentBackend | null>(null);
  const [connections, setConnections] = useState<ConnectionRecord[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null);
  const [connectionsLoading, setConnectionsLoading] = useState(true);
  const [sessionsCache, setSessionsCache] = useState<SessionsCache>({});
  const [debugTimeline, setDebugTimeline] = useState<DebugTimelineEntry[]>([]);
  
  const [isSearching, setIsSearching] = useState(false);
  const [discoveredServices, setDiscoveredServices] = useState<Service[]>([]);
  const zeroconf = useRef(new Zeroconf()).current;

  const [manualHost, setManualHost] = useState('');
  const [manualPort, setManualPort] = useState('8080');

  const [bridgeUrl, setBridgeUrl] = useState('');
  const developmentSettings = useDevelopmentSettings(connectionsStore);
  const savedBridgeUrls = useSavedBridgeUrls(connectionsStore);
  const [bridgeServers, setBridgeServers] = useState<BridgeServer[]>([]);
  const [selectedBridgeServer, setSelectedBridgeServer] = useState<BridgeServer | null>(null);
  const [pairingCode, setPairingCode] = useState('');
  const [connectingBridgeTransport, setConnectingBridgeTransport] =
    useState<BridgeConnectionTransport | null>(null);
  const repairingBridgeRecordRef = useRef<BridgeConnectionRecord | null>(null);
  const [cloudConnectionLink, setCloudConnectionLink] = useState('');
  const [embeddedProxyUrl, setEmbeddedProxyUrl] = useState(
    'http://127.0.0.1:3000/v1',
  );
  const [embeddedModel, setEmbeddedModel] = useState('qwen3.5:0.8b');
  const [embeddedApiKey, setEmbeddedApiKey] = useState('');
  const [embeddedHasSavedApiKey, setEmbeddedHasSavedApiKey] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [isAppLoading, setIsAppLoading] = useState(true);
  const {
    preferences: markdownDisplayPreferences,
    setPreferences: setMarkdownDisplayPreferences,
    hydrated: markdownDisplayPreferencesHydrated,
  } = usePersistedMarkdownDisplayPreferences();
  const theme = useMemo(
    () => applyDisplayTypographyPreset(
      baseTheme,
      markdownDisplayPreferences.baseFontSize,
    ),
    [baseTheme, markdownDisplayPreferences.baseFontSize],
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsAppLoading(false);
    }, 2800);
    return () => clearTimeout(timer);
  }, []);

  const styles = useMemo(() => createStyles(theme), [theme]);
  const appStateRef = useRef(AppState.currentState);
  const backendRef = useRef<AgentBackend | null>(null);
  const initialUrlHandledRef = useRef(false);
  const foregroundRecoveryInFlightRef = useRef(false);
  const [pendingActionDeepLink, setPendingActionDeepLink] = useState<ParsedActionDeepLink | null>(null);
  const {
    messagesCache,
    updateMessagesCache,
    saveMessagesComposeText,
    saveMessagesScrollAnchor,
    saveMessagesHistoryRange,
    deleteConnectionMessagesCache,
  } = useMessagesCache(connectionsStore);
  const activeConnection = useMemo(
    () =>
      selectedConnectionId != null
        ? connections.find((connection) => connection.id === selectedConnectionId) ?? null
        : null,
    [connections, selectedConnectionId],
  );

  useEffect(() => {
    backendRef.current = backend;
  }, [backend]);

  const appendDebugNote = useCallback(
    (entry: Omit<DebugTimelineEntry, 'id' | 'timestampMs'> & {
      detail?: string | null;
      meta?: Record<string, any> | null;
    }) => {
      setDebugTimeline((prev) =>
        appendDebugTimelineEntry(
          prev,
          createDebugTimelineEntry({
            scope: entry.scope,
            title: entry.title,
            detail: entry.detail,
            meta: entry.meta,
          }),
        ),
      );
    },
    [],
  );

  const executeActionDeepLink = useCallback(
    async (url: string) => {
      const handler = createActionDeepLinkHandler({
        hasConnection: (connectionId) =>
          connections.some((connection) => connection.id === connectionId),
        getBackendForConnection: (connectionId) =>
          connectionId === selectedConnectionId ? backendRef.current : null,
        queuePendingAction: setPendingActionDeepLink,
      });

      const outcome = await handler(url);
      if (!outcome.handled) {
        return;
      }

      if (outcome.status === 'queued') {
        appendDebugNote({
          scope: 'app',
          title: 'Action link queued',
          detail: outcome.parsed.callbackElementId,
          meta: {
            connectionId: outcome.parsed.connectionId,
            sessionId: outcome.parsed.sessionId,
            pluginId: outcome.parsed.pluginId ?? null,
          },
        });
        Alert.alert(
          'Action Pending',
          'Connect to the linked server to finish this action.',
        );
        return;
      }

      if (outcome.status === 'ok') {
        appendDebugNote({
          scope: 'app',
          title: 'Action link execution succeeded',
          detail: outcome.parsed.callbackElementId,
          meta: {
            connectionId: outcome.parsed.connectionId,
            sessionId: outcome.parsed.sessionId,
            pluginId: outcome.response.plugin,
            actionId: outcome.response.action_id,
          },
        });

        const resultMessage =
          outcome.response.result && typeof outcome.response.result.message === 'string'
            ? outcome.response.result.message
            : '';
        if (resultMessage) {
          Alert.alert('Action Complete', resultMessage);
        }
        return;
      }

      appendDebugNote({
        scope: 'app',
        title: 'Action link execution failed',
        detail: outcome.message,
        meta: {
          connectionId: outcome.parsed?.connectionId ?? null,
          sessionId: outcome.parsed?.sessionId ?? null,
          pluginId: outcome.parsed?.pluginId ?? null,
          callbackElementId: outcome.parsed?.callbackElementId ?? null,
          errorType: outcome.errorType,
        },
      });
      Alert.alert('Action Failed', outcome.message);
    },
    [appendDebugNote, connections, selectedConnectionId],
  );

  const handleIncomingUrl = useCallback(
    async (url: string | null | undefined) => {
      if (!url) {
        return;
      }
      await executeActionDeepLink(url);
    },
    [executeActionDeepLink],
  );

  useEffect(() => {
    if (
      !pendingActionDeepLink ||
      !backend ||
      pendingActionDeepLink.connectionId !== selectedConnectionId
    ) {
      return;
    }
    const parsed = pendingActionDeepLink;
    setPendingActionDeepLink(null);
    void executeActionDeepLink(parsed.redirectUrl);
  }, [backend, executeActionDeepLink, pendingActionDeepLink, selectedConnectionId]);

  useEffect(() => {
    if (!initialUrlHandledRef.current) {
      initialUrlHandledRef.current = true;
      Linking.getInitialURL()
        .then((url) => {
          void handleIncomingUrl(url);
        })
        .catch((error) => {
          appendDebugNote({
            scope: 'app',
            title: 'Initial URL read failed',
            detail: error?.message || String(error),
          });
        });
    }

    const subscription = Linking.addEventListener('url', (event) => {
      void handleIncomingUrl(event.url);
    });

    return () => {
      subscription.remove();
    };
  }, [appendDebugNote, handleIncomingUrl]);

  useEffect(() => {
    const loadSavedConnections = async () => {
      setConnectionsLoading(true);
      try {
        let records = await loadConnections(connectionsStore);
        if (Platform.OS === 'ios') {
          let configuration: EmbeddedRuntimePublicConfiguration | null = null;
          try {
            configuration = await getEmbeddedPythonRuntimeConfiguration();
          } catch (error) {
            appendDebugNote({
              scope: 'app',
              title: 'Embedded settings seed failed',
              detail: error instanceof Error ? error.message : String(error),
            });
          }
          const prior = records.find(
            (record): record is EmbeddedConnectionRecord =>
              record.id === EMBEDDED_CONNECTION_ID &&
              record.kind === 'embedded',
          );
          if (configuration) {
            records = [
              embeddedConnectionRecord(
                configuration,
                prior?.lastUsedAt ?? Date.now(),
              ),
              ...records.filter(
                (record) => record.id !== EMBEDDED_CONNECTION_ID,
              ),
            ];
          }
        }
        setConnections(records);
      } catch (err) {
        console.log('Failed to load saved connections', err);
      } finally {
        setConnectionsLoading(false);
      }
    };

    loadSavedConnections();
  }, [appendDebugNote]);

  useEffect(() => {
    const loadSessionsCache = async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY_SESSIONS_CACHE);
        if (!raw) {
          return;
        }
        try {
          const parsed = JSON.parse(raw) as SessionsCache;
          if (parsed && typeof parsed === 'object') {
            setSessionsCache(parsed);
          }
        } catch (err) {
          console.log('Failed to parse stored sessions cache', err);
        }
      } catch (err) {
        console.log('Failed to load sessions cache', err);
      }
    };

    loadSessionsCache();
  }, []);

  useEffect(() => {
    const save = async () => {
      if (connectionsLoading) {
        return;
      }
      try {
        await saveConnections(connectionsStore, connections);
      } catch (err) {
        console.log('Failed to save connections', err);
      }
    };

    save();
  }, [connections, connectionsLoading]);

  useEffect(() => {
    const saveSessions = async () => {
      try {
        await AsyncStorage.setItem(
          STORAGE_KEY_SESSIONS_CACHE,
          JSON.stringify(sessionsCache),
        );
      } catch (err) {
        console.log('Failed to save sessions cache', err);
      }
    };

    saveSessions();
  }, [sessionsCache]);

  const updateSessionsCache = (connectionId: string, list: SessionSummary[]) => {
    setSessionsCache((prev) => ({
      ...prev,
      [connectionId]: {
        connectionId,
        sessions: list,
        lastLoadedAt: Date.now(),
      },
    }));
  };

  const upsertConnection = useCallback((record: ConnectionRecord) => {
    setConnections((prev) => {
      const idx = prev.findIndex((r) => r.id === record.id);
      if (idx === -1) {
        return [...prev, record];
      }
      const next = [...prev];
      next[idx] = record;
      return next;
    });
  }, []);

  const connectionSetup = useConnectionSetup({
    transport,
    onConnected: (next, record, nextBackend) => {
      setTransport(next);
      setBackend(nextBackend ?? new RestAgentBackend({ transport: next }));
      upsertConnection(record);
      setSelectedConnectionId(record.id);
      if (isSearching) stopDiscovery();
      Keyboard.dismiss();
      setShowConnectionWizard(false);
      setConnectionMethod(null);
      setConnectingBridgeTransport(null);
      setBridgeServers([]);
      setSelectedBridgeServer(null);
      setPairingCode('');
      repairingBridgeRecordRef.current = null;
      setIsLoading(false);
    },
  });

  const openBridgeRepairFlow = useCallback(
    async (
      bridgeRecord: BridgeConnectionRecord,
      reasonCode: 'invalid_pairing_token' | 'server_not_found' | 'server_mismatch' | null,
    ) => {
      if (!developmentSettings.hydrated || !savedBridgeUrls.hydrated) return;
      connectionSetup.start();
      const ticket = connectionSetup.ticket();
      appendDebugNote({
        scope: 'app',
        title: 'Bridge repair flow opened',
        detail: reasonCode ?? 'manual_repair',
        meta: {
          connectionId: bridgeRecord.id,
          serverId: bridgeRecord.serverId,
        },
      });

      const bridge = createBridgeTransport({
        bridgeUrl: bridgeRecord.bridgeUrl,
        mode: resolveBridgeTransportMode(bridgeRecord, developmentSettings.mode),
        debug: true,
      });
      if (!connectionSetup.track(ticket, bridge)) return;
      await bridge.connect();
      const servers = await bridge.listServers();
      if (!connectionSetup.isCurrent(ticket)) return;
      await savedBridgeUrls.remember(bridgeRecord.bridgeUrl);
      if (!connectionSetup.isCurrent(ticket)) return;
      const preferredServer =
        servers.find((server) => server.server_id === bridgeRecord.serverId) ?? null;

      repairingBridgeRecordRef.current = bridgeRecord;
      setBridgeUrl(bridgeRecord.bridgeUrl);
      setBridgeServers(servers);
      setConnectingBridgeTransport(bridge);
      setPairingCode('');
      setShowConnectionWizard(true);
      setConnectionMethod('bridge');

      if (preferredServer) {
        await bridge.requestPairing(preferredServer.server_id);
        if (!connectionSetup.isCurrent(ticket)) return;
        setSelectedBridgeServer(preferredServer);
        Alert.alert(
          'Bridge Re-pair Required',
          reasonCode === 'server_not_found'
            ? 'The saved bridge server is reachable again, but the previous session could not be resumed. Enter a fresh pairing code to continue.'
            : 'The saved bridge pairing could not be resumed. Enter a fresh pairing code to continue.',
        );
        return;
      }

      setSelectedBridgeServer(null);
      Alert.alert(
        'Bridge Reconnect Needed',
        'The saved bridge session could not be resumed. Select an available server and pair again.',
      );
    },
    [appendDebugNote, developmentSettings.hydrated, developmentSettings.mode,
      savedBridgeUrls.hydrated, savedBridgeUrls.remember],
  );

  const handleAppForeground = useCallback(async () => {
    if (foregroundRecoveryInFlightRef.current) {
      return;
    }
    foregroundRecoveryInFlightRef.current = true;

    appendDebugNote({
      scope: 'app',
      title: 'App foregrounded',
      detail: activeConnection?.kind ?? 'no_active_connection',
      meta: {
        connectionId: activeConnection?.id ?? null,
      },
    });

    try {
      if (
        activeConnection?.kind !== 'bridge' ||
        !isBridgeConnectionTransport(transport)
      ) {
        return;
      }

      transport.prepareForResume();

      appendDebugNote({
        scope: 'app',
        title: 'Bridge reconnect started',
        detail: activeConnection.name,
        meta: {
          serverId: activeConnection.serverId,
        },
      });

      try {
        await transport.connect();
        appendDebugNote({
          scope: 'app',
          title: 'Bridge reconnect succeeded',
          detail: activeConnection.name,
          meta: {
            serverId: transport.getServerId(),
          },
        });

        const pairingToken = transport.getPairingToken();
        if (
          pairingToken &&
          pairingToken !== activeConnection.pairingToken
        ) {
          upsertConnection({
            ...activeConnection,
            pairingToken,
            lastUsedAt: Date.now(),
          });
        }
      } catch (error) {
        const reasonCode = getBridgeReconnectErrorCode(error);
        appendDebugNote({
          scope: 'app',
          title: 'Bridge reconnect failed',
          detail: error instanceof Error ? error.message : String(error),
          meta: {
            reasonCode,
            serverId: activeConnection.serverId,
          },
        });
        if (reasonCode) {
          if (reasonCode === 'invalid_pairing_token' || reasonCode === 'server_mismatch') {
            upsertConnection({
              ...activeConnection,
              pairingToken: null,
              lastUsedAt: Date.now(),
            });
          }
          await openBridgeRepairFlow(activeConnection, reasonCode);
          return;
        }
      }
    } finally {
      foregroundRecoveryInFlightRef.current = false;
    }
  }, [activeConnection, appendDebugNote, openBridgeRepairFlow, transport, upsertConnection]);

  useEffect(() => {
    const sub = AppState.addEventListener('change', (nextState) => {
      const previousState = appStateRef.current;
      appStateRef.current = nextState;
      if (Platform.OS === 'ios') {
        void noteEmbeddedPythonRuntimeAppState(nextState)
          .then((status) => {
            appendDebugNote({
              scope: 'app',
              title: 'Embedded runtime lifecycle updated',
              detail: status.state,
              meta: {
                backgroundTaskActive: status.backgroundTaskActive ?? false,
                requestId: status.requestId ?? null,
              },
            });
          })
          .catch((error) => {
            appendDebugNote({
              scope: 'app',
              title: 'Embedded runtime lifecycle update failed',
              detail: error instanceof Error ? error.message : String(error),
            });
          });
      }

      if (nextState === 'active') {
        if (previousState !== 'active') {
          void handleAppForeground();
        }
        return;
      }

      appendDebugNote({
        scope: 'app',
        title: 'App backgrounded',
        detail: nextState,
        meta: {
          activeConnectionId: activeConnection?.id ?? null,
        },
      });
      disconnectIfPossible(transport);
      disconnectIfPossible(connectingBridgeTransport);
    });

    return () => {
      sub.remove();
    };
  }, [
    activeConnection?.id,
    appendDebugNote,
    connectingBridgeTransport,
    handleAppForeground,
    transport,
  ]);

  useEffect(() => {
    if (connectionMethod !== 'embedded' || Platform.OS !== 'ios') {
      return;
    }
    let active = true;
    void getEmbeddedPythonRuntimeConfiguration()
      .then((configuration) => {
        if (!active) return;
        if (configuration.proxyUrl) {
          setEmbeddedProxyUrl(configuration.proxyUrl);
        }
        if (configuration.model) {
          setEmbeddedModel(configuration.model);
        }
        setEmbeddedHasSavedApiKey(configuration.hasApiKey);
      })
      .catch((error) => {
        appendDebugNote({
          scope: 'app',
          title: 'Embedded runtime configuration load failed',
          detail: error instanceof Error ? error.message : String(error),
        });
      });
    return () => {
      active = false;
    };
  }, [appendDebugNote, connectionMethod]);

  useEffect(() => {
    zeroconf.on('resolved', (service: any) => {
      console.log('🔍 Service resolved:', service);
      const newService: Service = {
        name: service.name,
        host: service.host || service.addresses?.[0] || 'unknown',
        port: service.port,
        addresses: service.addresses || [],
      };
      
      setDiscoveredServices(prev => {
        const exists = prev.some(s => s.name === newService.name);
        if (exists) return prev;
        return [...prev, newService];
      });
    });

    zeroconf.on('error', (error: any) => {
      console.log('❌ Error:', error);
      Alert.alert('Discovery Error', error.toString());
    });

    return () => {
      zeroconf.stop();
      zeroconf.removeAllListeners();
    };
  }, [zeroconf]);

  const selectMethod = (method: ConnectionMethod) => {
    setConnectionMethod(method);
    if (method === 'discovery') {
      startDiscovery();
    }
  };

  const cancelConnectionWizard = () => {
    Keyboard.dismiss();
    connectionSetup.cancel();
    repairingBridgeRecordRef.current = null;
    setIsLoading(false);
    setConnectingBridgeTransport(null);
    if (isSearching) {
      stopDiscovery();
    }
    setConnectionMethod(null);
    setShowConnectionWizard(false);
    setDiscoveredServices([]);
    setBridgeServers([]);
    setSelectedBridgeServer(null);
    setPairingCode('');
    setCloudConnectionLink('');
  };

  const startDiscovery = () => {
    console.log('🔍 Starting discovery...');
    setDiscoveredServices([]);
    setIsSearching(true);
    zeroconf.scan('http', 'tcp', 'local.');
  };

  const stopDiscovery = () => {
    console.log('⏹️ Stopping discovery...');
    setIsSearching(false);
    zeroconf.stop();
  };

  const connectManual = async () => {
    if (!manualHost || !manualPort) {
      Alert.alert('Error', 'Please enter both host and port');
      return;
    }

    const ticket = connectionSetup.ticket();
    setIsLoading(true);
    try {
      appendDebugNote({
        scope: 'app',
        title: 'Manual connection started',
        detail: `${manualHost}:${manualPort}`,
      });
      const port = parseInt(manualPort, 10);
      const baseUrl = `http://${manualHost}:${port}`;
      const nextTransport = createHttpTransport(baseUrl);
      if (!connectionSetup.track(ticket, nextTransport)) return;
      await nextTransport.request({ method: 'GET', path: '/api/data' });
      const id = generateId();
      const record: ManualConnectionRecord = {
        id,
        kind: 'manual',
        name: `${manualHost}:${manualPort}`,
        host: manualHost,
        port,
        lastUsedAt: Date.now(),
      };
      if (!connectionSetup.complete(ticket, nextTransport, record)) return;
      appendDebugNote({
        scope: 'app',
        title: 'Manual connection succeeded',
        detail: `${manualHost}:${manualPort}`,
      });
    } catch (error: any) {
      if (!connectionSetup.isCurrent(ticket)) return;
      connectionSetup.fail(ticket);
      appendDebugNote({
        scope: 'app',
        title: 'Manual connection failed',
        detail: error?.message || 'connection_error',
      });
      Alert.alert('Connection Error', error.message);
    } finally {
      if (connectionSetup.isCurrent(ticket)) setIsLoading(false);
    }
  };

  const connectEmbedded = async () => {
    const proxyUrl = embeddedProxyUrl.trim();
    const model = embeddedModel.trim();
    if (!proxyUrl || !model) {
      Alert.alert('Error', 'Please enter both proxy URL and model');
      return;
    }
    if (!embeddedApiKey && !embeddedHasSavedApiKey) {
      Alert.alert('Error', 'Please enter the proxy API key');
      return;
    }

    const ticket = connectionSetup.ticket();
    setIsLoading(true);
    try {
      appendDebugNote({
        scope: 'app',
        title: 'Embedded runtime connection started',
        detail: model,
        meta: { proxyUrl },
      });
      const configuration = await configureEmbeddedPythonRuntime({
        proxyUrl,
        model,
        ...(embeddedApiKey ? { apiKey: embeddedApiKey } : {}),
      });
      const embedded = createEmbeddedRuntimeBackend();
      if (!connectionSetup.track(ticket, embedded.transport)) return;
      await embedded.transport.request({
        method: 'POST',
        path: '/embedded/runtime/validate',
      });
      await embedded.backend.listAgents();
      const record: EmbeddedConnectionRecord = {
        id: EMBEDDED_CONNECTION_ID,
        kind: 'embedded',
        name: 'Local agent',
        proxyUrl: configuration.proxyUrl,
        model: configuration.model,
        lastUsedAt: Date.now(),
      };
      if (!connectionSetup.complete(ticket, embedded.transport, record, embedded.backend)) return;
      setEmbeddedApiKey('');
      setEmbeddedHasSavedApiKey(configuration.hasApiKey);
      appendDebugNote({
        scope: 'app',
        title: 'Embedded runtime connection succeeded',
        detail: configuration.model,
        meta: { proxyUrl: configuration.proxyUrl },
      });
    } catch (error: any) {
      if (!connectionSetup.isCurrent(ticket)) return;
      connectionSetup.fail(ticket);
      appendDebugNote({
        scope: 'app',
        title: 'Embedded runtime connection failed',
        detail: error?.message || 'connection_error',
      });
      Alert.alert(
        'Embedded Runtime Error',
        error?.message || 'Could not start the embedded runtime',
      );
    } finally {
      if (connectionSetup.isCurrent(ticket)) setIsLoading(false);
    }
  };

  const connectToService = async (service: Service) => {
    const ticket = connectionSetup.ticket();
    setIsLoading(true);
    try {
      appendDebugNote({
        scope: 'app',
        title: 'Discovery connection started',
        detail: `${service.host}:${service.port}`,
      });
      const baseUrl = `http://${service.host}:${service.port}`;
      const nextTransport = createHttpTransport(baseUrl);
      if (!connectionSetup.track(ticket, nextTransport)) return;
      await nextTransport.request({ method: 'GET', path: '/api/data' });
      const id = generateId();
      const record: DiscoveryConnectionRecord = {
        id,
        kind: 'discovery',
        name: service.name,
        host: service.host,
        port: service.port,
        serviceName: service.name,
        lastUsedAt: Date.now(),
      };
      if (!connectionSetup.complete(ticket, nextTransport, record)) return;
      appendDebugNote({
        scope: 'app',
        title: 'Discovery connection succeeded',
        detail: service.name,
      });
    } catch (error: any) {
      if (!connectionSetup.isCurrent(ticket)) return;
      connectionSetup.fail(ticket);
      appendDebugNote({
        scope: 'app',
        title: 'Discovery connection failed',
        detail: error?.message || 'connection_error',
      });
      Alert.alert('Connection Error', error.message);
    } finally {
      if (connectionSetup.isCurrent(ticket)) setIsLoading(false);
    }
  };

  const connectToBridge = async (input = bridgeUrl) => {
    const url = input.trim();
    if (!url) {
      Alert.alert('Error', 'Please enter a bridge address');
      return;
    }

    try {
      normalizeBridgeAddress(url);
    } catch (error) {
      Alert.alert('Invalid Bridge Address', error instanceof Error ? error.message : String(error));
      return;
    }

    const ticket = connectionSetup.ticket();
    if (!developmentSettings.hydrated || !savedBridgeUrls.hydrated) return;
    setBridgeUrl(url);
    setIsLoading(true);
    try {
      console.log('🚀 Starting bridge connection...');
      appendDebugNote({
        scope: 'app',
        title: 'Bridge connection started',
        detail: url,
      });
      
      const bridge = createBridgeTransport({
        bridgeUrl: url,
        mode: developmentSettings.mode,
        debug: true,
      });
      if (!connectionSetup.track(ticket, bridge)) return;
      await bridge.connect();
      if (!connectionSetup.isCurrent(ticket)) return;
      console.log('✅ Bridge connected, fetching servers...');
      
      const servers = await bridge.listServers();
      if (!connectionSetup.isCurrent(ticket)) return;
      await savedBridgeUrls.remember(url);
      if (!connectionSetup.isCurrent(ticket)) return;
      setConnectingBridgeTransport(bridge);
      console.log(`📋 Found ${servers.length} servers:`, servers);
      setBridgeServers(servers);
      
      if (servers.length === 0) {
        Alert.alert('No Servers', 'No servers available on bridge. Make sure servers are started with --bridge flag.');
      }
      appendDebugNote({
        scope: 'app',
        title: 'Bridge connection ready',
        detail: `${servers.length} server(s) discovered`,
      });
    } catch (error: any) {
      if (!connectionSetup.isCurrent(ticket)) return;
      connectionSetup.fail(ticket);
      console.log('❌ Bridge connection failed:', error);
      appendDebugNote({
        scope: 'app',
        title: 'Bridge connection failed',
        detail: error?.message || 'bridge_error',
      });
      Alert.alert(
        'Bridge Connection Error',
        bridgeConnectionErrorMessage(error),
        [{ text: 'OK' }]
      );
      setConnectingBridgeTransport(null);
    } finally {
      if (connectionSetup.isCurrent(ticket)) setIsLoading(false);
    }
  };

  const requestPairing = async (server: BridgeServer) => {
    if (!connectingBridgeTransport) return;

    const ticket = connectionSetup.ticket();
    setSelectedBridgeServer(server);
    setIsLoading(true);
    try {
      await connectingBridgeTransport.requestPairing(server.server_id);
      if (!connectionSetup.isCurrent(ticket)) return;
      Alert.alert(
        'Pairing Requested',
        'Check the server terminal for the 6-digit pairing code',
        [{ text: 'OK' }]
      );
    } catch (error: any) {
      if (!connectionSetup.isCurrent(ticket)) return;
      Alert.alert('Pairing Error', error.message);
    } finally {
      if (connectionSetup.isCurrent(ticket)) setIsLoading(false);
    }
  };

  const submitPairing = async () => {
    if (!connectingBridgeTransport || !selectedBridgeServer || !pairingCode) {
      Alert.alert('Error', 'Please enter pairing code');
      return;
    }

    const ticket = connectionSetup.ticket();
    setIsLoading(true);
    try {
      await connectingBridgeTransport.submitPairingCode(
        selectedBridgeServer.server_id,
        pairingCode
      );

      const repaired = repairingBridgeRecordRef.current;
      const id = repaired?.serverId === selectedBridgeServer.server_id ? repaired.id : generateId();
      const record: BridgeConnectionRecord = {
        id,
        kind: 'bridge',
        name: selectedBridgeServer.display_name,
        bridgeUrl,
        serverId: selectedBridgeServer.server_id,
        serverName: selectedBridgeServer.display_name,
        pairingToken: connectingBridgeTransport.getPairingToken(),
        transportMode: DEFAULT_BRIDGE_TRANSPORT_MODE,
        lastUsedAt: Date.now(),
      };
      if (!connectionSetup.isCurrent(ticket)) return;
      await savedBridgeUrls.remember(bridgeUrl);
      connectionSetup.complete(ticket, connectingBridgeTransport, record);
    } catch (error: any) {
      if (!connectionSetup.isCurrent(ticket)) return;
      Alert.alert('Pairing Failed', error.message);
    } finally {
      if (connectionSetup.isCurrent(ticket)) setIsLoading(false);
    }
  };

  const connectCloud = async () => {
    if (!cloudConnectionLink.trim()) {
      Alert.alert('Error', 'Please paste a cloud connection link');
      return;
    }

    const ticket = connectionSetup.ticket();
    setIsLoading(true);
    try {
      const parsed = parseCloudConnectionLink(cloudConnectionLink.trim());
      const nextTransport = new CloudTransport({
        orchestratorUrl: parsed.orchestratorUrl,
        connectionId: parsed.connectionId,
        instanceId: parsed.instanceId,
        token: parsed.token,
        defaultRequestTimeoutMs: DEFAULT_REQUEST_TIMEOUT_MS,
        timeoutRules: TRANSPORT_TIMEOUT_RULES,
      });
      if (!connectionSetup.track(ticket, nextTransport)) return;
      await nextTransport.request({ method: 'GET', path: '/api/data' });

      const id = generateId();
      const record: CloudConnectionRecord = {
        id,
        kind: 'cloud',
        name: `Cloud ${parsed.sessionId || parsed.connectionId || parsed.instanceId}`,
        orchestratorUrl: parsed.orchestratorUrl,
        connectionId: parsed.connectionId,
        instanceId: parsed.instanceId,
        initialSessionId: parsed.sessionId,
        sessionId: parsed.sessionId,
        token: parsed.token,
        lastUsedAt: Date.now(),
      };
      if (!connectionSetup.complete(ticket, nextTransport, record)) return;
      setCloudConnectionLink('');
    } catch (error: any) {
      if (!connectionSetup.isCurrent(ticket)) return;
      connectionSetup.fail(ticket);
      Alert.alert('Cloud Connection Error', error?.message || 'Could not connect to cloud agent');
    } finally {
      if (connectionSetup.isCurrent(ticket)) setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    appendDebugNote({
      scope: 'app',
      title: 'Disconnected active connection',
      detail: selectedConnectionId ?? 'manual_disconnect',
    });
    disconnectIfPossible(transport);
    disconnectIfPossible(connectingBridgeTransport);
    setTransport(null);
    setBackend(null);
    setConnectingBridgeTransport(null);
    cancelConnectionWizard();
  };

  const handleDeleteConnection = (record: ConnectionRecord) => {
    if (record.kind === 'embedded') {
      Alert.alert(
        'Built-in Connection',
        'The on-device Python connection is always available on iOS.',
      );
      return;
    }
    setConnections((prev) => prev.filter((r) => r.id !== record.id));

    setSessionsCache((prev) => {
      if (!prev[record.id]) {
        return prev;
      }
      const next = { ...prev };
      delete next[record.id];
      return next;
    });

    deleteConnectionMessagesCache(record.id);

    if (selectedConnectionId === record.id) {
      disconnectIfPossible(transport);
      setTransport(null);
      setBackend(null);
      setSelectedConnectionId(null);
    }
  };

  const renderMethodSelection = () => (
    <ConnectionMethodStep onSelect={selectMethod} onCancel={cancelConnectionWizard} />
  );

  const renderEmbeddedConnection = () => (
    <EmbeddedConnectionStep
      proxyUrl={embeddedProxyUrl} model={embeddedModel} apiKey={embeddedApiKey}
      hasKey={embeddedHasSavedApiKey} onProxyUrl={setEmbeddedProxyUrl}
      onModel={setEmbeddedModel} onApiKey={setEmbeddedApiKey}
      onConnect={connectEmbedded} onCancel={cancelConnectionWizard} loading={isLoading}
    />
  );

  const renderManualConnection = () => (
    <ManualConnectionStep
      host={manualHost} port={manualPort} onHost={setManualHost} onPort={setManualPort}
      onConnect={connectManual} onCancel={cancelConnectionWizard} loading={isLoading}
    />
  );

  const renderDiscoveryConnection = () => (
    <DiscoveryConnectionStep
      searching={isSearching} services={discoveredServices}
      onConnect={connectToService} onCancel={cancelConnectionWizard} loading={isLoading}
    />
  );

  const testBridgeConnectivity = async () => {
    if (!bridgeUrl) return;

    let httpUrl: string;
    try {
      httpUrl = `${deriveBridgeHttpBaseUrl(bridgeUrl)}/health`;
    } catch (error) {
      Alert.alert('Invalid Bridge Address', error instanceof Error ? error.message : String(error));
      return;
    }

    setIsLoading(true);
    try {
      console.log('🧪 Testing HTTP connectivity:', httpUrl);
      const response = await fetch(httpUrl, {
        method: 'GET',
        timeout: 5000,
      } as any);
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Bridge HTTP reachable:', data);
        Alert.alert(
          'Bridge Reachable',
          `Bridge is running!\n\nStatus: ${data.status || 'ok'}\n\nYou can now connect to the bridge.`,
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert('Bridge HTTP Error', `HTTP status: ${response.status}`);
      }
    } catch (error: any) {
      console.log('❌ Bridge HTTP test failed:', error);
      Alert.alert(
        'Cannot Reach Bridge',
        `The bridge server is not reachable.\n\nTested: ${httpUrl}\n\nError: ${error.message}\n\nPlease check:\n1. Bridge is running\n2. IP address is correct\n3. Device can reach the network`,
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const renderBridgeConnection = () => (
    <BridgeConnectionStep
      url={bridgeUrl} savedBridges={savedBridgeUrls.bridges} servers={bridgeServers}
      connected={connectingBridgeTransport !== null} selectedServer={selectedBridgeServer}
      code={pairingCode}
      loading={isLoading || !developmentSettings.hydrated || !savedBridgeUrls.hydrated}
      storageError={savedBridgeUrls.error?.message ?? developmentSettings.error?.message}
      onUrl={setBridgeUrl} onCode={setPairingCode}
      onConnect={() => { void connectToBridge(); }} onTest={testBridgeConnectivity}
      onSelectSaved={(url) => { void connectToBridge(url); }}
      onRemoveSaved={(url) => {
        void savedBridgeUrls.remove(url).catch((error) => {
          Alert.alert('Saved Bridge Error', error.message);
        });
      }}
      onPair={requestPairing} onSubmit={submitPairing}
      onCancelPairing={() => setSelectedBridgeServer(null)} onCancel={cancelConnectionWizard}
    />
  );

  const renderCloudConnection = () => (
    <CloudConnectionStep
      link={cloudConnectionLink} onLink={setCloudConnectionLink}
      onConnect={connectCloud} onCancel={cancelConnectionWizard} loading={isLoading}
    />
  );

  const renderConnectingScreen = () => {
    if (connectionMethod === 'embedded') return renderEmbeddedConnection();
    if (connectionMethod === 'manual') return renderManualConnection();
    if (connectionMethod === 'discovery') return renderDiscoveryConnection();
    if (connectionMethod === 'bridge') return renderBridgeConnection();
    if (connectionMethod === 'cloud') return renderCloudConnection();
    return null;
  };

  const handleSelectSavedConnection = async (
    record: ConnectionRecord,
  ): Promise<boolean> => {
    setIsLoading(true);
    let nextTransport: Transport | null = null;
    let nextBackend: AgentBackend | null = null;
    try {
      appendDebugNote({
        scope: 'app',
        title: 'Connection selected',
        detail: record.kind,
        meta: {
          connectionId: record.id,
          name: record.name,
        },
      });

      if (record.kind === 'embedded') {
        const embedded = createEmbeddedRuntimeBackend();
        await embedded.backend.listAgents();
        nextTransport = embedded.transport;
        nextBackend = embedded.backend;
      } else if (record.kind === 'manual' || record.kind === 'discovery') {
        const baseUrl = `http://${record.host}:${record.port}`;
        const httpTransport = createHttpTransport(baseUrl);
        await httpTransport.request({ method: 'GET', path: '/api/data' });
        nextTransport = httpTransport;
      } else if (record.kind === 'bridge') {
        if (!developmentSettings.hydrated || !savedBridgeUrls.hydrated) return false;
        if (!record.pairingToken) {
          await openBridgeRepairFlow(record, null);
          return false;
        }

        const bridge = createBridgeTransport({
          ...getSavedBridgeTransportOptions(record, developmentSettings.mode),
          debug: true,
        });
        try {
          await bridge.connect();
        } catch (error) {
          bridge.disconnect();
          const reasonCode = getBridgeReconnectErrorCode(error);
          if (reasonCode) {
            if (reasonCode === 'invalid_pairing_token' || reasonCode === 'server_mismatch') {
              upsertConnection({
                ...record,
                pairingToken: null,
                lastUsedAt: Date.now(),
              });
            }
            await openBridgeRepairFlow(record, reasonCode);
            return false;
          }
          throw error;
        }
        nextTransport = bridge;
        await savedBridgeUrls.remember(record.bridgeUrl);
      } else if (record.kind === 'cloud') {
        const cloud = createCloudTransport(record);
        await cloud.request({ method: 'GET', path: '/api/data' });
        nextTransport = cloud;
      }

      if (nextTransport) {
        setTransport(nextTransport);
        setBackend(nextBackend ?? new RestAgentBackend({ transport: nextTransport }));
        setSelectedConnectionId(record.id);
        upsertConnection({ ...record, lastUsedAt: Date.now() });
        if (nextTransport !== transport) disconnectIfPossible(transport);
        appendDebugNote({
          scope: 'app',
          title: 'Connection activated',
          detail: record.kind,
          meta: {
            connectionId: record.id,
          },
        });
        return true;
      }
      return false;
    } catch (error: any) {
      if (nextTransport !== transport) disconnectIfPossible(nextTransport);
      console.log('Failed to reconnect to saved connection', error);
      Alert.alert('Connection Error', record.kind === 'bridge'
        ? bridgeConnectionErrorMessage(error)
        : error?.message || 'Failed to reconnect');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const splashBg = colorScheme === 'dark' ? '#000000' : '#F2F2F7';

  return (
    <GestureHandlerRootView style={[styles.gestureRoot, { backgroundColor: splashBg }]}>
      <SafeAreaProvider>
        <ThemeProvider theme={theme}>
          <MarkdownDisplayPreferencesProvider
            value={markdownDisplayPreferences}
            onChange={setMarkdownDisplayPreferences}
          >
          <PinnedActionsProvider>
          <HomeWorkspaceProvider>
            {isAppLoading || !markdownDisplayPreferencesHydrated ||
              (!developmentSettings.hydrated && !developmentSettings.error) ||
              (!savedBridgeUrls.hydrated && !savedBridgeUrls.error) ? (
              <AnimatedSplashScreen />
            ) : (
              <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
                <StatusBar barStyle={colorScheme === 'dark' ? 'light-content' : 'dark-content'} />
                {/** Determine active connection info for display components */}
                {/** This is derived once here and passed down rather than recomputed in children. */}
                {(() => {
                  return (
                    <ConnectedRoot
                      developmentSettings={developmentSettings}
                      backend={backend}
                      transport={transport}
                      onDisconnect={handleDisconnect}
                      connections={connections}
                      connectionsLoading={connectionsLoading}
                      onSelectConnectionRecord={handleSelectSavedConnection}
                      onNewConnectionRequested={() => {
                        cancelConnectionWizard();
                        setConnectionMethod(null);
                        setShowConnectionWizard(true);
                      }}
                      onCloseConnectionWizard={cancelConnectionWizard}
                      renderConnectionWizard={() => {
                        if (!showConnectionWizard) {
                          return null;
                        }
                        if (!connectionMethod) {
                          return renderMethodSelection();
                        }
                        return renderConnectingScreen();
                      }}
                      onDeleteConnectionRecord={handleDeleteConnection}
                      activeConnectionId={selectedConnectionId}
                      sessionsCache={sessionsCache}
                      onUpdateSessionsCache={updateSessionsCache}
                      messagesCache={messagesCache}
                      onUpdateMessagesCache={updateMessagesCache}
                      onSaveMessagesComposeText={saveMessagesComposeText}
                      onSaveMessagesScrollAnchor={saveMessagesScrollAnchor}
                      onSaveMessagesHistoryRange={saveMessagesHistoryRange}
                      debugTimeline={debugTimeline}
                      onAppendDebugTimelineEntry={appendDebugNote}
                      onEmbeddedSettingsChanged={(configuration) => {
                        const prior = connections.find(
                          (record) =>
                            record.id === EMBEDDED_CONNECTION_ID &&
                            record.kind === 'embedded',
                        );
                        const updatedRecord = embeddedConnectionRecord(
                          configuration,
                          prior?.lastUsedAt ?? Date.now(),
                        );
                        upsertConnection(updatedRecord);
                        invalidateAgentsCache(EMBEDDED_CONNECTION_ID);
                        if (selectedConnectionId === EMBEDDED_CONNECTION_ID) {
                          void handleSelectSavedConnection(updatedRecord);
                        }
                      }}
                    />
                  );
                })()}
              </SafeAreaView>
            )}
          </HomeWorkspaceProvider>
          </PinnedActionsProvider>
          </MarkdownDisplayPreferencesProvider>
        </ThemeProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
const createStyles = (theme: Theme) =>
  StyleSheet.create({
    gestureRoot: {
      flex: 1,
    },
    safeArea: {
      flex: 1,
      backgroundColor: theme.background,
    },
  });

export default App;
