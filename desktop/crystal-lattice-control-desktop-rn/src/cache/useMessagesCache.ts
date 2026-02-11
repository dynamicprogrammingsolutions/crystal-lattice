import { useEffect, useMemo, useState } from 'react';

import type { IndexedMessage, KeyValueStore } from '@crystal-lattice/frontend-sdk';

import { STORAGE_KEY_MESSAGES_CACHE } from './storageKeys';
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
  }) => void;
  deleteConnectionMessagesCache: (connectionId: string) => void;
  clearMessagesCache: () => void;
}

export function useMessagesCache(store: KeyValueStore): UseMessagesCacheResult {
  const [messagesCache, setMessagesCache] = useState<MessagesCache>({});
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const raw = await store.get(STORAGE_KEY_MESSAGES_CACHE);
        if (!raw) {
          return;
        }
        const parsed = JSON.parse(raw) as MessagesCache;
        if (parsed && typeof parsed === 'object') {
          setMessagesCache(parsed);
        }
      } catch {
      } finally {
        setHydrated(true);
      }
    };

    load();
  }, [store]);

  useEffect(() => {
    if (!hydrated) return;
    const save = async () => {
      try {
        await store.set(STORAGE_KEY_MESSAGES_CACHE, JSON.stringify(messagesCache));
      } catch {
      }
    };
    save();
  }, [hydrated, messagesCache, store]);

  const updateMessagesCache = useMemo(() => {
    return (params: {
      connectionId: string;
      sessionId: string;
      messages: IndexedMessage[];
      cursorEventId?: string | null;
      activeRequestId?: string | null;
      rangeStartText?: string | null;
      rangeEndText?: string | null;
    }) => {
      setMessagesCache((prev) => {
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
          cursorEventId: params.cursorEventId ?? existing?.cursorEventId ?? null,
          activeRequestId: params.activeRequestId ?? existing?.activeRequestId ?? null,
          rangeStartText: params.rangeStartText ?? existing?.rangeStartText ?? null,
          rangeEndText: params.rangeEndText ?? existing?.rangeEndText ?? null,
        };

        const nextBySession: MessagesBySession = {
          ...bySession,
          [params.sessionId]: entry,
        };

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
            delete nextBySession[old.sessionId];
          }
        }

        return {
          ...prev,
          [params.connectionId]: nextBySession,
        };
      });
    };
  }, []);

  const clearMessagesCache = useMemo(() => {
    return () => {
      setMessagesCache({});
    };
  }, []);

  const deleteConnectionMessagesCache = useMemo(() => {
    return (connectionId: string) => {
      setMessagesCache((prev) => {
        if (!(connectionId in prev)) {
          return prev;
        }
        const next = { ...prev };
        delete next[connectionId];
        return next;
      });
    };
  }, []);

  return {
    messagesCache,
    hydrated,
    updateMessagesCache,
    deleteConnectionMessagesCache,
    clearMessagesCache,
  };
}
