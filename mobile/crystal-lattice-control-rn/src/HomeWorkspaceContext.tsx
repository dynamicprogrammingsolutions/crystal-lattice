import AsyncStorage from '@react-native-async-storage/async-storage';
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
  DEFAULT_MOBILE_GLOBAL_PREFERENCES,
  HOME_WATCHLIST_STORAGE_KEY,
  MAX_SESSION_NOTE_LENGTH,
  MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY,
  SESSION_NOTES_STORAGE_KEY,
  moveWatchedSession,
  normalizeMobileGlobalPreferences,
  normalizeSessionNotes,
  normalizeWatchlist,
  watchedSessionKey,
  type RecentSessionsWindow,
  type WatchedSessionIdentity,
} from './homeWorkspaceState';

interface HomeWorkspaceValue {
  hydrated: boolean;
  watchlist: readonly WatchedSessionIdentity[];
  notes: Readonly<Record<string, string>>;
  recentSessionsWindow: RecentSessionsWindow;
  timeTrackingEnabled: boolean;
  timeTrackingPluginId: string;
  isWatched: (connectionId: string, sessionId: string) => boolean;
  addToWatchlist: (connectionId: string, sessionId: string) => void;
  removeFromWatchlist: (connectionId: string, sessionId: string) => void;
  moveWatchlistItem: (fromIndex: number, toIndex: number) => void;
  setSessionNote: (sessionId: string, note: string) => void;
  removeSessionNote: (sessionId: string) => void;
  setRecentSessionsWindow: (value: RecentSessionsWindow) => void;
  setTimeTrackingEnabled: (value: boolean) => void;
  setTimeTrackingPluginId: (value: string) => void;
}

const defaultValue: HomeWorkspaceValue = {
  hydrated: false,
  watchlist: [],
  notes: {},
  recentSessionsWindow: DEFAULT_MOBILE_GLOBAL_PREFERENCES.recentSessionsWindow,
  timeTrackingEnabled: DEFAULT_MOBILE_GLOBAL_PREFERENCES.timeTrackingEnabled,
  timeTrackingPluginId: DEFAULT_MOBILE_GLOBAL_PREFERENCES.timeTrackingPluginId,
  isWatched: () => false,
  addToWatchlist: () => {},
  removeFromWatchlist: () => {},
  moveWatchlistItem: () => {},
  setSessionNote: () => {},
  removeSessionNote: () => {},
  setRecentSessionsWindow: () => {},
  setTimeTrackingEnabled: () => {},
  setTimeTrackingPluginId: () => {},
};

const HomeWorkspaceContext = createContext<HomeWorkspaceValue>(defaultValue);

const asyncStorage: KeyValueStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};

