import type {
  BridgeConnectionRecord,
  BridgeTransportMode,
} from '@crystal-lattice/frontend-sdk';

export const DEFAULT_BRIDGE_TRANSPORT_MODE: BridgeTransportMode = 'http';

export function resolveBridgeTransportMode(
  _record: Pick<BridgeConnectionRecord, 'transportMode'>,
  developmentMode: BridgeTransportMode = DEFAULT_BRIDGE_TRANSPORT_MODE,
): BridgeTransportMode {
  return developmentMode;
}

export function getSavedBridgeTransportOptions(
  record: Pick<
    BridgeConnectionRecord,
    'bridgeUrl' | 'serverId' | 'pairingToken' | 'transportMode'
  >,
  developmentMode: BridgeTransportMode = DEFAULT_BRIDGE_TRANSPORT_MODE,
): {
  bridgeUrl: string;
  mode: BridgeTransportMode;
  serverId: string;
  pairingToken: string | null;
} {
  return {
    bridgeUrl: record.bridgeUrl,
    mode: resolveBridgeTransportMode(record, developmentMode),
    serverId: record.serverId,
    pairingToken: record.pairingToken,
  };
}
