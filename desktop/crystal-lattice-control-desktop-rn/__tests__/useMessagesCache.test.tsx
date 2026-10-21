import React, { useEffect } from 'react';
import ReactTestRenderer from 'react-test-renderer';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import {
  getSessionScopedMessagesCacheEntryKey,
  SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
} from '@crystal-lattice/frontend-sdk';

import {
  useMessagesCache,
  type UseMessagesCacheResult,
} from '../src/cache/useMessagesCache';

function createInMemoryStore(
  initial?: Record<string, string>,
): KeyValueStore & {
  data: Map<string, string>;
  writes: string[];
  deletes: string[];
} {
  const data = new Map<string, string>(Object.entries(initial ?? {}));
  const writes: string[] = [];
  const deletes: string[] = [];

  return {
    data,
    writes,
    deletes,
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

async function flushAsyncWork(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

function Harness(props: {
  store: KeyValueStore;
  onSnapshot: (value: UseMessagesCacheResult) => void;
}): React.JSX.Element | null {
  const result = useMessagesCache(props.store);

  useEffect(() => {
    props.onSnapshot(result);
  }, [props, result]);

  return null;
}

test('desktop hook hydrates v2 cache and scrubs active request ids', async () => {
  const entryKey = getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1');
  const store = createInMemoryStore({
    [SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY]: JSON.stringify([
      { connectionId: 'conn-1', sessionId: 'sess-1' },
    ]),
    [entryKey]: JSON.stringify({
      connectionId: 'conn-1',
      sessionId: 'sess-1',
      messages: [{ index: 0, message: { role: 'assistant', content: 'hi' } }],
      lastLoadedAt: 5,
      cursorEventId: 'cursor:1',
      activeRequestId: 'req:1',
    }),
  });

  let latest: UseMessagesCacheResult | null = null;
  const current = (): UseMessagesCacheResult => {
    if (!latest) {
      throw new Error('Missing hook snapshot');
    }
    return latest;
  };

  await ReactTestRenderer.act(async () => {
    ReactTestRenderer.create(
      <Harness
        store={store}
        onSnapshot={value => {
          latest = value;
        }}
      />,
    );
    await flushAsyncWork();
  });

  expect(current().hydrated).toBe(true);
  expect(current().messagesCache['conn-1']?.['sess-1']).toMatchObject({
    cursorEventId: 'cursor:1',
    activeRequestId: null,
  });
});

test('desktop hook persists only the touched session entry and index', async () => {
  const store = createInMemoryStore();
  let latest: UseMessagesCacheResult | null = null;
  const current = (): UseMessagesCacheResult => {
    if (!latest) {
      throw new Error('Missing hook snapshot');
    }
    return latest;
  };

  await ReactTestRenderer.act(async () => {
    ReactTestRenderer.create(
      <Harness
        store={store}
        onSnapshot={value => {
          latest = value;
        }}
      />,
    );
    await flushAsyncWork();
  });

  store.writes.length = 0;

  await ReactTestRenderer.act(async () => {
    current().updateMessagesCache({
      connectionId: 'conn-1',
      sessionId: 'sess-1',
      messages: [{ index: 0, message: { role: 'user', content: 'hello' } }],
      cursorEventId: 'cursor:2',
      activeRequestId: 'req:2',
    });
    await flushAsyncWork();
  });

  expect(store.writes).toEqual([
    getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1'),
    SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
  ]);
  expect(
    JSON.parse(
      store.data.get(
        getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1'),
      ) ?? 'null',
    ),
  ).toMatchObject({
    connectionId: 'conn-1',
    sessionId: 'sess-1',
    cursorEventId: 'cursor:2',
    activeRequestId: null,
  });
});

test('desktop cache clears an explicitly completed request while preserving omitted state', async () => {
  const store = createInMemoryStore();
  let latest!: UseMessagesCacheResult;
  let renderer!: ReactTestRenderer.ReactTestRenderer;
  await ReactTestRenderer.act(async () => {
    renderer = ReactTestRenderer.create(
      <Harness
        store={store}
        onSnapshot={value => {
          latest = value;
        }}
      />,
    );
    await flushAsyncWork();
  });
  await ReactTestRenderer.act(async () => {
    latest.updateMessagesCache({
      connectionId: 'connection',
      sessionId: 'session',
      messages: [],
      activeRequestId: 'running',
      cursorEventId: 'cursor:1',
    });
  });
  await ReactTestRenderer.act(async () => {
    latest.updateMessagesCache({
      connectionId: 'connection',
      sessionId: 'session',
      messages: [],
    });
  });
  expect(latest.messagesCache.connection.session.activeRequestId).toBe(
    'running',
  );
  await ReactTestRenderer.act(async () => {
    latest.updateMessagesCache({
      connectionId: 'connection',
      sessionId: 'session',
      messages: [],
      activeRequestId: null,
      cursorEventId: null,
    });
  });
  expect(latest.messagesCache.connection.session.activeRequestId).toBeNull();
  expect(latest.messagesCache.connection.session.cursorEventId).toBeNull();
  await ReactTestRenderer.act(async () => {
    renderer.unmount();
  });
});
