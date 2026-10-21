import { useCallback, useEffect, useRef, useState } from 'react';
import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

export function usePersistedValue<Value>(
  store: KeyValueStore,
  initial: Value,
  load: (store: KeyValueStore) => Promise<Value>,
  save: (store: KeyValueStore, value: Value) => Promise<void>,
) {
  const [value, setValue] = useState(initial);
  const [hydrated, setHydrated] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const valueRef = useRef(value);
  const hydratedRef = useRef(false);
  const writesRef = useRef<Promise<void>>(Promise.resolve());

  useEffect(() => {
    let mounted = true;
    void load(store).then(
      (loaded) => {
        if (!mounted) return;
        valueRef.current = loaded;
        hydratedRef.current = true;
        setValue(loaded);
        setHydrated(true);
      },
      (failure) => {
        if (mounted) setError(failure instanceof Error ? failure : new Error(String(failure)));
      },
    );
    return () => { mounted = false; };
  }, [load, store]);

  const update = useCallback((change: (current: Value) => Value): Promise<void> => {
    const operation = writesRef.current.catch(() => {}).then(async () => {
      if (!hydratedRef.current) throw new Error('Settings have not loaded');
      const next = change(valueRef.current);
      await save(store, next);
      valueRef.current = next;
      setValue(next);
      setError(null);
    });
    writesRef.current = operation;
    return operation;
  }, [save, store]);

  return { value, hydrated, error, update };
}