import 'react-native-url-polyfill/auto';
import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  useColorScheme,
  Alert,
  TextInput,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Zeroconf from 'react-native-zeroconf';
import ConnectedRoot from './src/ConnectedRoot';
import ConnectionsScreen from './src/ConnectionsScreen';
import { getConnectionAdditionalInfo } from './src/connectionInfo';
import type { SessionSummary, IndexedMessage } from './src/api';
import { ThemeProvider, lightTheme, darkTheme, type Theme } from './src/theme';

type ConnectionMethod = 'manual' | 'discovery' | 'bridge';

interface Service {
  name: string;
  host: string;
  port: number;
  addresses: string[];
}

interface BridgeServer {
  server_id: string;
  display_name: string;
  computer_name: string;
  location?: string;
}

export interface ConnectionAdapter {
  connect(): Promise<void>;
  get(path: string): Promise<any>;
  put(path: string, data: any): Promise<any>;
  post(path: string, data: any): Promise<any>;
  patch(path: string, data: any): Promise<any>;
  delete(path: string, data?: any): Promise<any>;
  disconnect(): void;
  getDisplayName(): string;
}

export type ConnectionKind = 'manual' | 'discovery' | 'bridge';

export interface BaseConnectionRecord {
  id: string;
  kind: ConnectionKind;
  name: string;
  lastUsedAt: number;
}

export interface ManualConnectionRecord extends BaseConnectionRecord {
  kind: 'manual';
  host: string;
  port: number;
}

export interface DiscoveryConnectionRecord extends BaseConnectionRecord {
  kind: 'discovery';
  host: string;
  port: number;
  serviceName: string;
}

export interface BridgeConnectionRecord extends BaseConnectionRecord {
  kind: 'bridge';
  bridgeUrl: string;
  serverId: string;
  serverName: string;
  pairingToken: string | null;
}

export type ConnectionRecord =
  | ManualConnectionRecord
  | DiscoveryConnectionRecord
  | BridgeConnectionRecord;

const STORAGE_KEY_CONNECTIONS = 'clc_connections_v1';
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
  composeText?: string;
  scrollOffset?: number;
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

class HttpAdapter implements ConnectionAdapter {
  private host: string;
  private port: number;
  private name: string;

  constructor(host: string, port: number, name: string) {
    this.host = host;
    this.port = port;
    this.name = name;
  }

  async connect(): Promise<void> {
    const url = `http://${this.host}:${this.port}/api/data`;
    const response = await fetch(url, { method: 'GET', timeout: 5000 } as any);
    if (!response.ok) {
      throw new Error(`Connection failed: ${response.status}`);
    }
  }

  async get(path: string): Promise<any> {
    const url = `http://${this.host}:${this.port}${path}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    return await response.json();
  }

  async put(path: string, data: any): Promise<any> {
    const url = `http://${this.host}:${this.port}${path}`;
    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return await response.json();
  }

  async post(path: string, data: any): Promise<any> {
    const url = `http://${this.host}:${this.port}${path}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data ?? {}),
    });
    return await response.json();
  }

  async patch(path: string, data: any): Promise<any> {
    const url = `http://${this.host}:${this.port}${path}`;
    const response = await fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data ?? {}),
    });
    return await response.json();
  }

  async delete(path: string, data?: any): Promise<any> {
    const url = `http://${this.host}:${this.port}${path}`;
    const init: any = {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    };
    if (data !== undefined) {
      init.body = JSON.stringify(data);
    }
    const response = await fetch(url, init);
    if (!response.ok) {
      // Try to surface JSON error body when available
      let message = `Request failed: ${response.status}`;
      try {
        const errorData = await response.json();
        if (typeof errorData === 'object' && errorData && typeof (errorData as any).detail === 'string') {
          message = (errorData as any).detail;
        }
      } catch {
        // ignore JSON parse errors
      }
      throw new Error(message);
    }
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  disconnect(): void {
  }

  getDisplayName(): string {
    return this.name;
  }
}

class BridgeAdapter implements ConnectionAdapter {
  private bridgeUrl: string;
  private ws: WebSocket | null = null;
  private clientId: string;
  private refCounter: number = 0;
  private sessionId: string | null = null;
  private serverId: string | null = null;
  private serverName: string = '';
  private pairingToken: string | null = null;
  private connectPromise: Promise<void> | null = null;
  private responseHandlers: Map<string, (data: any) => void> = new Map();

  constructor(
    bridgeUrl: string,
    opts?: { serverId?: string; serverName?: string; pairingToken?: string | null },
  ) {
    this.bridgeUrl = bridgeUrl;
    this.clientId = this.generateUuid();
    if (opts) {
      this.serverId = opts.serverId ?? null;
      this.serverName = opts.serverName ?? '';
      this.pairingToken = opts.pairingToken ?? null;
    }
  }