export const HomeWorkspaceProvider: React.FC<{
  children: React.ReactNode;
  store?: KeyValueStore;
}> = ({ children, store = asyncStorage }) => {
  const [hydrated, setHydrated] = useState(false);
  const [watchlist, setWatchlist] = useState<WatchedSessionIdentity[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [recentSessionsWindow, setRecentSessionsWindowState] =
    useState<RecentSessionsWindow>(
      DEFAULT_MOBILE_GLOBAL_PREFERENCES.recentSessionsWindow,
    );
  const [timeTrackingEnabled, setTimeTrackingEnabledState] =
    useState<boolean>(
      DEFAULT_MOBILE_GLOBAL_PREFERENCES.timeTrackingEnabled,
    );
  const [timeTrackingPluginId, setTimeTrackingPluginIdState] =
    useState<string>(
      DEFAULT_MOBILE_GLOBAL_PREFERENCES.timeTrackingPluginId,
    );

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      store.get(HOME_WATCHLIST_STORAGE_KEY),
      store.get(SESSION_NOTES_STORAGE_KEY),
      store.get(MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY),
    ])
      .then(([watchlistRaw, notesRaw, preferencesRaw]) => {
        if (cancelled) return;
        const parse = (raw: string | null): unknown => {
          if (!raw) return null;
          try {
            return JSON.parse(raw);
          } catch {
            return null;
          }
        };
        setWatchlist(normalizeWatchlist(parse(watchlistRaw)));
        setNotes(normalizeSessionNotes(parse(notesRaw)));
        const preferences = normalizeMobileGlobalPreferences(
          parse(preferencesRaw),
        );
        setRecentSessionsWindowState(preferences.recentSessionsWindow);
        setTimeTrackingEnabledState(preferences.timeTrackingEnabled);
        setTimeTrackingPluginIdState(preferences.timeTrackingPluginId);
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
    void store.set(HOME_WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist));
  }, [hydrated, store, watchlist]);

  useEffect(() => {
    if (!hydrated) return;
    void store.set(SESSION_NOTES_STORAGE_KEY, JSON.stringify(notes));
  }, [hydrated, notes, store]);

  useEffect(() => {
    if (!hydrated) return;
    void store.set(
      MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY,
      JSON.stringify({
        recentSessionsWindow,
        timeTrackingEnabled,
        timeTrackingPluginId,
      }),
    );
  }, [hydrated, recentSessionsWindow, store, timeTrackingEnabled, timeTrackingPluginId]);

  const isWatched = useCallback(
    (connectionId: string, sessionId: string) => {
      const key = watchedSessionKey(connectionId, sessionId);
      return watchlist.some(
        (item) => watchedSessionKey(item.connectionId, item.sessionId) === key,
      );
    },
    [watchlist],
  );

  const addToWatchlist = useCallback(
    (connectionId: string, sessionId: string) => {
      const key = watchedSessionKey(connectionId, sessionId);
      setWatchlist((current) =>
        current.some(
          (item) => watchedSessionKey(item.connectionId, item.sessionId) === key,
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
      setWatchlist((current) =>
        current.filter(
          (item) => watchedSessionKey(item.connectionId, item.sessionId) !== key,
        ),
      );
    },
    [],
  );

  const moveWatchlistItem = useCallback((fromIndex: number, toIndex: number) => {
    setWatchlist((current) => moveWatchedSession(current, fromIndex, toIndex));
  }, []);

  const setSessionNote = useCallback((sessionId: string, note: string) => {
    if (!sessionId) return;
    const normalized = note.slice(0, MAX_SESSION_NOTE_LENGTH);
    setNotes((current) => {
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
    setNotes((current) => {
      if (!(sessionId in current)) return current;
      const next = { ...current };
      delete next[sessionId];
      return next;
    });
  }, []);

  const setRecentSessionsWindow = useCallback((value: RecentSessionsWindow) => {
    setRecentSessionsWindowState(value);
  }, []);

  const setTimeTrackingEnabled = useCallback((value: boolean) => {
    setTimeTrackingEnabledState(value);
  }, []);

  const setTimeTrackingPluginId = useCallback((value: string) => {
    setTimeTrackingPluginIdState(value);
  }, []);

  const value = useMemo<HomeWorkspaceValue>(
    () => ({
      hydrated,
      watchlist,
      notes,
      recentSessionsWindow,
      timeTrackingEnabled,
      timeTrackingPluginId,
      isWatched,
      addToWatchlist,
      removeFromWatchlist,
      moveWatchlistItem,
      setSessionNote,
      removeSessionNote,
      setRecentSessionsWindow,
      setTimeTrackingEnabled,
      setTimeTrackingPluginId,
    }),
    [
      addToWatchlist,
      hydrated,
      isWatched,
      moveWatchlistItem,
      notes,
      recentSessionsWindow,
      removeFromWatchlist,
      removeSessionNote,
      setRecentSessionsWindow,
      setSessionNote,
      setTimeTrackingEnabled,
      setTimeTrackingPluginId,
      timeTrackingEnabled,
      timeTrackingPluginId,
      watchlist,
    ],
  );

  return (
    <HomeWorkspaceContext.Provider value={value}>
      {children}
    </HomeWorkspaceContext.Provider>
  );
};

export function useHomeWorkspace(): HomeWorkspaceValue {
  return useContext(HomeWorkspaceContext);
}