import type { ConnectionRecord } from '../App';

export function getConnectionAdditionalInfo(record: ConnectionRecord): string {
  if (record.kind === 'bridge') {
    const serverId = (record as any).serverId;
    if (typeof serverId === 'string' && serverId.length > 0) {
      return `serverId: ${serverId}`;
    }
  }

  return `id: ${record.id}`;
}
