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

it('uses HTTP for historical records without a mode', () => {
  expect(resolveBridgeTransportMode(bridgeRecord())).toBe('http');
  expect(getConnectionAdditionalInfo(bridgeRecord())).toBe('serverId: server-1');
});

it.each(['websocket', 'http', 'hybrid'] as const)(
  'uses the HTTP product default for historical %s metadata',
  (transportMode) => {
    expect(getConnectionAdditionalInfo(bridgeRecord({ transportMode }))).toBe('serverId: server-1');
  },
);

it.each([
  [undefined, 'http'],
  ['websocket', 'http'],
  ['http', 'http'],
  ['hybrid', 'http'],
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

it.each(['websocket', 'hybrid'] as const)(
  'applies an app-wide %s diagnostic override while preserving the saved token',
  (mode) => {
    const record = bridgeRecord({ transportMode: 'http' });
    expect(getSavedBridgeTransportOptions(record, mode)).toEqual({
      bridgeUrl: record.bridgeUrl, serverId: record.serverId, pairingToken: 'token', mode,
    });
    expect(record.transportMode).toBe('http');
  },
);
