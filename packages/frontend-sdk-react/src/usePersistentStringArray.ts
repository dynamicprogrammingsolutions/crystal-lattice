import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from 'react';

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
  hasStoredPreference: boolean;
  setValue: Dispatch<SetStateAction<string[]>>;
}

export function parsePersistentStringArray(raw: string | null): string[] | null {
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

function arraysEqual(left: readonly string[], right: readonly string[]): boolean {
  return left.length === right.length && left.every((item, index) => item === right[index]);
}

export function resolveDefaultPersistentStringArray(options: {
  current: readonly string[];
  initial: readonly string[];
  hasStoredPreference: boolean;
}): string[] {
  if (options.hasStoredPreference || arraysEqual(options.current, options.initial)) {
    return options.current as string[];
  }
  return [...options.initial];
}

export function usePersistentStringArray(options: UsePersistentStringArrayOptions): UsePersistentStringArrayResult {
  const { store, key, initial, migrateFromKeys } = options;

  const initialForKey = initial.filter((item) => typeof item === 'string');

  const [loaded, setLoaded] = useState(false);
  const [value, setValue] = useState<string[]>(initialForKey);
  const [hasStoredPreference, setHasStoredPreference] = useState(false);
  const valueRef = useRef(value);
  const initialRef = useRef(initialForKey);
  initialRef.current = initialForKey;

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  const migrateKeys = useMemo(
    () => (Array.isArray(migrateFromKeys) ? migrateFromKeys.filter(Boolean) : []),
    [Array.isArray(migrateFromKeys) ? migrateFromKeys.filter(Boolean).join('\u0000') : ''],
  );

  useEffect(() => {
    setLoaded(false);
    setValue(initialRef.current);
    setHasStoredPreference(false);
  }, [key]);

  useEffect(() => {
    if (!hasStoredPreference) {
      setValue((current) =>
        resolveDefaultPersistentStringArray({
          current,
          initial: initialForKey,
          hasStoredPreference,
        }),
      );
    }
  }, [hasStoredPreference, initial]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const raw = await store.get(key);
        const parsed = parsePersistentStringArray(raw);
        if (parsed !== null) {
          if (!cancelled) {
            setValue(parsed);
            setHasStoredPreference(true);
          }
          return;
        }

        for (const migrateKey of migrateKeys) {
          if (!migrateKey || migrateKey === key) continue;
          const migrateRaw = await store.get(migrateKey);
          const migrated = parsePersistentStringArray(migrateRaw);
          if (migrated === null) {
            continue;
          }

          if (!cancelled) {
            setValue(migrated);
            setHasStoredPreference(true);
          }
          try {
            await store.set(key, JSON.stringify(migrated));
          } catch {
          }
          return;
        }

        if (!cancelled) {
          setValue(initialRef.current);
          setHasStoredPreference(false);
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

  const setValueSafe = useCallback<Dispatch<SetStateAction<string[]>>>(
    (update) => {
      const current = valueRef.current;
      const next = typeof update === 'function' ? (update as any)(current) : update;
      const list = Array.isArray(next) ? next.filter((item) => typeof item === 'string') : [];
      valueRef.current = list;
      setValue(list);
      setHasStoredPreference(true);
      store.set(key, JSON.stringify(list)).catch(() => {
        // Ignore persistence failures and keep the current session's choice.
      });
    },
    [key, store],
  );

  return { loaded, value, hasStoredPreference, setValue: setValueSafe };
}
