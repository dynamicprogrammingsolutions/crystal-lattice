import type { KeyValueStore } from "@crystal-lattice/frontend-sdk";

import type { HumanTimeSpan } from "./spanTracker";

export type SpanCacheStore = KeyValueStore;

export const HUMAN_TIME_SPANS_STORAGE_KEY = "clc_human_time_spans_v1";

/**
 * Soft cap per connection so a permanently failing upload can never grow
 * the cache without bound; the oldest spans drop first.
 */
export const HUMAN_TIME_SPANS_SOFT_CAP = 5_000;

type CacheState = Record<string, HumanTimeSpan[]>;

// Appends are read-modify-write cycles over one storage key; serialize them
// per store so concurrent closes never overwrite each other.
const appendChains = new WeakMap<object, Promise<unknown>>();

function chainFor(store: SpanCacheStore): Promise<unknown> {
  let chain = appendChains.get(store);
  if (!chain) {
    chain = Promise.resolve();
    appendChains.set(store, chain);
  }
  return chain;
}

function enqueue(
  store: SpanCacheStore,
  run: () => Promise<void>,
): Promise<void> {
  const next = chainFor(store)
    .then(run)
    .catch(() => undefined);
  appendChains.set(store, next);
  return next;
}

function parseState(raw: string | null): CacheState {
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {};
    }
    const state: CacheState = {};
    for (const [connectionId, value] of Object.entries(parsed as CacheState)) {
      if (!Array.isArray(value)) continue;
      const spans = value.filter(
        (entry): entry is HumanTimeSpan =>
          !!entry &&
          typeof entry === "object" &&
          typeof entry.from === "string" &&
          typeof entry.to === "string" &&
          (entry.sessionId === null || typeof entry.sessionId === "string"),
      );
      if (spans.length > 0) {
        state[connectionId] = spans;
      }
    }
    return state;
  } catch {
    return {};
  }
}

async function readState(store: SpanCacheStore): Promise<CacheState> {
  try {
    return parseState(await store.get(HUMAN_TIME_SPANS_STORAGE_KEY));
  } catch {
    return {};
  }
}

async function writeState(
  store: SpanCacheStore,
  state: CacheState,
): Promise<void> {
  await store.set(HUMAN_TIME_SPANS_STORAGE_KEY, JSON.stringify(state));
}

/**
 * Append one closed span to the connection's durable cache. Best-effort: a
 * storage failure drops this span (returns false) and never throws, so
 * telemetry can never block the UI.
 */
export async function appendSpan(
  connectionId: string,
  span: HumanTimeSpan,
  store: SpanCacheStore,
): Promise<boolean> {
  let appended = false;
  await enqueue(store, async () => {
    const state = await readState(store);
    const current = state[connectionId] ?? [];
    const next = [...current, span];
    if (next.length > HUMAN_TIME_SPANS_SOFT_CAP) {
      next.splice(0, next.length - HUMAN_TIME_SPANS_SOFT_CAP);
    }
    state[connectionId] = next;
    await writeState(store, state);
    appended = true;
  });
  return appended;
}

/** Load the connection's pending spans (oldest first). */
export async function loadSpans(
  connectionId: string,
  store: SpanCacheStore,
): Promise<HumanTimeSpan[]> {
  const state = await readState(store);
  return state[connectionId] ?? [];
}

/**
 * Remove the first `count` pending spans — called only after an upload
 * confirmed them. Appends only ever push to the end, so the first N are
 * exactly the spans the confirmed batch uploaded.
 */
export async function removeFirstSpans(
  connectionId: string,
  count: number,
  store: SpanCacheStore,
): Promise<void> {
  await enqueue(store, async () => {
    const state = await readState(store);
    const current = state[connectionId];
    if (!current || count <= 0) return;
    if (count >= current.length) {
      delete state[connectionId];
    } else {
      state[connectionId] = current.slice(count);
    }
    await writeState(store, state);
  });
}

function spansEqual(left: HumanTimeSpan, right: HumanTimeSpan): boolean {
  return (
    left.sessionId === right.sessionId &&
    left.from === right.from &&
    left.to === right.to
  );
}

/**
 * Remove confirmed spans by value while retaining rejected neighbors. Each
 * requested span removes at most one matching cache entry.
 */
export async function removeSpans(
  connectionId: string,
  confirmed: HumanTimeSpan[],
  store: SpanCacheStore,
): Promise<void> {
  if (confirmed.length === 0) return;
  await enqueue(store, async () => {
    const state = await readState(store);
    const current = state[connectionId];
    if (!current) return;
    const remaining = [...current];
    for (const span of confirmed) {
      const index = remaining.findIndex((entry) => spansEqual(entry, span));
      if (index >= 0) {
        remaining.splice(index, 1);
      }
    }
    if (remaining.length === 0) {
      delete state[connectionId];
    } else {
      state[connectionId] = remaining;
    }
    await writeState(store, state);
  });
}
