import type { KeyValueStore } from '../storage/keyValueStore';

import type { ConnectionRecord } from './types';

export const CONNECTIONS_STORAGE_KEY = 'clc_connections_v1';

export async function loadConnections(store: KeyValueStore): Promise<ConnectionRecord[]> {
  const raw = await store.get(CONNECTIONS_STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed as ConnectionRecord[];
  } catch {
    return [];
  }
}

export async function saveConnections(
  store: KeyValueStore,
  connections: readonly ConnectionRecord[],
): Promise<void> {
  await store.set(CONNECTIONS_STORAGE_KEY, JSON.stringify(connections));
}
