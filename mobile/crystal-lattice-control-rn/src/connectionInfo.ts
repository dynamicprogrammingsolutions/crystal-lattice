import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';

export function getConnectionAdditionalInfo(record: ConnectionRecord): string {
  if (record.kind === 'embedded') {
    return `${record.model} via ${record.proxyUrl}`;
  }
  if (record.kind === 'bridge') {
    if (record.serverId.length > 0) {
      return `serverId: ${record.serverId}`;
    }
  }

  if (record.kind === 'cloud') {
    return record.connectionId
      ? `connection: ${record.connectionId}`
      : `session: ${record.sessionId || record.initialSessionId || record.instanceId || record.id}`;
  }

  return `id: ${record.id}`;
}
