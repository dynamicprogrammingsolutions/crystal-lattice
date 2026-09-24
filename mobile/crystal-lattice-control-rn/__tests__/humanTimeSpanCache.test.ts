import AsyncStorage from '@react-native-async-storage/async-storage';

import {
  HUMAN_TIME_SPANS_STORAGE_KEY,
  HUMAN_TIME_SPANS_SOFT_CAP,
  appendSpan,
  loadSpans,
  removeFirstSpans,
} from '../src/humanTimeTelemetry/spanCache';
import type { HumanTimeSpan } from '../src/humanTimeTelemetry/spanTracker';

function span(sessionId: string | null, from: string, to: string): HumanTimeSpan {
  return { sessionId, from, to };
}

async function readRaw(): Promise<Record<string, unknown>> {
  const raw = await AsyncStorage.getItem(HUMAN_TIME_SPANS_STORAGE_KEY);
  return raw ? (JSON.parse(raw) as Record<string, unknown>) : {};
}

describe('human time span cache', () => {
  beforeEach(async () => {
    await AsyncStorage.clear();
  });

  it('appends spans and loads them back, keyed per connection', async () => {
    const first = span('session-1', '2026-09-25T08:00:00.000Z', '2026-09-25T08:05:00.000Z');
    const second = span(null, '2026-09-25T09:00:00.000Z', '2026-09-25T09:02:00.000Z');

    expect(await appendSpan('connection-a', first)).toBe(true);
    expect(await appendSpan('connection-a', second)).toBe(true);
    expect(await appendSpan('connection-b', second)).toBe(true);

    expect(await loadSpans('connection-a')).toEqual([first, second]);
    expect(await loadSpans('connection-b')).toEqual([second]);
    expect(await loadSpans('connection-unknown')).toEqual([]);
  });

  it('survives a restart (state reloaded from storage)', async () => {
    const recorded = span('session-1', '2026-09-25T08:00:00.000Z', '2026-09-25T08:05:00.000Z');
    await appendSpan('connection-a', recorded);

    // A fresh process reads the same backing store.
    expect(await loadSpans('connection-a')).toEqual([recorded]);
  });

  it('removes only the first N spans after an upload confirms them', async () => {
    const spans = [
      span('s1', '2026-09-25T08:00:00.000Z', '2026-09-25T08:01:00.000Z'),
      span('s1', '2026-09-25T08:02:00.000Z', '2026-09-25T08:03:00.000Z'),
      span(null, '2026-09-25T08:04:00.000Z', '2026-09-25T08:05:00.000Z'),
    ];
    for (const entry of spans) {
      await appendSpan('connection-a', entry);
    }

    await removeFirstSpans('connection-a', 2);
    expect(await loadSpans('connection-a')).toEqual([spans[2]]);

    // Removing more than remains is a no-op beyond the available count.
    await removeFirstSpans('connection-a', 5);
    expect(await loadSpans('connection-a')).toEqual([]);
  });

  it('keeps other connections untouched when one connection drains', async () => {
    const aSpan = span('s1', '2026-09-25T08:00:00.000Z', '2026-09-25T08:01:00.000Z');
    const bSpan = span('s2', '2026-09-25T09:00:00.000Z', '2026-09-25T09:01:00.000Z');
    await appendSpan('connection-a', aSpan);
    await appendSpan('connection-b', bSpan);

    await removeFirstSpans('connection-a', 1);

    expect(await loadSpans('connection-a')).toEqual([]);
    expect(await loadSpans('connection-b')).toEqual([bSpan]);
  });

  it('drops a span on a storage failure instead of throwing', async () => {
    const recorded = span('s1', '2026-09-25T08:00:00.000Z', '2026-09-25T08:01:00.000Z');
    await appendSpan('connection-a', recorded);
    await expect(loadSpans('connection-a')).resolves.toEqual([recorded]);

    const failingStore = {
      get: () => Promise.reject(new Error('storage unavailable')),
      set: () => Promise.reject(new Error('storage unavailable')),
      delete: () => Promise.reject(new Error('storage unavailable')),
    };
    const next = span('s1', '2026-09-25T08:02:00.000Z', '2026-09-25T08:03:00.000Z');
    await expect(appendSpan('connection-a', next, failingStore)).resolves.toBe(false);

    // The failed append dropped only that span; the cache is unchanged and
    // later appends work again.
    await expect(loadSpans('connection-a')).resolves.toEqual([recorded]);
    await expect(appendSpan('connection-a', next)).resolves.toBe(true);
    await expect(loadSpans('connection-a')).resolves.toEqual([recorded, next]);
  });

  it('treats malformed stored payloads as empty and keeps appending', async () => {
    await AsyncStorage.setItem(HUMAN_TIME_SPANS_STORAGE_KEY, 'not-json');
    await expect(loadSpans('connection-a')).resolves.toEqual([]);

    const recorded = span('s1', '2026-09-25T08:00:00.000Z', '2026-09-25T08:01:00.000Z');
    await expect(appendSpan('connection-a', recorded)).resolves.toBe(true);
    await expect(loadSpans('connection-a')).resolves.toEqual([recorded]);
  });

  it('drops the oldest spans beyond the soft cap', async () => {
    const first = span('s1', '2026-09-25T08:00:00.000Z', '2026-09-25T08:01:00.000Z');
    await appendSpan('connection-a', first);
    for (let index = 0; index < HUMAN_TIME_SPANS_SOFT_CAP; index += 1) {
      const entry = span(
        's1',
        `2026-09-25T09:${String(index).padStart(2, '0')}:00.000Z`,
        `2026-09-25T09:${String(index).padStart(2, '0')}:30.000Z`,
      );
      await appendSpan('connection-a', entry);
    }

    const remaining = await loadSpans('connection-a');
    expect(remaining).toHaveLength(HUMAN_TIME_SPANS_SOFT_CAP);
    expect(remaining).not.toContainEqual(first);
    const raw = await readRaw();
    expect(Object.keys(raw)).toEqual(['connection-a']);
  });
});