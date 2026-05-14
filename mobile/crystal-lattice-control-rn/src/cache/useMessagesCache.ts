import { useCallback, useEffect, useRef, useState } from 'react';

import type {
  IndexedMessage,
  KeyValueStore,
  SessionScopedMessagesCacheIndexEntry,
} from '@crystal-lattice/frontend-sdk';
import {
  clearSessionScopedMessagesCache,
  deleteConnectionSessionScopedMessagesCacheEntries,
  deleteSessionScopedMessagesCacheEntry,
  loadSessionScopedMessagesCache,
  persistSessionScopedMessagesCacheEntry,
} from '@crystal-lattice/frontend-sdk';

import type { ChatScrollAnchor } from '../chatScroll';
import type {
  MessagesBySession,
  MessagesCache,
  MessagesCacheEntry,
} from './types';

const MAX_CACHED_SESSIONS_PER_CONNECTION = 10;

export interface UseMessagesCacheResult {
  messagesCache: MessagesCache;
  hydrated: boolean;
  updateMessagesCache: (
    connectionId: string,
    sessionId: string,
    messages: IndexedMessage[],
    eventsCursorId: string | null,
    activeRequestId: string | null,
  ) => void;
  saveMessagesComposeText: (
    connectionId: string,
    sessionId: string,
    composeText: string,
  ) => void;
  saveMessagesScrollAnchor: (
    connectionId: string,
    sessionId: string,
    scrollAnchor: ChatScrollAnchor,
  ) => void;
  deleteConnectionMessagesCache: (connectionId: string) => void;
  clearMessagesCache: () => void;
}

function hydrateMobileEntry(
  entry: MessagesCacheEntry,
): MessagesCacheEntry {
  return {
    ...entry,
    eventsCursorId: entry.cursorEventId ?? null,
  };
}