  private generateUuid(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      // eslint-disable-next-line no-bitwise
      const r = Math.random() * 16 | 0;
      // eslint-disable-next-line no-bitwise
      const v = c === 'x' ? r : ((r & 0x3) | 0x8);
      return v.toString(16);
    });
  }

  private getRef(): string {
    this.refCounter++;
    return this.refCounter.toString();
  }

  private phoenixMessage(topic: string, event: string, payload: any): string {
    return JSON.stringify({
      topic,
      event,
      payload,
      ref: this.getRef(),
    });
  }

  private async ensureConnected(): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    if (!this.connectPromise) {
      this.connectPromise = this.connectInternal();
    }

    try {
      await this.connectPromise;
    } finally {
      this.connectPromise = null;
    }
  }

  async connect(): Promise<void> {
    await this.ensureConnected();
  }

  private connectInternal(): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log('🔌 Connecting to bridge:', this.bridgeUrl);
      
      const connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          console.log('⏰ Connection timeout');
          this.ws.close();
          reject(new Error('Connection timeout - bridge is not responding. Check that:\n1. Bridge is running (docker-compose ps)\n2. URL is correct\n3. Device can reach the bridge (try curl from terminal)'));
        }
      }, 10000);

      try {
        const fullUrl = `${this.bridgeUrl}?type=app`;
        console.log('📡 Full WebSocket URL:', fullUrl);
        
        this.ws = new WebSocket(fullUrl);
        console.log('📞 WebSocket created, waiting for connection...');

        this.ws.onopen = async () => {
          console.log('✅ WebSocket opened successfully');
          clearTimeout(connectionTimeout);
          
          this.ws!.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('📨 Received:', data);
            
            if (data.ref && this.responseHandlers.has(data.ref)) {
              const handler = this.responseHandlers.get(data.ref)!;
              this.responseHandlers.delete(data.ref);
              handler(data);
            }
          };

          try {
            await this.joinChannel();

            if (this.pairingToken && this.serverId && !this.sessionId) {
              console.log('🔁 Attempting to resume bridge session');
              await this.resumeSessionRaw();
            }

            console.log('✅ Bridge connection complete');
            resolve();
          } catch (err: any) {
            console.log('❌ Failed to complete bridge handshake:', err);
            clearTimeout(connectionTimeout);
            this.ws?.close();
            reject(new Error(`Failed to complete bridge handshake: ${err.message}`));
          }
        };

        this.ws.onerror = (error: any) => {
          console.log('❌ WebSocket error event:', JSON.stringify(error));
          console.log('❌ WebSocket error type:', error.type);
          console.log('❌ WebSocket error message:', error.message);
          clearTimeout(connectionTimeout);
          
          let errorMessage = 'WebSocket connection failed.\n\n';
          errorMessage += 'Possible causes:\n';
          errorMessage += '1. Bridge service not running\n';
          errorMessage += '2. Incorrect URL (check IP address)\n';
          errorMessage += '3. Network connectivity issue\n';
          errorMessage += '4. Firewall blocking connection\n\n';
          errorMessage += `URL: ${this.bridgeUrl}`;
          
          reject(new Error(errorMessage));
        };

        this.ws.onclose = (event: any) => {
          console.log('🔌 WebSocket closed:', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
          });
          clearTimeout(connectionTimeout);
          this.ws = null;
          this.sessionId = null;
          
          if (event.code !== 1000 && event.code !== 1005) {
            const errorMsg = `Connection closed unexpectedly (code: ${event.code})`;
            if (!this.sessionId) {
              reject(new Error(errorMsg));
            }
          }
        };
      } catch (error: any) {
        console.log('❌ Exception creating WebSocket:', error);
        clearTimeout(connectionTimeout);
        reject(new Error(`Failed to create WebSocket: ${error.message}`));
      }
    });
  }

  private sendMessageRaw(topic: string, event: string, payload: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const ref = this.getRef();
      const message = JSON.stringify({ topic, event, payload, ref });

      this.responseHandlers.set(ref, (data) => {
        if (data.event === 'phx_reply' && data.payload.status === 'ok') {
          resolve(data.payload.response);
        } else {
          reject(new Error(data.payload.response?.error || 'Request failed'));
        }
      });

      this.ws.send(message);

      setTimeout(() => {
        if (this.responseHandlers.has(ref)) {
          this.responseHandlers.delete(ref);
          reject(new Error('Request timeout'));
        }
      }, 30000);
    });
  }

  private async sendMessage(topic: string, event: string, payload: any): Promise<any> {
    await this.ensureConnected();
    return this.sendMessageRaw(topic, event, payload);
  }

  private async joinChannel(): Promise<void> {
    const topic = `app:${this.clientId}`;
    const ref = this.getRef();
    const msg = JSON.stringify({ topic, event: 'phx_join', payload: {}, ref });

    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      this.responseHandlers.set(ref, (data) => {
        if (data.event === 'phx_reply' && data.payload.status === 'ok') {
          console.log('✅ Joined app channel');
          resolve();
        } else {
          reject(new Error('Failed to join channel'));
        }
      });

      this.ws.send(msg);
    });
  }

  async listServers(): Promise<BridgeServer[]> {
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'list_servers',
      {}
    );
    return response.servers || [];
  }

  async requestPairing(serverId: string): Promise<void> {
    this.serverId = serverId;
    await this.sendMessage(
      `app:${this.clientId}`,
      'pair_request',
      { server_id: serverId }
    );
  }

  async submitPairingCode(serverId: string, code: string, serverName: string): Promise<void> {
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'pair_submit',
      { server_id: serverId, code: code }
    );
    this.sessionId = response.session_id;
    this.pairingToken = response.pairing_token || null;
    this.serverId = serverId;
    this.serverName = serverName;
  }

  private async resumeSessionRaw(): Promise<void> {
    if (!this.pairingToken || !this.serverId) {
      return;
    }

    const response = await this.sendMessageRaw(
      `app:${this.clientId}`,
      'resume_session',
      {
        pairing_token: this.pairingToken,
        server_id: this.serverId,
      }
    );

    this.sessionId = response.session_id;
  }

  async get(path: string): Promise<any> {
    await this.ensureConnected();

    if (!this.sessionId) {
      throw new Error('Not paired with any server');
    }

    const requestId = this.generateUuid();
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'http_request',
      {
        request_id: requestId,
        session_id: this.sessionId,
        method: 'GET',
        path,
        headers: {},
        body: null,
      }
    );

    if (response.body) {
      return JSON.parse(response.body);
    }
    return response;
  }

  async put(path: string, data: any): Promise<any> {
    await this.ensureConnected();

    if (!this.sessionId) {
      throw new Error('Not paired with any server');
    }

    const requestId = this.generateUuid();
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'http_request',
      {
        request_id: requestId,
        session_id: this.sessionId,
        method: 'PUT',
        path,
        headers: {},
        body: JSON.stringify(data),
      }
    );

    if (response.body) {
      return JSON.parse(response.body);
    }
    return response;
  }

  async post(path: string, data: any): Promise<any> {
    await this.ensureConnected();

    if (!this.sessionId) {
      throw new Error('Not paired with any server');
    }

    const requestId = this.generateUuid();
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'http_request',
      {
        request_id: requestId,
        session_id: this.sessionId,
        method: 'POST',
        path,
        headers: {},
        body: JSON.stringify(data ?? {}),
      }
    );

    if (response.body) {
      return JSON.parse(response.body);
    }
    return response;
  }

  async patch(path: string, data: any): Promise<any> {
    if (!this.sessionId) {
      throw new Error('Not paired with any server');
    }

    const requestId = this.generateUuid();
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'http_request',
      {
        request_id: requestId,
        session_id: this.sessionId,
        method: 'PATCH',
        path,
        headers: {},
        body: JSON.stringify(data ?? {}),
      }
    );

    if (response.body) {
      return JSON.parse(response.body);
    }
    return response;
  }

  async delete(path: string, data?: any): Promise<any> {
    if (!this.sessionId) {
      throw new Error('Not paired with any server');
    }

    const requestId = this.generateUuid();
    const response = await this.sendMessage(
      `app:${this.clientId}`,
      'http_request',
      {
        request_id: requestId,
        session_id: this.sessionId,
        method: 'DELETE',
        path,
        headers: {},
        body: data === undefined ? null : JSON.stringify(data),
      }
    );

    if (response.body) {
      return JSON.parse(response.body);
    }
    return response;
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.serverId = null;
  }

  getDisplayName(): string {
    return this.serverName || 'Bridge Server';
  }
}

