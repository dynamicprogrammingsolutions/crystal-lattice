import { describe, expect, it } from 'vitest';

import type { KeyValueStore } from './keyValueStore';
import {
  clearSessionScopedMessagesCache,
  deleteConnectionSessionScopedMessagesCacheEntries,
  getSessionScopedMessagesCacheEntryKey,
  loadSessionScopedMessagesCache,
  persistSessionScopedMessagesCacheEntry,
  SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
} from './sessionScopedMessagesCache';

function createInMemoryStore(initial?: Record<string, string>): KeyValueStore & {
  dump(): Record<string, string>;
  writes: string[];
  deletes: string[];
} {
  const data = new Map<string, string>(Object.entries(initial ?? {}));
  const writes: string[] = [];
  const deletes: string[] = [];

  return {
    writes,
    deletes,
    dump() {
      return Object.fromEntries(data.entries());
    },
    async get(key) {
      return data.get(key) ?? null;
    },
    async set(key, value) {
      writes.push(key);
      data.set(key, value);
    },
    async delete(key) {
      deletes.push(key);
      data.delete(key);
    },
  };
}

describe('sessionScopedMessagesCache storage', () => {
  it('hydrates v2 entries, normalizes cursor ids, and scrubs active requests', async () => {
    const validKey = getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1');
    const malformedKey = getSessionScopedMessagesCacheEntryKey('conn-2', 'sess-2');
    const store = createInMemoryStore({
      [SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY]: JSON.stringify([
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-2', sessionId: 'sess-2' },
        { nope: true },
      ]),
      [validKey]: JSON.stringify({
        connectionId: 'conn-1',
        sessionId: 'sess-1',
        messages: [{ index: 0, message: { role: 'assistant', content: 'hello' } }],
        lastLoadedAt: 123,
        eventsCursorId: 'cursor:1',
        activeRequestId: 'req:1',
        composeText: 'draft',
      }),
      [malformedKey]: '{"broken":true}',
    });

    const result = await loadSessionScopedMessagesCache(store);

    expect(result.index).toEqual([{ connectionId: 'conn-1', sessionId: 'sess-1' }]);
    expect(result.cache).toEqual({
      'conn-1': {
        'sess-1': {
          connectionId: 'conn-1',
          sessionId: 'sess-1',
          messages: [{ index: 0, message: { role: 'assistant', content: 'hello' } }],
          lastLoadedAt: 123,
          cursorEventId: 'cursor:1',
          activeRequestId: null,
          composeText: 'draft',
        },
      },
    });
  });

  it('persists only the targeted session entry and leaves unrelated entries untouched', async () => {
    const untouchedKey = getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1');
    const targetKey = getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-2');
    const untouchedRaw = JSON.stringify({
      connectionId: 'conn-1',
      sessionId: 'sess-1',
      messages: [],
      lastLoadedAt: 10,
      cursorEventId: 'keep-me',
      activeRequestId: null,
    });
    const store = createInMemoryStore({
      [SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY]: JSON.stringify([
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-1', sessionId: 'sess-2' },
      ]),
      [untouchedKey]: untouchedRaw,
      [targetKey]: JSON.stringify({
        connectionId: 'conn-1',
        sessionId: 'sess-2',
        messages: [],
        lastLoadedAt: 11,
        cursorEventId: 'old',
        activeRequestId: null,
      }),
    });

    const nextIndex = await persistSessionScopedMessagesCacheEntry(store, {
      index: [
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-1', sessionId: 'sess-2' },
      ],
      entry: {
        connectionId: 'conn-1',
        sessionId: 'sess-2',
        messages: [{ index: 0, message: { role: 'user', content: 'updated' } }],
        lastLoadedAt: 99,
        cursorEventId: 'cursor:new',
        activeRequestId: 'req:new',
      },
    });

    expect(nextIndex).toEqual([
      { connectionId: 'conn-1', sessionId: 'sess-1' },
      { connectionId: 'conn-1', sessionId: 'sess-2' },
    ]);
    expect(store.dump()[untouchedKey]).toBe(untouchedRaw);
    expect(JSON.parse(store.dump()[targetKey] ?? 'null')).toMatchObject({
      connectionId: 'conn-1',
      sessionId: 'sess-2',
      lastLoadedAt: 99,
      cursorEventId: 'cursor:new',
      activeRequestId: null,
    });
    expect(store.writes).toEqual([targetKey, SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY]);
  });

  it('deletes only one connection and keeps other cached sessions', async () => {
    const store = createInMemoryStore({
      [SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY]: JSON.stringify([
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-1', sessionId: 'sess-2' },
        { connectionId: 'conn-2', sessionId: 'sess-3' },
      ]),
      [getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1')]: '{}',
      [getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-2')]: '{}',
      [getSessionScopedMessagesCacheEntryKey('conn-2', 'sess-3')]: '{}',
    });

    const nextIndex = await deleteConnectionSessionScopedMessagesCacheEntries(store, {
      index: [
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-1', sessionId: 'sess-2' },
        { connectionId: 'conn-2', sessionId: 'sess-3' },
      ],
      connectionId: 'conn-1',
    });

    expect(nextIndex).toEqual([{ connectionId: 'conn-2', sessionId: 'sess-3' }]);
    expect(store.dump()).toEqual({
      [SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY]: JSON.stringify([
        { connectionId: 'conn-2', sessionId: 'sess-3' },
      ]),
      [getSessionScopedMessagesCacheEntryKey('conn-2', 'sess-3')]: '{}',
    });
  });

  it('clears all tracked entries and removes the index key', async () => {
    const store = createInMemoryStore({
      [SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY]: JSON.stringify([
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-2', sessionId: 'sess-2' },
      ]),
      [getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1')]: '{}',
      [getSessionScopedMessagesCacheEntryKey('conn-2', 'sess-2')]: '{}',
    });

    const nextIndex = await clearSessionScopedMessagesCache(store, {
      index: [
        { connectionId: 'conn-1', sessionId: 'sess-1' },
        { connectionId: 'conn-2', sessionId: 'sess-2' },
      ],
    });

    expect(nextIndex).toEqual([]);
    expect(store.dump()).toEqual({});
  });
});