import { useSyncExternalStore } from 'react';
import type { Subscribable } from '@crystal-lattice/frontend-sdk';

export function useSubscribableSnapshot<T>(subscribable: Subscribable<T>): T {
  return useSyncExternalStore(
    (onStoreChange: () => void) => subscribable.subscribe(onStoreChange),
    () => subscribable.getSnapshot(),
    () => subscribable.getSnapshot(),
  );
}
