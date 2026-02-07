import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react';

import AsyncStorage from '@react-native-async-storage/async-storage';

interface PinnedEntry {
  loaded: boolean;
  pinned: string[];
  initialPinned: string[];
  migrateFromKeys: string[];
}

interface PinnedActionsContextValue {
  entries: Record<string, PinnedEntry>;
  registerKey: (storageKey: string, initialPinned: string[], migrateFromKeys: string[]) => void;
  setPinnedForKey: (storageKey: string, update: SetStateAction<string[]>) => void;
}

const PinnedActionsContext = createContext<PinnedActionsContextValue | undefined>(undefined);

function parseStringArray(raw: string | null): string[] | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return null;
    }
    return parsed.filter((item: any) => typeof item === 'string');
  } catch {
    return null;
  }
}

function sanitizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item) => typeof item === 'string');
}

export const PinnedActionsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [entries, setEntries] = useState<Record<string, PinnedEntry>>({});
  const entriesRef = useRef(entries);
  entriesRef.current = entries;

  const loadingKeysRef = useRef<Set<string>>(new Set());

  const registerKey = useCallback(
    (storageKey: string, initialPinned: string[], migrateFromKeys: string[]) => {
      const existing = entriesRef.current[storageKey];
      if (existing) {
        return;
      }

      setEntries((prev) => {
        if (prev[storageKey]) {
          return prev;
        }

        const migrateKeys = Array.isArray(migrateFromKeys)
          ? migrateFromKeys.filter((key) => typeof key === 'string' && key.length > 0 && key !== storageKey)
          : [];

        return {
          ...prev,
          [storageKey]: {
            loaded: false,
            pinned: [],
            initialPinned: sanitizeStringArray(initialPinned),
            migrateFromKeys: migrateKeys,
          },
        };
      });
    },
    [],
  );

  const setPinnedForKey = useCallback((storageKey: string, update: SetStateAction<string[]>) => {
    setEntries((prev) => {
      const existing =
        prev[storageKey] ??
        ({
          loaded: true,
          pinned: [],
          initialPinned: [],
          migrateFromKeys: [],
        } as PinnedEntry);

      const prevPinned = existing.pinned;
      const nextPinned =
        typeof update === 'function'
          ? sanitizeStringArray((update as (value: string[]) => string[])(prevPinned))
          : sanitizeStringArray(update);

      const nextEntries = {
        ...prev,
        [storageKey]: {
          ...existing,
          loaded: true,
          pinned: nextPinned,
        },
      };

      AsyncStorage.setItem(storageKey, JSON.stringify(nextPinned)).catch(() => {
        // Ignore persistence failures.
      });

      return nextEntries;
    });
  }, []);

  useEffect(() => {
    Object.entries(entries).forEach(([storageKey, entry]) => {
      if (entry.loaded) return;
      if (loadingKeysRef.current.has(storageKey)) return;

      loadingKeysRef.current.add(storageKey);

      const load = async () => {
        try {
          const raw = await AsyncStorage.getItem(storageKey);
          const parsed = parseStringArray(raw);
          if (parsed) {
            setEntries((prev) => {
              const current = prev[storageKey];
              if (!current) return prev;
              return {
                ...prev,
                [storageKey]: {
                  ...current,
                  loaded: true,
                  pinned: parsed,
                },
              };
            });
            return;
          }

          for (const migrateKey of entry.migrateFromKeys) {
            const migrateRaw = await AsyncStorage.getItem(migrateKey);
            const migrated = parseStringArray(migrateRaw);
            if (!migrated) {
              continue;
            }

            setEntries((prev) => {
              const current = prev[storageKey];
              if (!current) return prev;
              return {
                ...prev,
                [storageKey]: {
                  ...current,
                  loaded: true,
                  pinned: migrated,
                },
              };
            });

            try {
              await AsyncStorage.setItem(storageKey, JSON.stringify(migrated));
            } catch {
            }
            return;
          }

          setEntries((prev) => {
            const current = prev[storageKey];
            if (!current) return prev;
            return {
              ...prev,
              [storageKey]: {
                ...current,
                loaded: true,
                pinned: current.initialPinned,
              },
            };
          });
        } finally {
          loadingKeysRef.current.delete(storageKey);
        }
      };

      load().catch(() => {
        // Errors are handled via fallback updates.
      });
    });
  }, [entries]);

  const value = useMemo<PinnedActionsContextValue>(() => {
    return {
      entries,
      registerKey,
      setPinnedForKey,
    };
  }, [entries, registerKey, setPinnedForKey]);

  return <PinnedActionsContext.Provider value={value}>{children}</PinnedActionsContext.Provider>;
};

export function usePinnedActionsContext(): PinnedActionsContextValue {
  const ctx = useContext(PinnedActionsContext);
  if (!ctx) {
    throw new Error('usePinnedActionsContext must be used within a PinnedActionsProvider');
  }
  return ctx;
}

export function usePersistentPinnedActionsFromContext<T extends string>(
  storageKey: string,
  initialPinned: T[],
  options?: {
    migrateFromKeys?: string[];
  },
): { loaded: boolean; pinned: T[]; setPinned: Dispatch<SetStateAction<T[]>> } {
  const { entries, registerKey, setPinnedForKey } = usePinnedActionsContext();

  useEffect(() => {
    registerKey(
      storageKey,
      initialPinned as string[],
      (options?.migrateFromKeys ?? []) as string[],
    );
  }, [initialPinned, options?.migrateFromKeys, registerKey, storageKey]);

  const entry = entries[storageKey];
  const pinned = (entry ? (entry.pinned as T[]) : ([] as T[]));
  const loaded = entry ? entry.loaded : false;

  const setPinned: Dispatch<SetStateAction<T[]>> = (update) => {
    setPinnedForKey(storageKey, update as SetStateAction<string[]>);
  };

  return { loaded, pinned, setPinned };
}