export function useMessagesCache(store: KeyValueStore): UseMessagesCacheResult {
  const [messagesCache, setMessagesCache] = useState<MessagesCache>({});
  const [hydrated, setHydrated] = useState(false);
  const messagesCacheRef = useRef<MessagesCache>({});
  const hydratedRef = useRef(false);
  const indexRef = useRef<SessionScopedMessagesCacheIndexEntry[]>([]);
  const pendingOpsRef = useRef<Array<() => Promise<void>>>([]);
  const persistenceChainRef = useRef<Promise<void>>(Promise.resolve());

  const commitMessagesCache = useCallback((next: MessagesCache) => {
    messagesCacheRef.current = next;
    setMessagesCache(next);
  }, []);

  const enqueuePersistence = useCallback((operation: () => Promise<void>) => {
    if (!hydratedRef.current) {
      pendingOpsRef.current.push(operation);
      return;
    }

    persistenceChainRef.current = persistenceChainRef.current
      .then(operation)
      .catch(() => {});
  }, []);

  const flushPendingPersistence = useCallback(() => {
    if (!hydratedRef.current || pendingOpsRef.current.length === 0) {
      return;
    }

    const pending = pendingOpsRef.current;
    pendingOpsRef.current = [];
    for (const operation of pending) {
      enqueuePersistence(operation);
    }
  }, [enqueuePersistence]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const loaded = await loadSessionScopedMessagesCache<ChatScrollAnchor>(store);
        if (cancelled) {
          return;
        }

        const nextCache: MessagesCache = {};
        for (const [connectionId, bySession] of Object.entries(loaded.cache)) {
          const nextBySession: MessagesBySession = {};
          for (const [sessionId, entry] of Object.entries(bySession)) {
            nextBySession[sessionId] = hydrateMobileEntry(entry as MessagesCacheEntry);
          }
          nextCache[connectionId] = nextBySession;
        }

        indexRef.current = loaded.index;
        commitMessagesCache(nextCache);
      } catch {
      } finally {
        if (cancelled) {
          return;
        }
        hydratedRef.current = true;
        setHydrated(true);
        flushPendingPersistence();
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [commitMessagesCache, flushPendingPersistence, store]);

  const updateMessagesCache = useCallback((
    connectionId: string,
    sessionId: string,
    messages: IndexedMessage[],
    eventsCursorId: string | null,
    activeRequestId: string | null,
  ) => {
    const prev = messagesCacheRef.current;
    const bySession = prev[connectionId] ?? {};
    const existing = bySession[sessionId];

    const entry: MessagesCacheEntry = {
      ...(existing ?? {
        connectionId,
        sessionId,
        messages: [],
        lastLoadedAt: null,
      }),
      connectionId,
      sessionId,
      messages,
      lastLoadedAt: Date.now(),
      cursorEventId: eventsCursorId,
      eventsCursorId,
      activeRequestId,
    };

    const nextBySession: MessagesBySession = {
      ...bySession,
      [sessionId]: entry,
    };

    const evictedEntries: MessagesCacheEntry[] = [];
    const sessionIds = Object.keys(nextBySession);
    if (sessionIds.length > MAX_CACHED_SESSIONS_PER_CONNECTION) {
      const sortedByAge = sessionIds
        .map((id) => nextBySession[id])
        .sort((a, b) => (a.lastLoadedAt ?? 0) - (b.lastLoadedAt ?? 0));
      const toDrop = sortedByAge.slice(
        0,
        sessionIds.length - MAX_CACHED_SESSIONS_PER_CONNECTION,
      );
      for (const old of toDrop) {
        evictedEntries.push(old);
        delete nextBySession[old.sessionId];
      }
    }

    const nextCache: MessagesCache = {
      ...prev,
      [connectionId]: nextBySession,
    };
    commitMessagesCache(nextCache);

    enqueuePersistence(async () => {
      try {
        let nextIndex = indexRef.current;
        for (const old of evictedEntries) {
          nextIndex = await deleteSessionScopedMessagesCacheEntry(store, {
            index: nextIndex,
            connectionId: old.connectionId,
            sessionId: old.sessionId,
          });
        }
        nextIndex = await persistSessionScopedMessagesCacheEntry(store, {
          index: nextIndex,
          entry,
        });
        indexRef.current = nextIndex;
      } catch {
      }
    });
  }, [commitMessagesCache, enqueuePersistence, store]);

  const saveMessagesComposeText = useCallback((
    connectionId: string,
    sessionId: string,
    composeText: string,
  ) => {
    const prev = messagesCacheRef.current;
    const bySession = prev[connectionId] ?? {};
    const existing = bySession[sessionId];

    const entry: MessagesCacheEntry = existing
      ? {
          ...existing,
          composeText,
        }
      : {
          connectionId,
          sessionId,
          messages: [],
          lastLoadedAt: null,
          composeText,
          cursorEventId: null,
          eventsCursorId: null,
          activeRequestId: null,
        };

    const nextCache: MessagesCache = {
      ...prev,
      [connectionId]: {
        ...bySession,
        [sessionId]: entry,
      },
    };
    commitMessagesCache(nextCache);

    enqueuePersistence(async () => {
      try {
        indexRef.current = await persistSessionScopedMessagesCacheEntry(store, {
          index: indexRef.current,
          entry,
        });
      } catch {
      }
    });
  }, [commitMessagesCache, enqueuePersistence, store]);

  const saveMessagesScrollAnchor = useCallback((
    connectionId: string,
    sessionId: string,
    scrollAnchor: ChatScrollAnchor,
  ) => {
    const prev = messagesCacheRef.current;
    const bySession = prev[connectionId] ?? {};
    const existing = bySession[sessionId];

    const entry: MessagesCacheEntry = existing
      ? {
          ...existing,
          scrollAnchor,
        }
      : {
          connectionId,
          sessionId,
          messages: [],
          lastLoadedAt: null,
          composeText: '',
          scrollAnchor,
          cursorEventId: null,
          eventsCursorId: null,
          activeRequestId: null,
        };

    const nextCache: MessagesCache = {
      ...prev,
      [connectionId]: {
        ...bySession,
        [sessionId]: entry,
      },
    };
    commitMessagesCache(nextCache);

    enqueuePersistence(async () => {
      try {
        indexRef.current = await persistSessionScopedMessagesCacheEntry(store, {
          index: indexRef.current,
          entry,
        });
      } catch {
      }
    });
  }, [commitMessagesCache, enqueuePersistence, store]);

  const deleteConnectionMessagesCache = useCallback((connectionId: string) => {
    const prev = messagesCacheRef.current;
    if (!(connectionId in prev)) {
      return;
    }

    const next = { ...prev };
    delete next[connectionId];
    commitMessagesCache(next);

    enqueuePersistence(async () => {
      try {
        indexRef.current =
          await deleteConnectionSessionScopedMessagesCacheEntries(store, {
            index: indexRef.current,
            connectionId,
          });
      } catch {
      }
    });
  }, [commitMessagesCache, enqueuePersistence, store]);

  const clearMessagesCache = useCallback(() => {
    commitMessagesCache({});
    enqueuePersistence(async () => {
      try {
        indexRef.current = await clearSessionScopedMessagesCache(store, {
          index: indexRef.current,
        });
      } catch {
      }
    });
  }, [commitMessagesCache, enqueuePersistence, store]);

  return {
    messagesCache,
    hydrated,
    updateMessagesCache,
    saveMessagesComposeText,
    saveMessagesScrollAnchor,
    deleteConnectionMessagesCache,
    clearMessagesCache,
  };
}