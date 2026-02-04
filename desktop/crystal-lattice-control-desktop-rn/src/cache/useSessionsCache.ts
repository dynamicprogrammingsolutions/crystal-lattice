import { useEffect, useMemo, useState } from 'react';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import type { SessionSummary } from '@crystal-lattice/frontend-sdk';

import { STORAGE_KEY_SESSIONS_CACHE } from './storageKeys';
import type { SessionsCache } from './types';

export interface UseSessionsCacheResult {
  sessionsCache: SessionsCache;
  hydrated: boolean;
  updateSessionsCache: (connectionId: string, sessions: SessionSummary[]) => void;
  deleteConnectionSessionsCache: (connectionId: string) => void;
  clearSessionsCache: () => void;
}

export function useSessionsCache(store: KeyValueStore): UseSessionsCacheResult {
  const [sessionsCache, setSessionsCache] = useState<SessionsCache>({});
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const raw = await store.get(STORAGE_KEY_SESSIONS_CACHE);
        if (!raw) {
          return;
        }
        const parsed = JSON.parse(raw) as SessionsCache;
        if (parsed && typeof parsed === 'object') {
          setSessionsCache(parsed);
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
        await store.set(STORAGE_KEY_SESSIONS_CACHE, JSON.stringify(sessionsCache));
      } catch {
      }
    };
    save();
  }, [hydrated, sessionsCache, store]);

  const updateSessionsCache = useMemo(() => {
    return (connectionId: string, sessions: SessionSummary[]) => {
      setSessionsCache((prev) => ({
        ...prev,
        [connectionId]: {
          connectionId,
          sessions,
          lastLoadedAt: Date.now(),
        },
      }));
    };
  }, []);

  const deleteConnectionSessionsCache = useMemo(() => {
    return (connectionId: string) => {
      setSessionsCache((prev) => {
        if (!(connectionId in prev)) {
          return prev;
        }
        const next = { ...prev };
        delete next[connectionId];
        return next;
      });
    };
  }, []);

  const clearSessionsCache = useMemo(() => {
    return () => {
      setSessionsCache({});
    };
  }, []);

  return {
    sessionsCache,
    hydrated,
    updateSessionsCache,
    deleteConnectionSessionsCache,
    clearSessionsCache,
  };
}
