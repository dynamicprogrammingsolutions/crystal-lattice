import type { BridgeServer, WebSocketFactory } from './bridgeTransport';
import { BridgeTransport } from './bridgeTransport';
import type { PathPrefixTimeoutRule, Transport, TransportTimeoutRule } from './transport';
import { HttpBridgeTransport } from './httpBridgeTransport';
import { HybridBridgeTransport } from './hybridBridgeTransport';
import { deriveBridgeWebSocketUrl } from './bridgeAddress';

export type BridgeTransportMode = 'websocket' | 'http' | 'hybrid';

export interface BridgeConnectionTransport extends Transport {
  connect(): Promise<void>;
  disconnect(): void;
  prepareForResume(): void;
  getPairingToken(): string | null;
  getServerId(): string | null;
  isPaired(): boolean;
  listServers(): Promise<BridgeServer[]>;
  requestPairing(serverId: string): Promise<void>;
  submitPairingCode(serverId: string, code: string): Promise<void>;
}

export interface BridgeConnectionTransportOptions {
  bridgeUrl: string;
  bridgeHttpBaseUrl?: string;
  mode?: BridgeTransportMode;
  serverId?: string | null;
  pairingToken?: string | null;
  clientId?: string;
  fetchImpl?: typeof fetch;
  wsFactory?: WebSocketFactory;
  defaultRequestTimeoutMs?: number;
  connectTimeoutMs?: number;
  heartbeatIntervalMs?: number;
  heartbeatTimeoutMs?: number;
  debug?: boolean;
  logger?: (msg: string, meta?: any) => void;
  timeoutRules?: TransportTimeoutRule[];
  timeoutMsByPathPrefix?: PathPrefixTimeoutRule[];
}

export function createBridgeConnectionTransport(
  options: BridgeConnectionTransportOptions,
): BridgeConnectionTransport {
  const mode = options.mode ?? 'http';
  if (mode === 'http') {
    return new HttpBridgeTransport(options);
  }
  if (mode === 'hybrid') {
    return new HybridBridgeTransport({
      ...options,
      bridgeUrl: deriveBridgeWebSocketUrl(options.bridgeUrl),
    });
  }
  return new BridgeTransport({
    bridgeUrl: deriveBridgeWebSocketUrl(options.bridgeUrl),
    serverId: options.serverId,
    pairingToken: options.pairingToken,
    clientId: options.clientId,
    wsFactory: options.wsFactory,
    defaultRequestTimeoutMs: options.defaultRequestTimeoutMs,
    connectTimeoutMs: options.connectTimeoutMs,
    heartbeatIntervalMs: options.heartbeatIntervalMs,
    heartbeatTimeoutMs: options.heartbeatTimeoutMs,
    debug: options.debug,
    logger: options.logger,
    timeoutRules: options.timeoutRules,
    timeoutMsByPathPrefix: options.timeoutMsByPathPrefix,
  });
}
