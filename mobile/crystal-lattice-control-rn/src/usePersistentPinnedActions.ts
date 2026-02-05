import type { Dispatch, SetStateAction } from 'react';

import { usePersistentPinnedActions as usePersistentPinnedActionsFromStore } from '@crystal-lattice/frontend-sdk-react';

import { asyncStorageKeyValueStore } from './storage/asyncStorageKeyValueStore';

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
  const { pinned, setPinned, loaded } = usePersistentPinnedActionsFromStore<T>({
    store: asyncStorageKeyValueStore,
    key: storageKey,
    initialPinned,
    migrateFromKeys: options?.migrateFromKeys,
  });

  return { pinned, setPinned, loaded };
}

