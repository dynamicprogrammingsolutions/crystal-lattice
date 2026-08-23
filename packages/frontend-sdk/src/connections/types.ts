import type { BridgeTransportMode } from '../transport/bridgeConnectionTransport';

export type ConnectionKind = 'manual' | 'discovery' | 'bridge' | 'cloud';

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
  transportMode?: BridgeTransportMode;
}

export interface CloudConnectionRecord extends BaseConnectionRecord {
  kind: 'cloud';
  orchestratorUrl: string;
  connectionId?: string;
  instanceId?: string;
  initialSessionId?: string;
  sessionId?: string;
  token: string;
}

export type ConnectionRecord =
  | ManualConnectionRecord
  | DiscoveryConnectionRecord
  | BridgeConnectionRecord
  | CloudConnectionRecord;
