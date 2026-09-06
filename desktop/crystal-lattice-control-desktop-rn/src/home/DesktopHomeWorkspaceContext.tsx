import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import {
  MAX_SESSION_NOTE_LENGTH,
  moveWatchedSession,
  normalizeSessionNotes,
  normalizeWatchlist,
  watchedSessionKey,
  type WatchedSessionIdentity,
} from '@crystal-lattice/frontend-rn-components';

export const DESKTOP_HOME_WATCHLIST_STORAGE_KEY =
  'clc_desktop_home_watchlist_v1';
export const DESKTOP_SESSION_NOTES_STORAGE_KEY = 'clc_desktop_session_notes_v1';

export interface DesktopHomeWorkspaceValue {
  hydrated: boolean;
  watchlist: readonly WatchedSessionIdentity[];
  notes: Readonly<Record<string, string>>;
  isWatched: (connectionId: string, sessionId: string) => boolean;
  addToWatchlist: (connectionId: string, sessionId: string) => void;
  removeFromWatchlist: (connectionId: string, sessionId: string) => void;
  moveWatchlistItem: (fromIndex: number, toIndex: number) => void;
  removeConnectionFromWatchlist: (connectionId: string) => void;
  setSessionNote: (sessionId: string, note: string) => void;
  removeSessionNote: (sessionId: string) => void;
}

const defaultValue: DesktopHomeWorkspaceValue = {
  hydrated: false,
  watchlist: [],
  notes: {},
  isWatched: () => false,
  addToWatchlist: () => {},
  removeFromWatchlist: () => {},
  moveWatchlistItem: () => {},
  removeConnectionFromWatchlist: () => {},
  setSessionNote: () => {},
  removeSessionNote: () => {},
};

const DesktopHomeWorkspaceContext =
  createContext<DesktopHomeWorkspaceValue>(defaultValue);

function parse(raw: string | null): unknown {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function DesktopHomeWorkspaceProvider({
  children,
  store,
}: {
  children: React.ReactNode;
  store: KeyValueStore;
}): React.JSX.Element {
  const [hydrated, setHydrated] = useState(false);
  const [watchlist, setWatchlist] = useState<WatchedSessionIdentity[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      store.get(DESKTOP_HOME_WATCHLIST_STORAGE_KEY),
      store.get(DESKTOP_SESSION_NOTES_STORAGE_KEY),
    ])
      .then(([watchlistRaw, notesRaw]) => {
        if (cancelled) return;
        setWatchlist(normalizeWatchlist(parse(watchlistRaw)));
        setNotes(normalizeSessionNotes(parse(notesRaw)));
      })
      .finally(() => {
        if (!cancelled) setHydrated(true);
      });
    return () => {
      cancelled = true;
    };
  }, [store]);

  useEffect(() => {
    if (!hydrated) return;
    void store.set(
      DESKTOP_HOME_WATCHLIST_STORAGE_KEY,
      JSON.stringify(watchlist),
    );
  }, [hydrated, store, watchlist]);

  useEffect(() => {
    if (!hydrated) return;
    void store.set(DESKTOP_SESSION_NOTES_STORAGE_KEY, JSON.stringify(notes));
  }, [hydrated, notes, store]);

  const isWatched = useCallback(
    (connectionId: string, sessionId: string) => {
      const key = watchedSessionKey(connectionId, sessionId);
      return watchlist.some(
        item => watchedSessionKey(item.connectionId, item.sessionId) === key,
      );
    },
    [watchlist],
  );

  const addToWatchlist = useCallback(
    (connectionId: string, sessionId: string) => {
      const key = watchedSessionKey(connectionId, sessionId);
      setWatchlist(current =>
        current.some(
          item => watchedSessionKey(item.connectionId, item.sessionId) === key,
        )
          ? current
          : [...current, { connectionId, sessionId }],
      );
    },
    [],
  );

  const removeFromWatchlist = useCallback(
    (connectionId: string, sessionId: string) => {
      const key = watchedSessionKey(connectionId, sessionId);
      setWatchlist(current =>
        current.filter(
          item => watchedSessionKey(item.connectionId, item.sessionId) !== key,
        ),
      );
    },
    [],
  );

  const moveWatchlistItem = useCallback(
    (fromIndex: number, toIndex: number) => {
      setWatchlist(current => moveWatchedSession(current, fromIndex, toIndex));
    },
    [],
  );

  const removeConnectionFromWatchlist = useCallback((connectionId: string) => {
    setWatchlist(current =>
      current.filter(item => item.connectionId !== connectionId),
    );
  }, []);

  const setSessionNote = useCallback((sessionId: string, note: string) => {
    if (!sessionId) return;
    const normalized = note.slice(0, MAX_SESSION_NOTE_LENGTH);
    setNotes(current => {
      if (!normalized.trim()) {
        if (!(sessionId in current)) return current;
        const next = { ...current };
        delete next[sessionId];
        return next;
      }
      return { ...current, [sessionId]: normalized };
    });
  }, []);

  const removeSessionNote = useCallback((sessionId: string) => {
    setNotes(current => {
      if (!(sessionId in current)) return current;
      const next = { ...current };
      delete next[sessionId];
      return next;
    });
  }, []);

  const value = useMemo<DesktopHomeWorkspaceValue>(
    () => ({
      hydrated,
      watchlist,
      notes,
      isWatched,
      addToWatchlist,
      removeFromWatchlist,
      moveWatchlistItem,
      removeConnectionFromWatchlist,
      setSessionNote,
      removeSessionNote,
    }),
    [
      addToWatchlist,
      hydrated,
      isWatched,
      moveWatchlistItem,
      notes,
      removeConnectionFromWatchlist,
      removeFromWatchlist,
      removeSessionNote,
      setSessionNote,
      watchlist,
    ],
  );

  return (
    <DesktopHomeWorkspaceContext.Provider value={value}>
      {children}
    </DesktopHomeWorkspaceContext.Provider>
  );
}

export function useDesktopHomeWorkspace(): DesktopHomeWorkspaceValue {
  return useContext(DesktopHomeWorkspaceContext);
}
