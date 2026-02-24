import { useCallback, useEffect, useMemo, useState, type Dispatch, type SetStateAction } from 'react';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

export interface UsePersistentStringArrayOptions {
  store: KeyValueStore;
  key: string;
  initial: string[];
  migrateFromKeys?: string[];
}

export interface UsePersistentStringArrayResult {
  loaded: boolean;
  value: string[];
  setValue: Dispatch<SetStateAction<string[]>>;
}

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

export function usePersistentStringArray(options: UsePersistentStringArrayOptions): UsePersistentStringArrayResult {
  const { store, key, initial, migrateFromKeys } = options;

  const initialForKey = useMemo(() => initial, [key]);

  const [loaded, setLoaded] = useState(false);
  const [value, setValue] = useState<string[]>(initialForKey);

  const migrateKeys = useMemo(
    () => (Array.isArray(migrateFromKeys) ? migrateFromKeys.filter(Boolean) : []),
    [migrateFromKeys],
  );

  useEffect(() => {
    setLoaded(false);
    setValue(initialForKey);
  }, [initialForKey, key]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const raw = await store.get(key);
        const parsed = parseStringArray(raw);
        if (parsed) {
          if (!cancelled) {
            setValue(parsed);
          }
          return;
        }

        for (const migrateKey of migrateKeys) {
          if (!migrateKey || migrateKey === key) continue;
          const migrateRaw = await store.get(migrateKey);
          const migrated = parseStringArray(migrateRaw);
          if (!migrated) {
            continue;
          }

          if (!cancelled) {
            setValue(migrated);
          }
          try {
            await store.set(key, JSON.stringify(migrated));
          } catch {
          }
          return;
        }
      } finally {
        if (!cancelled) {
          setLoaded(true);
        }
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [key, migrateKeys, store]);

  useEffect(() => {
    if (!loaded) {
      return;
    }

    const save = async () => {
      try {
        await store.set(key, JSON.stringify(value));
      } catch {
      }
    };

    save();
  }, [key, loaded, store, value]);

  const setValueSafe = useCallback<Dispatch<SetStateAction<string[]>>>(
    (update) => {
      setValue((prev) => {
        const next = typeof update === 'function' ? (update as any)(prev) : update;
        const list = Array.isArray(next) ? next.filter((item) => typeof item === 'string') : [];
        return list;
      });
    },
    [],
  );

  return { loaded, value, setValue: setValueSafe };
}
