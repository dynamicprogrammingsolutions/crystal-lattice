import type { IndexedMessage } from '../types/messages';

import type { KeyValueStore } from './keyValueStore';

export const SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY = 'clc_messages_cache_index_v2';
export const SESSION_SCOPED_MESSAGES_CACHE_ENTRY_KEY_PREFIX =
  'clc_messages_cache_entry_v2';

export interface SessionScopedMessagesCacheEntry<TScrollAnchor = unknown> {
  connectionId: string;
  sessionId: string;
  messages: IndexedMessage[];
  lastLoadedAt: number | null;
  cursorEventId?: string | null;
  activeRequestId?: string | null;
  composeText?: string;
  scrollAnchor?: TScrollAnchor;
  rangeStartText?: string | null;
  rangeEndText?: string | null;
}

export type SessionScopedMessagesBySession<TScrollAnchor = unknown> = Record<
  string,
  SessionScopedMessagesCacheEntry<TScrollAnchor>
>;

export type SessionScopedMessagesCache<TScrollAnchor = unknown> = Record<
  string,
  SessionScopedMessagesBySession<TScrollAnchor>
>;

export interface SessionScopedMessagesCacheIndexEntry {
  connectionId: string;
  sessionId: string;
}

export interface SessionScopedMessagesCacheHydrationResult<TScrollAnchor = unknown> {
  cache: SessionScopedMessagesCache<TScrollAnchor>;
  index: SessionScopedMessagesCacheIndexEntry[];
}

export function getSessionScopedMessagesCacheEntryKey(
  connectionId: string,
  sessionId: string,
): string {
  return [
    SESSION_SCOPED_MESSAGES_CACHE_ENTRY_KEY_PREFIX,
    encodeURIComponent(connectionId),
    encodeURIComponent(sessionId),
  ].join(':');
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function normalizeOptionalString(value: unknown): string | null | undefined {
  if (typeof value === 'string') {
    return value;
  }
  if (value === null) {
    return null;
  }
  return undefined;
}

function normalizeEntry<TScrollAnchor = unknown>(
  value: unknown,
): SessionScopedMessagesCacheEntry<TScrollAnchor> | null {
  if (!isRecord(value)) {
    return null;
  }

  const connectionId = value.connectionId;
  const sessionId = value.sessionId;
  if (typeof connectionId !== 'string' || typeof sessionId !== 'string') {
    return null;
  }

  const messages = value.messages;
  if (!Array.isArray(messages)) {
    return null;
  }

  const cursorEventId =
    normalizeOptionalString(value.cursorEventId) ??
    normalizeOptionalString(value.eventsCursorId) ??
    null;
  const composeText =
    typeof value.composeText === 'string' ? value.composeText : undefined;
  const rangeStartText = normalizeOptionalString(value.rangeStartText);
  const rangeEndText = normalizeOptionalString(value.rangeEndText);

  return {
    connectionId,
    sessionId,
    messages: messages as IndexedMessage[],
    lastLoadedAt: typeof value.lastLoadedAt === 'number' ? value.lastLoadedAt : null,
    cursorEventId,
    // Persisted in-flight request ids cannot be resumed after app restart.
    activeRequestId: null,
    composeText,
    scrollAnchor: value.scrollAnchor as TScrollAnchor | undefined,
    rangeStartText,
    rangeEndText,
  };
}

function normalizeIndexEntry(value: unknown): SessionScopedMessagesCacheIndexEntry | null {
  if (!isRecord(value)) {
    return null;
  }
  const { connectionId, sessionId } = value;
  if (typeof connectionId !== 'string' || typeof sessionId !== 'string') {
    return null;
  }
  return { connectionId, sessionId };
}

function parseIndex(raw: string | null): SessionScopedMessagesCacheIndexEntry[] {
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }

    const seen = new Set<string>();
    const next: SessionScopedMessagesCacheIndexEntry[] = [];
    for (const item of parsed) {
      const normalized = normalizeIndexEntry(item);
      if (!normalized) {
        continue;
      }
      const dedupeKey = `${normalized.connectionId}\u0000${normalized.sessionId}`;
      if (seen.has(dedupeKey)) {
        continue;
      }
      seen.add(dedupeKey);
      next.push(normalized);
    }
    return next;
  } catch {
    return [];
  }
}

async function writeIndex(
  store: KeyValueStore,
  index: SessionScopedMessagesCacheIndexEntry[],
): Promise<void> {
  if (index.length === 0) {
    await store.delete(SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY);
    return;
  }

  await store.set(
    SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY,
    JSON.stringify(index),
  );
}

