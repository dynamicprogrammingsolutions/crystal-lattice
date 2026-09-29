import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from 'react';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import { usePersistentPinnedActions } from '@crystal-lattice/frontend-sdk-react';

import { desktopEventBus } from '../events/desktopEventBus';

function sanitizePinned<T extends string>(value: unknown): T[] {
  return Array.isArray(value)
    ? (value.filter(item => typeof item === 'string') as T[])
    : [];
}

function pinnedEqual(
  left: readonly string[],
  right: readonly string[],
): boolean {
  return (
    left.length === right.length &&
    left.every((value, index) => value === right[index])
  );
}

export function useSynchronizedPersistentPinnedActions<T extends string>({
  store,
  key,
  initialPinned,
}: {
  store: KeyValueStore;
  key: string;
  initialPinned: T[];
}): {
  loaded: boolean;
  pinned: T[];
  hasStoredPreference: boolean;
  setPinned: Dispatch<SetStateAction<T[]>>;
} {
  const {
    loaded: persistedLoaded,
    pinned: persistedPinned,
    hasStoredPreference: hasPersistedPreference,
    setPinned: persistPinned,
  } = usePersistentPinnedActions<T>({ store, key, initialPinned });
  const [pinned, setPinnedState] = useState<T[]>(persistedPinned);
  const [hasLivePreference, setHasLivePreference] = useState(false);
  const pinnedRef = useRef(pinned);
  const sourceRef = useRef(Symbol('desktop-pinned-actions'));

  pinnedRef.current = pinned;

  useEffect(() => {
    setHasLivePreference(false);
  }, [key]);

  useEffect(() => {
    return desktopEventBus.subscribe('pinnedActionsChanged', payload => {
      if (payload.storageKey !== key || payload.source === sourceRef.current) {
        return;
      }
      const next = sanitizePinned<T>(payload.pinned);
      pinnedRef.current = next;
      setHasLivePreference(true);
      setPinnedState(current => (pinnedEqual(current, next) ? current : next));
    });
  }, [key]);

  useEffect(() => {
    if (hasLivePreference) {
      return;
    }
    const next = persistedPinned;
    pinnedRef.current = next;
    setPinnedState(current => (pinnedEqual(current, next) ? current : next));
  }, [hasLivePreference, persistedPinned]);

  const setPinned = useCallback<Dispatch<SetStateAction<T[]>>>(
    update => {
      const next = sanitizePinned<T>(
        typeof update === 'function'
          ? (update as (current: T[]) => T[])(pinnedRef.current)
          : update,
      );
      pinnedRef.current = next;
      setHasLivePreference(true);
      setPinnedState(next);
      persistPinned(next);
      desktopEventBus.publish('pinnedActionsChanged', {
        storageKey: key,
        pinned: next,
        source: sourceRef.current,
      });
    },
    [key, persistPinned],
  );

  return {
    loaded: persistedLoaded || hasLivePreference,
    pinned,
    hasStoredPreference: hasPersistedPreference || hasLivePreference,
    setPinned,
  };
}
