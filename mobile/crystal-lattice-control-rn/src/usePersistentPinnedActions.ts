import { useEffect, type Dispatch, type SetStateAction } from 'react';

import { usePersistentPinnedActionsFromContext } from './PinnedActionsContext';

export interface UsePersistentPinnedActionsResult<T extends string> {
  loaded: boolean;
  pinned: T[];
  setPinned: Dispatch<SetStateAction<T[]>>;
}

export function usePersistentPinnedActions<T extends string>(
  storageKey: string,
  initialPinned: T[],
  options?: {
    migrateFromKeys?: string[];
  },
): UsePersistentPinnedActionsResult<T> {
  const { pinned, setPinned, loaded } = usePersistentPinnedActionsFromContext<T>(
    storageKey,
    initialPinned,
    options,
  );

  useEffect(() => {
    // Ensure React tracks the dependency on initialPinned.
  }, [initialPinned]);

  return { pinned, setPinned, loaded };
}

