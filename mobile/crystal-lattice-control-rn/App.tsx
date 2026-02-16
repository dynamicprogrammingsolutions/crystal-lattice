import 'react-native-url-polyfill/auto';
import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  useColorScheme,
  Alert,
  TextInput,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Zeroconf from 'react-native-zeroconf';
import {
  BridgeTransport,
  FetchTransport,
  type KeyValueStore,
  loadConnections,
  RestAgentBackend,
  saveConnections,
  type AgentBackend,
  type BridgeServer,
  type BridgeConnectionRecord,
  type ConnectionRecord,
  type DiscoveryConnectionRecord,
  type ManualConnectionRecord,
  type Transport,
} from '@crystal-lattice/frontend-sdk';
import ConnectedRoot from './src/ConnectedRoot';
import { getConnectionAdditionalInfo } from './src/connectionInfo';
import type { SessionSummary, IndexedMessage } from './src/api';
import type { ChatScrollAnchor } from './src/chatScroll';
import { ThemeProvider, lightTheme, darkTheme, type Theme } from './src/theme';
import { PinnedActionsProvider } from './src/PinnedActionsContext';

type ConnectionMethod = 'manual' | 'discovery' | 'bridge';

interface Service {
  name: string;
  host: string;
  port: number;
  addresses: string[];
}

const connectionsStore: KeyValueStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};
const STORAGE_KEY_SESSIONS_CACHE = 'clc_sessions_cache_v1';
const STORAGE_KEY_MESSAGES_CACHE = 'clc_messages_cache_v1';

export interface SessionsCacheEntry {
  connectionId: string;
  sessions: SessionSummary[];
  lastLoadedAt: number | null;
}

export type SessionsCache = Record<string, SessionsCacheEntry>;

export interface MessagesCacheEntry {
  connectionId: string;
  sessionId: string;
  messages: IndexedMessage[];
  lastLoadedAt: number | null;
  eventsCursorId?: string | null;
  cursorEventId?: string | null;
  activeRequestId?: string | null;
  composeText?: string;
  scrollAnchor?: ChatScrollAnchor;
}

export type MessagesBySession = Record<string, MessagesCacheEntry>;
export type MessagesCache = Record<string, MessagesBySession>;

