import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';

import { resolveBridgeTransportMode } from './bridgeConnection';

export function getConnectionAdditionalInfo(record: ConnectionRecord): string {
  if (record.kind === 'bridge') {
    const mode = resolveBridgeTransportMode(record);
    if (record.serverId.length > 0) {
      return `serverId: ${record.serverId} · transport: ${mode}`;
    }
  }

  if (record.kind === 'cloud') {
    return record.connectionId
      ? `connection: ${record.connectionId}`
      : `session: ${record.sessionId || record.initialSessionId || record.instanceId || record.id}`;
  }

  return `id: ${record.id}`;
}
