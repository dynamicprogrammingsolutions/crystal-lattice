import React, { useEffect } from 'react';
import ReactTestRenderer from 'react-test-renderer';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import {
  getSessionScopedMessagesCacheEntryKey,
  SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
} from '@crystal-lattice/frontend-sdk';

import { useMessagesCache, type UseMessagesCacheResult } from '../src/cache/useMessagesCache';

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

function createStore(
  options?: {
    delayedIndexGet?: Promise<string | null>;
  },
): KeyValueStore & {
  data: Map<string, string>;
  writes: string[];
  deletes: string[];
} {
  const data = new Map<string, string>();
  const writes: string[] = [];
  const deletes: string[] = [];

  return {
    data,
    writes,
    deletes,
    async get(key) {
      if (
        key === SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY &&
        options?.delayedIndexGet
      ) {
        return options.delayedIndexGet;
      }
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

test('mobile hook does not persist before hydration completes', async () => {
  const delayedIndex = createDeferred<string | null>();
  const store = createStore({ delayedIndexGet: delayedIndex.promise });
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
        onSnapshot={(value) => {
          latest = value;
        }}
      />,
    );
    await flushAsyncWork();
  });

  expect(current().hydrated).toBe(false);
  expect(store.writes).toEqual([]);

  await ReactTestRenderer.act(async () => {
    delayedIndex.resolve(null);
    await flushAsyncWork();
  });

  expect(current().hydrated).toBe(true);
  expect(store.writes).toEqual([]);
});

test('mobile hook persists one session entry after hydration and preserves compatibility fields', async () => {
  const store = createStore();
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
        onSnapshot={(value) => {
          latest = value;
        }}
      />,
    );
    await flushAsyncWork();
  });

  await ReactTestRenderer.act(async () => {
    current().updateMessagesCache(
      'conn-1',
      'sess-1',
      [{ index: 0, message: { role: 'assistant', content: 'cached' } }],
      'cursor:3',
      'req:3',
    );
    await flushAsyncWork();
  });

  expect(current().messagesCache['conn-1']?.['sess-1']).toMatchObject({
    eventsCursorId: 'cursor:3',
    cursorEventId: 'cursor:3',
    activeRequestId: 'req:3',
  });
  expect(store.writes).toEqual([
    getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1'),
    SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
  ]);
  expect(
    JSON.parse(
      store.data.get(getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1')) ?? 'null',
    ),
  ).toMatchObject({
    connectionId: 'conn-1',
    sessionId: 'sess-1',
    cursorEventId: 'cursor:3',
    activeRequestId: null,
  });
});

test('mobile hook persists history range and preserves it across message updates', async () => {
  const store = createStore();
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
        onSnapshot={(value) => {
          latest = value;
        }}
      />,
    );
    await flushAsyncWork();
  });

  await ReactTestRenderer.act(async () => {
    current().saveMessagesHistoryRange('conn-1', 'sess-1', '-50', '');
    await flushAsyncWork();
  });

  expect(current().messagesCache['conn-1']?.['sess-1']).toMatchObject({
    rangeStartText: '-50',
    rangeEndText: '',
  });

  await ReactTestRenderer.act(async () => {
    current().updateMessagesCache(
      'conn-1',
      'sess-1',
      [{ index: 9, message: { role: 'assistant', content: 'newest' } }],
      'cursor:10',
      null,
    );
    await flushAsyncWork();
  });

  expect(current().messagesCache['conn-1']?.['sess-1']).toMatchObject({
    rangeStartText: '-50',
    rangeEndText: '',
    eventsCursorId: 'cursor:10',
  });
  expect(
    JSON.parse(
      store.data.get(getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1')) ?? 'null',
    ),
  ).toMatchObject({
    rangeStartText: '-50',
    rangeEndText: '',
  });
});

test('mobile hook hydrates a persisted per-session history range', async () => {
  const store = createStore();
  const entryKey = getSessionScopedMessagesCacheEntryKey('conn-1', 'sess-1');
  store.data.set(
    SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
    JSON.stringify([{ connectionId: 'conn-1', sessionId: 'sess-1' }]),
  );
  store.data.set(
    entryKey,
    JSON.stringify({
      connectionId: 'conn-1',
      sessionId: 'sess-1',
      messages: [],
      lastLoadedAt: 100,
      rangeStartText: '100',
      rangeEndText: '200',
    }),
  );
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
        onSnapshot={(value) => {
          latest = value;
        }}
      />,
    );
    await flushAsyncWork();
  });

  expect(current().messagesCache['conn-1']?.['sess-1']).toMatchObject({
    rangeStartText: '100',
    rangeEndText: '200',
  });
});