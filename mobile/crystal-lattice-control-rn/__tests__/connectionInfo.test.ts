import type { BridgeConnectionRecord } from '@crystal-lattice/frontend-sdk';

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