function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    // eslint-disable-next-line no-bitwise
    const r = (Math.random() * 16) | 0;
    // eslint-disable-next-line no-bitwise
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function App(): React.JSX.Element {
  const colorScheme = useColorScheme();
  const theme = colorScheme === 'dark' ? darkTheme : lightTheme;

  const [connectionMethod, setConnectionMethod] = useState<ConnectionMethod | null>(null);
  const [showConnectionWizard, setShowConnectionWizard] = useState(false);
  const [transport, setTransport] = useState<Transport | null>(null);
  const [backend, setBackend] = useState<AgentBackend | null>(null);
  const [connections, setConnections] = useState<ConnectionRecord[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null);
  const [connectionsLoading, setConnectionsLoading] = useState(false);
  const [sessionsCache, setSessionsCache] = useState<SessionsCache>({});
  const [messagesCache, setMessagesCache] = useState<MessagesCache>({});
  
  const [isSearching, setIsSearching] = useState(false);
  const [discoveredServices, setDiscoveredServices] = useState<Service[]>([]);
  const zeroconf = useRef(new Zeroconf()).current;

  const [manualHost, setManualHost] = useState('');
  const [manualPort, setManualPort] = useState('8080');

  const [bridgeUrl, setBridgeUrl] = useState('');
  const [bridgeServers, setBridgeServers] = useState<BridgeServer[]>([]);
  const [selectedBridgeServer, setSelectedBridgeServer] = useState<BridgeServer | null>(null);
  const [pairingCode, setPairingCode] = useState('');
  const [connectingBridgeTransport, setConnectingBridgeTransport] = useState<BridgeTransport | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const styles = useMemo(() => createStyles(theme), [theme]);

  useEffect(() => {
    const loadSavedConnections = async () => {
      setConnectionsLoading(true);
      try {
        const records = await loadConnections(connectionsStore);
        setConnections(records);
      } catch (err) {
        console.log('Failed to load saved connections', err);
      } finally {
        setConnectionsLoading(false);
      }
    };

    loadSavedConnections();
  }, []);

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
    const loadMessagesCache = async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY_MESSAGES_CACHE);
        if (!raw) {
          return;
        }
        try {
          const parsed = JSON.parse(raw) as MessagesCache;
          if (parsed && typeof parsed === 'object') {
            setMessagesCache(parsed);
          }
        } catch (err) {
          console.log('Failed to parse stored messages cache', err);
        }
      } catch (err) {
        console.log('Failed to load messages cache', err);
      }
    };

    loadMessagesCache();
  }, []);

  useEffect(() => {
    const save = async () => {
      try {
        await saveConnections(connectionsStore, connections);
      } catch (err) {
        console.log('Failed to save connections', err);
      }
    };

    save();
  }, [connections]);

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

  useEffect(() => {
    const saveMessages = async () => {
      try {
        await AsyncStorage.setItem(
          STORAGE_KEY_MESSAGES_CACHE,
          JSON.stringify(messagesCache),
        );
      } catch (err) {
        console.log('Failed to save messages cache', err);
      }
    };

    saveMessages();
  }, [messagesCache]);

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

  const updateMessagesCache = (
    connectionId: string,
    sessionId: string,
    list: IndexedMessage[],
    eventsCursorId: string | null,
    activeRequestId: string | null,
  ) => {
    setMessagesCache((prev) => {
      const bySession = prev[connectionId] ?? {};

      const existing = bySession[sessionId];

      const entry: MessagesCacheEntry = {
        ...(existing ?? {}),
        connectionId,
        sessionId,
        messages: list,
        lastLoadedAt: Date.now(),
        eventsCursorId,
        activeRequestId,
      };

      const nextBySession: MessagesBySession = { ...bySession, [sessionId]: entry };

      const MAX_SESSIONS_PER_CONNECTION = 10;
      const sessionIds = Object.keys(nextBySession);
      if (sessionIds.length > MAX_SESSIONS_PER_CONNECTION) {
        const sortedByAge = sessionIds
          .map((id) => nextBySession[id])
          .sort((a, b) => (a.lastLoadedAt ?? 0) - (b.lastLoadedAt ?? 0));
        const toDrop = sortedByAge.slice(
          0,
          sessionIds.length - MAX_SESSIONS_PER_CONNECTION,
        );
        for (const old of toDrop) {
          delete nextBySession[old.sessionId];
        }
      }

      return {
        ...prev,
        [connectionId]: nextBySession,
      };
    });
  };

  const upsertConnection = (record: ConnectionRecord) => {
    setConnections((prev) => {
      const idx = prev.findIndex((r) => r.id === record.id);
      if (idx === -1) {
        return [...prev, record];
      }
      const next = [...prev];
      next[idx] = record;
      return next;
    });
  };

  const saveMessagesComposeText = (
    connectionId: string,
    sessionId: string,
    composeText: string,
  ) => {
    setMessagesCache((prev) => {
      const bySession = prev[connectionId] ?? {};
      const existing = bySession[sessionId];

      const entry: MessagesCacheEntry = existing
        ? {
            ...existing,
            composeText,
          }
        : {
            connectionId,
            sessionId,
            messages: [],
            lastLoadedAt: null,
            composeText,
          };

      return {
        ...prev,
        [connectionId]: {
          ...bySession,
          [sessionId]: entry,
        },
      };
    });
  };

  const saveMessagesScrollAnchor = (
    connectionId: string,
    sessionId: string,
    scrollAnchor: ChatScrollAnchor,
  ) => {
    setMessagesCache((prev) => {
      const bySession = prev[connectionId] ?? {};
      const existing = bySession[sessionId];

      const entry: MessagesCacheEntry = existing
        ? {
            ...existing,
            scrollAnchor,
          }
        : {
            connectionId,
            sessionId,
            messages: [],
            lastLoadedAt: null,
            composeText: '',
            scrollAnchor,
          };

      return {
        ...prev,
        [connectionId]: {
          ...bySession,
          [sessionId]: entry,
        },
      };
    });
  };

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
    if (isSearching) {
      stopDiscovery();
    }
    setConnectionMethod(null);
    setShowConnectionWizard(false);
    setDiscoveredServices([]);
    setBridgeServers([]);
    setSelectedBridgeServer(null);
    setPairingCode('');
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

    setIsLoading(true);
    try {
      const port = parseInt(manualPort, 10);
      const baseUrl = `http://${manualHost}:${port}`;
      const nextTransport = new FetchTransport({ baseUrl });
      await nextTransport.request({ method: 'GET', path: '/api/data' });
      setTransport(nextTransport);
      setBackend(new RestAgentBackend({ transport: nextTransport }));
      const id = generateId();
      const record: ManualConnectionRecord = {
        id,
        kind: 'manual',
        name: `${manualHost}:${manualPort}`,
        host: manualHost,
        port,
        lastUsedAt: Date.now(),
      };
      upsertConnection(record);
      setSelectedConnectionId(id);
      setShowConnectionWizard(false);
      setConnectionMethod(null);
    } catch (error: any) {
      Alert.alert('Connection Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const connectToService = async (service: Service) => {
    setIsLoading(true);
    try {
      const baseUrl = `http://${service.host}:${service.port}`;
      const nextTransport = new FetchTransport({ baseUrl });
      await nextTransport.request({ method: 'GET', path: '/api/data' });
      setTransport(nextTransport);
      setBackend(new RestAgentBackend({ transport: nextTransport }));
      stopDiscovery();
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
      upsertConnection(record);
      setSelectedConnectionId(id);
      setShowConnectionWizard(false);
      setConnectionMethod(null);
    } catch (error: any) {
      Alert.alert('Connection Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const connectToBridge = async () => {
    if (!bridgeUrl) {
      Alert.alert('Error', 'Please enter bridge URL');
      return;
    }

    if (!bridgeUrl.startsWith('ws://') && !bridgeUrl.startsWith('wss://')) {
      Alert.alert('Invalid URL', 'Bridge URL must start with ws:// or wss://');
      return;
    }

    setIsLoading(true);
    try {
      console.log('🚀 Starting bridge connection...');
      
      const bridge = new BridgeTransport({ bridgeUrl, debug: true });
      await bridge.connect();
      console.log('✅ Bridge connected, fetching servers...');
      
      setConnectingBridgeTransport(bridge);
      
      const servers = await bridge.listServers();
      console.log(`📋 Found ${servers.length} servers:`, servers);
      setBridgeServers(servers);
      
      if (servers.length === 0) {
        Alert.alert('No Servers', 'No servers available on bridge. Make sure servers are started with --bridge flag.');
      }
    } catch (error: any) {
      console.log('❌ Bridge connection failed:', error);
      Alert.alert(
        'Bridge Connection Error',
        error.message,
        [{ text: 'OK' }]
      );
      setConnectingBridgeTransport(null);
    } finally {
      setIsLoading(false);
    }
  };

  const requestPairing = async (server: BridgeServer) => {
    if (!connectingBridgeTransport) return;

    setSelectedBridgeServer(server);
    setIsLoading(true);
    try {
      await connectingBridgeTransport.requestPairing(server.server_id);
      Alert.alert(
        'Pairing Requested',
        'Check the server terminal for the 6-digit pairing code',
        [{ text: 'OK' }]
      );
    } catch (error: any) {
      Alert.alert('Pairing Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const submitPairing = async () => {
    if (!connectingBridgeTransport || !selectedBridgeServer || !pairingCode) {
      Alert.alert('Error', 'Please enter pairing code');
      return;
    }

    setIsLoading(true);
    try {
      await connectingBridgeTransport.submitPairingCode(
        selectedBridgeServer.server_id,
        pairingCode
      );

      setTransport(connectingBridgeTransport);
      setBackend(new RestAgentBackend({ transport: connectingBridgeTransport }));
      const id = generateId();
      const record: BridgeConnectionRecord = {
        id,
        kind: 'bridge',
        name: selectedBridgeServer.display_name,
        bridgeUrl,
        serverId: selectedBridgeServer.server_id,
        serverName: selectedBridgeServer.display_name,
        pairingToken: connectingBridgeTransport.getPairingToken(),
        lastUsedAt: Date.now(),
      };
      upsertConnection(record);
      setSelectedConnectionId(id);
      setShowConnectionWizard(false);
      setConnectionMethod(null);
      setPairingCode('');
      setConnectingBridgeTransport(null);
    } catch (error: any) {
      Alert.alert('Pairing Failed', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    if (transport && 'disconnect' in transport && typeof (transport as any).disconnect === 'function') {
      (transport as any).disconnect();
    }
    if (
      connectingBridgeTransport &&
      'disconnect' in connectingBridgeTransport &&
      typeof (connectingBridgeTransport as any).disconnect === 'function'
    ) {
      (connectingBridgeTransport as any).disconnect();
    }
    setTransport(null);
    setBackend(null);
    setConnectingBridgeTransport(null);
    cancelConnectionWizard();
  };

  const handleDeleteConnection = (record: ConnectionRecord) => {
    setConnections((prev) => prev.filter((r) => r.id !== record.id));

    setSessionsCache((prev) => {
      if (!prev[record.id]) {
        return prev;
      }
      const next = { ...prev };
      delete next[record.id];
      return next;
    });

    setMessagesCache((prev) => {
      if (!prev[record.id]) {
        return prev;
      }
      const next = { ...prev };
      delete next[record.id];
      return next;
    });

    if (selectedConnectionId === record.id) {
      if (transport && 'disconnect' in transport && typeof (transport as any).disconnect === 'function') {
        (transport as any).disconnect();
      }
      setTransport(null);
      setBackend(null);
      setSelectedConnectionId(null);
    }
  };

  const renderMethodSelection = () => (
    <View style={styles.container}>
      <Text style={styles.title}>Select Connection Method</Text>
      
      <TouchableOpacity
        style={[styles.button, styles.methodButton]}
        onPress={() => selectMethod('manual')}>
        <Text style={styles.buttonText}>Manual Address</Text>
        <Text style={styles.methodDescription}>Enter IP address and port</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.methodButton]}
        onPress={() => selectMethod('discovery')}>
        <Text style={styles.buttonText}>Automatic Discovery</Text>
        <Text style={styles.methodDescription}>Find services via Bonjour</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.methodButton]}
        onPress={() => selectMethod('bridge')}>
        <Text style={styles.buttonText}>Bridge Service</Text>
        <Text style={styles.methodDescription}>Connect via bridge server</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.secondaryButton]}
        onPress={cancelConnectionWizard}>
        <Text style={styles.buttonTextSecondary}>Cancel</Text>
      </TouchableOpacity>
    </View>
  );

  const renderManualConnection = () => (
    <View style={styles.container}>
      <Text style={styles.title}>Manual Connection</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Host (e.g., 192.168.1.100)"
        value={manualHost}
        onChangeText={setManualHost}
        autoCapitalize="none"
        autoCorrect={false}
      />
      
      <TextInput
        style={styles.input}
        placeholder="Port (e.g., 8080)"
        value={manualPort}
        onChangeText={setManualPort}
        keyboardType="number-pad"
      />

      <TouchableOpacity
        style={[styles.button, styles.primaryButton]}
        onPress={connectManual}
        disabled={isLoading}>
        <Text style={styles.buttonText}>
          {isLoading ? 'Connecting...' : 'Connect'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.secondaryButton]}
        onPress={cancelConnectionWizard}>
        <Text style={styles.buttonTextSecondary}>Back</Text>
      </TouchableOpacity>
    </View>
  );

  const renderDiscoveryConnection = () => (
    <View style={styles.container}>
      <Text style={styles.title}>Service Discovery</Text>

      <View style={styles.statusContainer}>
        <View style={[styles.statusDot, isSearching ? styles.statusSearching : styles.statusInactive]} />
        <Text style={styles.statusText}>
          {isSearching ? 'Searching...' : 'Not searching'}
        </Text>
      </View>

      {discoveredServices.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Found {discoveredServices.length} service(s)
          </Text>
          <ScrollView style={styles.serviceList}>
            {discoveredServices.map((service, index) => (
              <TouchableOpacity
                key={`${service.name}-${index}`}
                style={styles.serviceItem}
                onPress={() => connectToService(service)}
                disabled={isLoading}>
                <Text style={styles.serviceName}>{service.name}</Text>
                <Text style={styles.serviceDetails}>
                  {service.host}:{service.port}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {isSearching && discoveredServices.length === 0 && (
        <Text style={styles.infoText}>Searching for services...</Text>
      )}

      <TouchableOpacity
        style={[styles.button, styles.secondaryButton]}
        onPress={cancelConnectionWizard}>
        <Text style={styles.buttonTextSecondary}>Back</Text>
      </TouchableOpacity>
    </View>
  );

  const testBridgeConnectivity = async () => {
    if (!bridgeUrl) return;

    const httpUrl = bridgeUrl
      .replace('ws://', 'http://')
      .replace('wss://', 'https://')
      .replace('/ws/websocket', '/health');

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
          `Bridge is running!\n\nStatus: ${data.status || 'ok'}\n\nYou can now try connecting via WebSocket.`,
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
    <View style={styles.container}>
      <Text style={styles.title}>Bridge Connection</Text>
      
      {!connectingBridgeTransport && (
        <>
          <Text style={styles.infoText}>
            For testing on a physical device, use your computer's IP address (not localhost).
          </Text>
          
          <Text style={[styles.infoText, { fontSize: 12, marginTop: 8 }]}>
            Example: ws://192.168.1.100:4000/ws/websocket
          </Text>

          <TextInput
            style={styles.input}
            placeholder="Bridge URL (e.g., ws://192.168.1.100:4000/ws/websocket)"
            value={bridgeUrl}
            onChangeText={setBridgeUrl}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={connectToBridge}
            disabled={isLoading}>
            <Text style={styles.buttonText}>
              {isLoading ? 'Connecting...' : 'Connect to Bridge'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={testBridgeConnectivity}
            disabled={isLoading || !bridgeUrl}>
            <Text style={styles.buttonTextSecondary}>Test Connectivity</Text>
          </TouchableOpacity>
        </>
      )}

      {connectingBridgeTransport && !selectedBridgeServer && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Available Servers ({bridgeServers.length})
          </Text>
          <ScrollView style={styles.serviceList}>
            {bridgeServers.map((server) => (
              <TouchableOpacity
                key={server.server_id}
                style={styles.serviceItem}
                onPress={() => requestPairing(server)}
                disabled={isLoading}>
                <Text style={styles.serviceName}>{server.display_name}</Text>
                <Text style={styles.serviceDetails}>{server.computer_name}</Text>
                <Text style={styles.serviceDetails}>ID: {server.server_id}</Text>
                {server.location && (
                  <Text style={styles.serviceDetails}>{server.location}</Text>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {selectedBridgeServer && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Pairing with {selectedBridgeServer.display_name}</Text>
          <Text style={styles.infoText}>
            Check the server terminal for the 6-digit pairing code
          </Text>
          
          <TextInput
            style={styles.input}
            placeholder="Enter 6-digit code"
            value={pairingCode}
            onChangeText={setPairingCode}
            keyboardType="number-pad"
            maxLength={6}
          />

          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={submitPairing}
            disabled={isLoading}>
            <Text style={styles.buttonText}>
              {isLoading ? 'Pairing...' : 'Submit Code'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={() => setSelectedBridgeServer(null)}>
            <Text style={styles.buttonTextSecondary}>Cancel</Text>
          </TouchableOpacity>
        </View>
      )}

      <TouchableOpacity
        style={[styles.button, styles.secondaryButton]}
        onPress={cancelConnectionWizard}>
        <Text style={styles.buttonTextSecondary}>Cancel</Text>
      </TouchableOpacity>
    </View>
  );

  const renderConnectingScreen = () => {
    if (connectionMethod === 'manual') return renderManualConnection();
    if (connectionMethod === 'discovery') return renderDiscoveryConnection();
    if (connectionMethod === 'bridge') return renderBridgeConnection();
    return null;
  };

  const handleSelectSavedConnection = async (record: ConnectionRecord) => {
    setIsLoading(true);
    try {
      if (transport && 'disconnect' in transport && typeof (transport as any).disconnect === 'function') {
        (transport as any).disconnect();
      }

      let nextTransport: Transport | null = null;

      if (record.kind === 'manual' || record.kind === 'discovery') {
        const baseUrl = `http://${record.host}:${record.port}`;
        const httpTransport = new FetchTransport({ baseUrl });
        await httpTransport.request({ method: 'GET', path: '/api/data' });
        nextTransport = httpTransport;
      } else if (record.kind === 'bridge') {
        const bridge = new BridgeTransport({
          bridgeUrl: record.bridgeUrl,
          serverId: record.serverId,
          pairingToken: record.pairingToken,
          debug: true
        });
        await bridge.connect();
        nextTransport = bridge;
      }

      if (nextTransport) {
        setTransport(nextTransport);
        setBackend(new RestAgentBackend({ transport: nextTransport }));
        setSelectedConnectionId(record.id);
        upsertConnection({ ...record, lastUsedAt: Date.now() });
      }
    } catch (error: any) {
      console.log('Failed to reconnect to saved connection', error);
      Alert.alert('Connection Error', error?.message || 'Failed to reconnect');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaProvider>
      <ThemeProvider theme={theme}>
        <PinnedActionsProvider>
          <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
            <StatusBar barStyle={colorScheme === 'dark' ? 'light-content' : 'dark-content'} />
          {/** Determine active connection info for display components */}
          {/** This is derived once here and passed down rather than recomputed in children. */}
          {(() => {
          const activeConnection =
            selectedConnectionId != null
              ? connections.find((c) => c.id === selectedConnectionId) || null
              : null;
          const activeConnectionAdditionalInfo =
            activeConnection != null ? getConnectionAdditionalInfo(activeConnection) : null;
          const activeConnectionName = activeConnection != null ? activeConnection.name : null;

          return (
            <ConnectedRoot
              backend={backend}
              transport={transport}
              onDisconnect={handleDisconnect}
              connections={connections}
              connectionsLoading={connectionsLoading}
              onSelectConnectionRecord={handleSelectSavedConnection}
              onNewConnectionRequested={() => {
                if (backend) {
                  handleDisconnect();
                }
                setConnectionMethod(null);
                setShowConnectionWizard(true);
              }}
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
              activeConnectionName={activeConnectionName}
              activeConnectionAdditionalInfo={activeConnectionAdditionalInfo}
              sessionsCache={sessionsCache}
              onUpdateSessionsCache={updateSessionsCache}
              messagesCache={messagesCache}
              onUpdateMessagesCache={updateMessagesCache}
              onSaveMessagesComposeText={saveMessagesComposeText}
              onSaveMessagesScrollAnchor={saveMessagesScrollAnchor}
            />
          );
          })()}
          </SafeAreaView>
        </PinnedActionsProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
const createStyles = (theme: Theme) =>
  StyleSheet.create({
    safeArea: {
      flex: 1,
      backgroundColor: theme.background,
    },
    scrollContent: {
      flexGrow: 1,
    },
    container: {
      flex: 1,
      padding: 16,
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      marginBottom: 24,
      textAlign: 'center',
      color: theme.text,
    },
    statusContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 12,
      backgroundColor: theme.primaryMuted,
      borderRadius: 8,
      marginBottom: 16,
    },
    statusDot: {
      width: 12,
      height: 12,
      borderRadius: 6,
      marginRight: 8,
    },
    statusText: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.text,
    },
    button: {
      paddingHorizontal: 20,
      paddingVertical: 12,
      borderRadius: 8,
      alignItems: 'center',
      marginBottom: 12,
    },
    methodButton: {
      backgroundColor: theme.primary,
      paddingVertical: 16,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
      marginTop: 8,
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: 16,
      fontWeight: '600',
    },
    buttonTextSecondary: {
      color: theme.text,
      fontSize: 16,
      fontWeight: '600',
    },
    methodDescription: {
      color: theme.textOnPrimary,
      fontSize: 12,
      marginTop: 4,
      opacity: 0.8,
    },
    input: {
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      padding: 12,
      marginBottom: 12,
      fontSize: 16,
      color: theme.text,
    },
    section: {
      marginTop: 16,
      flex: 1,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '600',
      marginBottom: 8,
      color: theme.text,
    },
    serviceList: {
      maxHeight: 300,
    },
    serviceItem: {
      padding: 12,
      backgroundColor: theme.surface,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    serviceName: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    serviceDetails: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    infoText: {
      fontSize: 14,
      color: theme.textSecondary,
      textAlign: 'center',
      fontStyle: 'italic',
      marginVertical: 16,
    },
    endpointItem: {
      padding: 12,
      backgroundColor: theme.surface,
      borderRadius: 8,
      marginBottom: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    endpointName: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    endpointDescription: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    loadingContainer: {
      alignItems: 'center',
      marginTop: 16,
    },
    loadingText: {
      marginTop: 8,
      fontSize: 14,
      color: theme.textSecondary,
    },
    responseContainer: {
      backgroundColor: theme.surfaceAlt,
      borderRadius: 8,
      padding: 12,
      maxHeight: 200,
    },
    responseText: {
      fontSize: 12,
      fontFamily: 'Courier',
      color: theme.text,
    },
    statusSearching: {
      backgroundColor: '#FF9500',
    },
    statusInactive: {
      backgroundColor: theme.textSecondary,
    },
    statusConnected: {
      backgroundColor: 'rgba(52, 199, 89, 0.1)',
    },
    statusConnectedDot: {
      backgroundColor: theme.success,
    },
  });

export default App;
