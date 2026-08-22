import type { BridgeConnectionRecord } from '@crystal-lattice/frontend-sdk';

import {
  getSavedBridgeTransportOptions,
  resolveBridgeTransportMode,
} from '../src/bridgeConnection';
import { getConnectionAdditionalInfo } from '../src/connectionInfo';

function bridgeRecord(overrides: Partial<BridgeConnectionRecord> = {}): BridgeConnectionRecord {
  return {
    id: 'connection-1',
    kind: 'bridge',
    name: 'Bridge',
    lastUsedAt: 1,
    bridgeUrl: 'wss://bridge.test/ws/websocket',
    serverId: 'server-1',
    serverName: 'Server',
    pairingToken: 'token',
    ...overrides,
  };
}

it('treats bridge records without a mode as WebSocket-only', () => {
  expect(resolveBridgeTransportMode(bridgeRecord())).toBe('websocket');
  expect(getConnectionAdditionalInfo(bridgeRecord())).toContain('transport: websocket');
});

it.each(['websocket', 'http', 'hybrid'] as const)(
  'shows an explicit %s bridge transport override',
  (transportMode) => {
    expect(getConnectionAdditionalInfo(bridgeRecord({ transportMode }))).toContain(
      `transport: ${transportMode}`,
    );
  },
);

it.each([
  [undefined, 'websocket'],
  ['websocket', 'websocket'],
  ['http', 'http'],
  ['hybrid', 'hybrid'],
] as const)(
  'reconstructs a saved %s bridge mode with the same server and pairing token',
  (transportMode, expectedMode) => {
    const record = bridgeRecord({
      transportMode,
      pairingToken: 'saved-pairing-token',
    });

    expect(getSavedBridgeTransportOptions(record)).toEqual({
      bridgeUrl: 'wss://bridge.test/ws/websocket',
      mode: expectedMode,
      serverId: 'server-1',
      pairingToken: 'saved-pairing-token',
    });
  },
);