function upsertIndexEntry(
  index: SessionScopedMessagesCacheIndexEntry[],
  nextEntry: SessionScopedMessagesCacheIndexEntry,
): SessionScopedMessagesCacheIndexEntry[] {
  const existingIndex = index.findIndex(
    (entry) =>
      entry.connectionId === nextEntry.connectionId &&
      entry.sessionId === nextEntry.sessionId,
  );
  if (existingIndex >= 0) {
    const next = index.slice();
    next[existingIndex] = nextEntry;
    return next;
  }
  return [...index, nextEntry];
}

export async function loadSessionScopedMessagesCache<TScrollAnchor = unknown>(
  store: KeyValueStore,
): Promise<SessionScopedMessagesCacheHydrationResult<TScrollAnchor>> {
  const index = parseIndex(await store.get(SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY));
  const cache: SessionScopedMessagesCache<TScrollAnchor> = {};
  const hydratedIndex: SessionScopedMessagesCacheIndexEntry[] = [];

  for (const indexEntry of index) {
    const key = getSessionScopedMessagesCacheEntryKey(
      indexEntry.connectionId,
      indexEntry.sessionId,
    );
    const rawEntry = await store.get(key);
    if (!rawEntry) {
      continue;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(rawEntry);
    } catch {
      continue;
    }

    const normalized = normalizeEntry<TScrollAnchor>(parsed);
    if (
      !normalized ||
      normalized.connectionId !== indexEntry.connectionId ||
      normalized.sessionId !== indexEntry.sessionId
    ) {
      continue;
    }

    const bySession = cache[normalized.connectionId] ?? {};
    bySession[normalized.sessionId] = normalized;
    cache[normalized.connectionId] = bySession;
    hydratedIndex.push(indexEntry);
  }

  return {
    cache,
    index: hydratedIndex,
  };
}

export async function persistSessionScopedMessagesCacheEntry<
  TScrollAnchor = unknown,
>(
  store: KeyValueStore,
  params: {
    index: SessionScopedMessagesCacheIndexEntry[];
    entry: SessionScopedMessagesCacheEntry<TScrollAnchor>;
  },
): Promise<SessionScopedMessagesCacheIndexEntry[]> {
  const normalized = normalizeEntry<TScrollAnchor>(params.entry);
  if (!normalized) {
    return params.index;
  }

  const key = getSessionScopedMessagesCacheEntryKey(
    normalized.connectionId,
    normalized.sessionId,
  );
  await store.set(key, JSON.stringify(normalized));

  const nextIndex = upsertIndexEntry(params.index, {
    connectionId: normalized.connectionId,
    sessionId: normalized.sessionId,
  });
  await writeIndex(store, nextIndex);
  return nextIndex;
}

export async function deleteSessionScopedMessagesCacheEntry(
  store: KeyValueStore,
  params: {
    index: SessionScopedMessagesCacheIndexEntry[];
    connectionId: string;
    sessionId: string;
  },
): Promise<SessionScopedMessagesCacheIndexEntry[]> {
  await store.delete(
    getSessionScopedMessagesCacheEntryKey(
      params.connectionId,
      params.sessionId,
    ),
  );

  const nextIndex = params.index.filter(
    (entry) =>
      !(
        entry.connectionId === params.connectionId &&
        entry.sessionId === params.sessionId
      ),
  );
  await writeIndex(store, nextIndex);
  return nextIndex;
}

export async function deleteConnectionSessionScopedMessagesCacheEntries(
  store: KeyValueStore,
  params: {
    index: SessionScopedMessagesCacheIndexEntry[];
    connectionId: string;
  },
): Promise<SessionScopedMessagesCacheIndexEntry[]> {
  const toDelete = params.index.filter(
    (entry) => entry.connectionId === params.connectionId,
  );
  for (const entry of toDelete) {
    await store.delete(
      getSessionScopedMessagesCacheEntryKey(
        entry.connectionId,
        entry.sessionId,
      ),
    );
  }

  const nextIndex = params.index.filter(
    (entry) => entry.connectionId !== params.connectionId,
  );
  await writeIndex(store, nextIndex);
  return nextIndex;
}

export async function clearSessionScopedMessagesCache(
  store: KeyValueStore,
  params: {
    index: SessionScopedMessagesCacheIndexEntry[];
  },
): Promise<SessionScopedMessagesCacheIndexEntry[]> {
  for (const entry of params.index) {
    await store.delete(
      getSessionScopedMessagesCacheEntryKey(
        entry.connectionId,
        entry.sessionId,
      ),
    );
  }
  await store.delete(SESSION_SCOPED_MESSAGES_CACHE_INDEX_KEY);
  return [];
}