import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type Dispatch,
  type SetStateAction,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface PinnedEntry {
  loaded: boolean;
  pinned: string[];
  initialPinned: string[];
}

interface PinnedActionsContextValue {
  entries: Record<string, PinnedEntry>;
  registerKey: (storageKey: string, initialPinned: string[]) => void;
  setPinnedForKey: (storageKey: string, update: SetStateAction<string[]>) => void;
}

const PinnedActionsContext = createContext<PinnedActionsContextValue | undefined>(
  undefined,
);

export const PinnedActionsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [entries, setEntries] = useState<Record<string, PinnedEntry>>({});
  const loadingKeysRef = useRef<Set<string>>(new Set());

  const registerKey = useCallback((storageKey: string, initialPinned: string[]) => {
    setEntries((prev) => {
      if (prev[storageKey]) {
        return prev;
      }
      return {
        ...prev,
        [storageKey]: {
          loaded: false,
          pinned: [],
          initialPinned,
        },
      };
    });
  }, []);

  const setPinnedForKey = useCallback(
    (storageKey: string, update: SetStateAction<string[]>) => {
      setEntries((prev) => {
        const existing = prev[storageKey] ?? {
          loaded: true,
          pinned: [],
          initialPinned: [],
        };
        const prevPinned = existing.pinned;
        const nextPinned =
          typeof update === 'function'
            ? (update as (value: string[]) => string[])(prevPinned)
            : (update as string[]);
        const nextEntries = {
          ...prev,
          [storageKey]: {
            ...existing,
            loaded: true,
            pinned: nextPinned,
          },
        };

        // Persist asynchronously; failures are logged but do not
        // block UI updates.
        AsyncStorage.setItem(storageKey, JSON.stringify(nextPinned)).catch((err) => {
          console.log(`Failed to save pinned actions for ${storageKey}`, err);
        });

        return nextEntries;
      });
    },
    [],
  );

  // Load any entries that are registered but not yet loaded. We do
  // this centrally so each storageKey is only read from
  // AsyncStorage once per app run.
  useEffect(() => {
    Object.entries(entries).forEach(([storageKey, entry]) => {
      if (entry.loaded) return;
      if (loadingKeysRef.current.has(storageKey)) return;

      loadingKeysRef.current.add(storageKey);

      const load = async () => {
        try {
          const raw = await AsyncStorage.getItem(storageKey);
          if (raw) {
            try {
              const parsed = JSON.parse(raw);
              if (Array.isArray(parsed)) {
                const valid = parsed.filter((key: any) => typeof key === 'string');
                const nextPinned = (valid.length > 0 || parsed.length === 0
                  ? (valid as string[])
                  : []) as string[];
                setEntries((prev) => {
                  const current = prev[storageKey];
                  if (!current) return prev;
                  return {
                    ...prev,
                    [storageKey]: {
                      ...current,
                      loaded: true,
                      pinned: nextPinned,
                    },
                  };
                });
                return;
              }
            } catch (err) {
              console.log(`Failed to parse stored pinned actions for ${storageKey}`, err);
            }
          }

          // No stored value (or parse failed): use initialPinned as
          // the default once we've "loaded".
          setEntries((prev) => {
            const current = prev[storageKey];
            if (!current) return prev;
            return {
              ...prev,
              [storageKey]: {
                ...current,
                loaded: true,
                pinned: current.initialPinned ?? [],
              },
            };
          });
        } catch (err) {
          console.log(`Failed to load pinned actions for ${storageKey}`, err);
          setEntries((prev) => {
            const current = prev[storageKey];
            if (!current) return prev;
            return {
              ...prev,
              [storageKey]: {
                ...current,
                loaded: true,
                pinned: [],
              },
            };
          });
        } finally {
          loadingKeysRef.current.delete(storageKey);
        }
      };

      load().catch(() => {
        // Errors are logged above.
      });
    });
  }, [entries]);

  const value: PinnedActionsContextValue = {
    entries,
    registerKey,
    setPinnedForKey,
  };

  return (
    <PinnedActionsContext.Provider value={value}>{children}</PinnedActionsContext.Provider>
  );
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
): { pinned: T[]; setPinned: Dispatch<SetStateAction<T[]>> } {
  const { entries, registerKey, setPinnedForKey } = usePinnedActionsContext();

  // Ensure this storageKey is known to the provider and has an
  // associated initialPinned default. This side-effect is safe
  // inside the hook; it just seeds the provider's state.
  useEffect(() => {
    registerKey(storageKey, initialPinned as string[]);
  }, [storageKey, initialPinned, registerKey]);

  const entry = entries[storageKey];
  const pinned = (entry ? (entry.pinned as T[]) : ([] as T[]));

  const setPinned: Dispatch<SetStateAction<T[]>> = (update) => {
    setPinnedForKey(storageKey, update as SetStateAction<string[]>);
  };

  return { pinned, setPinned };
}
