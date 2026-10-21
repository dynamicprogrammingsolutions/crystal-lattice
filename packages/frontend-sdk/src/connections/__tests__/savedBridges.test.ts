import { describe, expect, it } from 'vitest';
import {
  CONNECTIONS_STORAGE_KEY,
  SAVED_BRIDGES_STORAGE_KEY,
  loadSavedBridgeUrls,
  saveSavedBridgeUrls,
  type KeyValueStore,
  type SavedBridgeUrl,
} from '../../..';

function store(initial: Record<string, string> = {}): KeyValueStore {
  const values = new Map(Object.entries(initial));
  return {
    get: async (key) => values.get(key) ?? null,
    set: async (key, value) => { values.set(key, value); },
    delete: async (key) => { values.delete(key); },
  };
}

describe('saved bridge URLs public store', () => {
  it('round-trips endpoints with labels and timestamps independently of credentials', async () => {
    const credentials = JSON.stringify([{ pairingToken: 'private-token' }]);
    const storage = store({ [CONNECTIONS_STORAGE_KEY]: credentials });
    const entries: SavedBridgeUrl[] = [
      { url: 'wss://bridge.test/ws/websocket', label: 'Office', lastUsedAt: 10 },
      { url: 'ws://127.0.0.1:4000/ws/websocket', lastUsedAt: 20 },
    ];
    await saveSavedBridgeUrls(storage, entries);
    expect(await loadSavedBridgeUrls(storage)).toEqual(entries);
    await saveSavedBridgeUrls(storage, entries.filter((entry) => entry.label !== 'Office'));
    expect(await loadSavedBridgeUrls(storage)).toEqual([entries[1]]);
    expect(await storage.get(CONNECTIONS_STORAGE_KEY)).toBe(credentials);
  });

  it.each([null, 'not-json', '{}', '[null, {"url": 1}, {"url":"bad","lastUsedAt":"1"}]'])(
    'ignores missing or invalid storage %s',
    async (raw) => {
      const storage = store(raw === null ? {} : { [SAVED_BRIDGES_STORAGE_KEY]: raw });
      expect(await loadSavedBridgeUrls(storage)).toEqual([]);
    },
  );
});