import type {
  BridgeConnectionRecord,
  BridgeTransportMode,
} from '@crystal-lattice/frontend-sdk';

export const DEFAULT_BRIDGE_TRANSPORT_MODE: BridgeTransportMode = 'websocket';

export function resolveBridgeTransportMode(
  record: Pick<BridgeConnectionRecord, 'transportMode'>,
): BridgeTransportMode {
  return record.transportMode ?? DEFAULT_BRIDGE_TRANSPORT_MODE;
}

export function getSavedBridgeTransportOptions(
  record: Pick<
    BridgeConnectionRecord,
    'bridgeUrl' | 'serverId' | 'pairingToken' | 'transportMode'
  >,
): {
  bridgeUrl: string;
  mode: BridgeTransportMode;
  serverId: string;
  pairingToken: string | null;
} {
  return {
    bridgeUrl: record.bridgeUrl,
    mode: resolveBridgeTransportMode(record),
    serverId: record.serverId,
    pairingToken: record.pairingToken,
  };
}
