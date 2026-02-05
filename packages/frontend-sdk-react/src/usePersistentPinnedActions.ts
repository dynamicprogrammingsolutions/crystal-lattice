import type { Dispatch, SetStateAction } from 'react';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

import { usePersistentStringArray } from './usePersistentStringArray';

export interface UsePersistentPinnedActionsOptions<T extends string> {
  store: KeyValueStore;
  key: string;
  initialPinned: T[];
  migrateFromKeys?: string[];
}

export interface UsePersistentPinnedActionsResult<T extends string> {
  loaded: boolean;
  pinned: T[];
  setPinned: Dispatch<SetStateAction<T[]>>;
}

export function usePersistentPinnedActions<T extends string>(
  options: UsePersistentPinnedActionsOptions<T>,
): UsePersistentPinnedActionsResult<T> {
  const { loaded, value, setValue } = usePersistentStringArray({
    store: options.store,
    key: options.key,
    initial: options.initialPinned as string[],
    migrateFromKeys: options.migrateFromKeys,
  });

  return {
    loaded,
    pinned: value as T[],
    setPinned: setValue as Dispatch<SetStateAction<T[]>>,
  };
}
