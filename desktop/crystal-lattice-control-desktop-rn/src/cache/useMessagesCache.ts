import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

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
import type {
  MessagesBySession,
  MessagesCache,
  MessagesCacheEntry,
} from './types';

const MAX_CACHED_SESSIONS_PER_CONNECTION = 50;

export interface UseMessagesCacheResult {
  messagesCache: MessagesCache;
  hydrated: boolean;
  updateMessagesCache: (params: {
    connectionId: string;
    sessionId: string;
    messages: IndexedMessage[];
    cursorEventId?: string | null;
    activeRequestId?: string | null;
    rangeStartText?: string | null;
    rangeEndText?: string | null;
    composeText?: string;
    scrollAnchor?: unknown;
  }) => void;
  deleteConnectionMessagesCache: (connectionId: string) => void;
  clearMessagesCache: () => void;
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
        const loaded = await loadSessionScopedMessagesCache(store);
        if (cancelled) {
          return;
        }
        indexRef.current = loaded.index;
        commitMessagesCache(loaded.cache);
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

  const updateMessagesCache = useCallback((params: {
    connectionId: string;
    sessionId: string;
    messages: IndexedMessage[];
    cursorEventId?: string | null;
    activeRequestId?: string | null;
    rangeStartText?: string | null;
    rangeEndText?: string | null;
    composeText?: string;
    scrollAnchor?: unknown;
  }) => {
    const prev = messagesCacheRef.current;
    const bySession = prev[params.connectionId] ?? {};
    const existing = bySession[params.sessionId];

    const entry: MessagesCacheEntry = {
      ...(existing ?? {
        connectionId: params.connectionId,
        sessionId: params.sessionId,
        lastLoadedAt: null,
        messages: [],
      }),
      connectionId: params.connectionId,
      sessionId: params.sessionId,
      messages: params.messages,
      lastLoadedAt: Date.now(),
      cursorEventId: params.cursorEventId === undefined
        ? existing?.cursorEventId ?? null
        : params.cursorEventId,
      activeRequestId: params.activeRequestId === undefined
        ? existing?.activeRequestId ?? null
        : params.activeRequestId,
      rangeStartText: params.rangeStartText ?? existing?.rangeStartText ?? null,
      rangeEndText: params.rangeEndText ?? existing?.rangeEndText ?? null,
      composeText: params.composeText ?? existing?.composeText,
      scrollAnchor: params.scrollAnchor ?? existing?.scrollAnchor,
    };

    const nextBySession: MessagesBySession = {
      ...bySession,
      [params.sessionId]: entry,
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
      [params.connectionId]: nextBySession,
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

  const deleteConnectionMessagesCache = useMemo(() => {
    return (connectionId: string) => {
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
    };
  }, [commitMessagesCache, enqueuePersistence, store]);

  return {
    messagesCache,
    hydrated,
    updateMessagesCache,
    deleteConnectionMessagesCache,
    clearMessagesCache,
  };
}
