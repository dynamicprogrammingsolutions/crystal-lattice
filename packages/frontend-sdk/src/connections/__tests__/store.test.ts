import { describe, expect, it } from 'vitest';

import type { KeyValueStore } from '../../storage/keyValueStore';

import { CONNECTIONS_STORAGE_KEY, loadConnections, saveConnections } from '../store';
import type { ConnectionRecord } from '../types';

function createInMemoryStore(initial?: Record<string, string>): KeyValueStore {
  const data = new Map<string, string>(Object.entries(initial ?? {}));

  return {
    async get(key) {
      return data.get(key) ?? null;
    },
    async set(key, value) {
      data.set(key, value);
    },
    async delete(key) {
      data.delete(key);
    },
  };
}

describe('connections store', () => {
  it('returns empty array when storage is missing', async () => {
    const store = createInMemoryStore();
    expect(await loadConnections(store)).toEqual([]);
  });

  it('returns empty array when storage is malformed JSON', async () => {
    const store = createInMemoryStore({ [CONNECTIONS_STORAGE_KEY]: 'not-json' });
    expect(await loadConnections(store)).toEqual([]);
  });

  it('round-trips saved connections', async () => {
    const store = createInMemoryStore();

    const connections: ConnectionRecord[] = [
      {
        id: '1',
        kind: 'manual',
        name: 'Local',
        lastUsedAt: 1,
        host: '127.0.0.1',
        port: 8080,
      },
      {
        id: '2',
        kind: 'discovery',
        name: 'Bonjour',
        lastUsedAt: 2,
        host: '192.168.1.10',
        port: 8080,
        serviceName: 'Agent Terminal',
      },
      {
        id: '3',
        kind: 'bridge',
        name: 'Bridge',
        lastUsedAt: 3,
        bridgeUrl: 'ws://localhost:4000/ws/websocket',
        serverId: 'srv_1',
        serverName: 'My Server',
        pairingToken: null,
      },
    ];

    await saveConnections(store, connections);
    expect(await loadConnections(store)).toEqual(connections);
  });
});