function App(): React.JSX.Element {
  const colorScheme = useColorScheme();
  const theme = colorScheme === 'dark' ? darkTheme : lightTheme;

  const [connectionMethod, setConnectionMethod] = useState<ConnectionMethod | null>(null);
  const [showConnectionWizard, setShowConnectionWizard] = useState(false);
  const [adapter, setAdapter] = useState<ConnectionAdapter | null>(null);
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
  const [bridgeAdapter, setBridgeAdapter] = useState<BridgeAdapter | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const styles = useMemo(() => createStyles(theme), [theme]);

  useEffect(() => {
    const loadConnections = async () => {
      setConnectionsLoading(true);
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY_CONNECTIONS);
        if (raw) {
          try {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) {
              setConnections(parsed as ConnectionRecord[]);
            }
          } catch {
            // ignore malformed storage
          }
        }
      } catch (err) {
        console.log('Failed to load saved connections', err);
      } finally {
        setConnectionsLoading(false);
      }
    };

    loadConnections();
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
        await AsyncStorage.setItem(
          STORAGE_KEY_CONNECTIONS,
          JSON.stringify(connections),
        );
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

  const updateMessagesUiState = (
    connectionId: string,
    sessionId: string,
    composeText: string,
    scrollOffset: number,
  ) => {
    setMessagesCache((prev) => {
      const bySession = prev[connectionId] ?? {};
      const existing = bySession[sessionId];

      const entry: MessagesCacheEntry = existing
        ? {
            ...existing,
            composeText,
            scrollOffset,
          }
        : {
            connectionId,
            sessionId,
            messages: [],
            lastLoadedAt: null,
            composeText,
            scrollOffset,
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
      const httpAdapter = new HttpAdapter(manualHost, parseInt(manualPort, 10), `${manualHost}:${manualPort}`);
      await httpAdapter.connect();
      setAdapter(httpAdapter);
      const id = generateId();
      const record: ManualConnectionRecord = {
        id,
        kind: 'manual',
        name: `${manualHost}:${manualPort}`,
        host: manualHost,
        port: parseInt(manualPort, 10),
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
      const httpAdapter = new HttpAdapter(service.host, service.port, service.name);
      await httpAdapter.connect();
      setAdapter(httpAdapter);
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
      
      const bridge = new BridgeAdapter(bridgeUrl);
      await bridge.connect();
      console.log('✅ Bridge connected, fetching servers...');
      
      setBridgeAdapter(bridge);
      
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
      setBridgeAdapter(null);
    } finally {
      setIsLoading(false);
    }
  };

  const requestPairing = async (server: BridgeServer) => {
    if (!bridgeAdapter) return;

    setSelectedBridgeServer(server);
    setIsLoading(true);
    try {
      await bridgeAdapter.requestPairing(server.server_id);
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
    if (!bridgeAdapter || !selectedBridgeServer || !pairingCode) {
      Alert.alert('Error', 'Please enter pairing code');
      return;
    }

    setIsLoading(true);
    try {
      await bridgeAdapter.submitPairingCode(
        selectedBridgeServer.server_id,
        pairingCode,
        selectedBridgeServer.display_name
      );
      setAdapter(bridgeAdapter);
      const id = generateId();
      const record: BridgeConnectionRecord = {
        id,
        kind: 'bridge',
        name: selectedBridgeServer.display_name,
        bridgeUrl,
        serverId: selectedBridgeServer.server_id,
        serverName: selectedBridgeServer.display_name,
        pairingToken: (bridgeAdapter as any).pairingToken ?? null,
        lastUsedAt: Date.now(),
      };
      upsertConnection(record);
      setSelectedConnectionId(id);
      setShowConnectionWizard(false);
      setConnectionMethod(null);
      setPairingCode('');
    } catch (error: any) {
      Alert.alert('Pairing Failed', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    if (adapter) {
      adapter.disconnect();
      setAdapter(null);
    }
    if (bridgeAdapter) {
      bridgeAdapter.disconnect();
      setBridgeAdapter(null);
    }
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
      if (adapter) {
        adapter.disconnect();
        setAdapter(null);
      }
      if (bridgeAdapter) {
        bridgeAdapter.disconnect();
        setBridgeAdapter(null);
      }
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
      
      {!bridgeAdapter && (
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

      {bridgeAdapter && !selectedBridgeServer && (
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
      let nextAdapter: ConnectionAdapter | null = null;

      if (record.kind === 'manual' || record.kind === 'discovery') {
        const httpAdapter = new HttpAdapter(record.host, record.port, record.name);
        await httpAdapter.connect();
        nextAdapter = httpAdapter;
      } else if (record.kind === 'bridge') {
        const bridge = new BridgeAdapter(record.bridgeUrl, {
          serverId: record.serverId,
          serverName: record.serverName,
          pairingToken: record.pairingToken,
        });
        await bridge.connect();
        nextAdapter = bridge;
      }

      if (nextAdapter) {
        setAdapter(nextAdapter);
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
    <ThemeProvider theme={theme}>
      <SafeAreaView style={styles.safeArea}>
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

          return (
            <ConnectedRoot
              adapter={adapter}
              onDisconnect={handleDisconnect}
              connections={connections}
              connectionsLoading={connectionsLoading}
              onSelectConnectionRecord={handleSelectSavedConnection}
              onNewConnectionRequested={() => {
                if (adapter) {
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
              activeConnectionAdditionalInfo={activeConnectionAdditionalInfo}
              sessionsCache={sessionsCache}
              onUpdateSessionsCache={updateSessionsCache}
              messagesCache={messagesCache}
              onUpdateMessagesCache={updateMessagesCache}
              onUpdateMessagesUiState={updateMessagesUiState}
            />
          );
        })()}
      </SafeAreaView>
    </ThemeProvider>
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
