import { useEffect, type Dispatch, type SetStateAction } from 'react';
import { usePersistentPinnedActionsFromContext } from './PinnedActionsContext';

export interface UsePersistentPinnedActionsResult<T extends string> {
  pinned: T[];
  setPinned: Dispatch<SetStateAction<T[]>>;
}

export function usePersistentPinnedActions<T extends string>(
  storageKey: string,
  initialPinned: T[],
): UsePersistentPinnedActionsResult<T> {
  // Delegate to the application-level PinnedActionsProvider. This
  // hook now assumes it is called under that provider; if it is not,
  // it will throw with a clear error.
  const { pinned, setPinned } = usePersistentPinnedActionsFromContext<T>(
    storageKey,
    initialPinned,
  );

  // Ensure React marks the dependency on initialPinned seen by the
  // underlying context hook. (The actual registration is handled
  // inside usePersistentPinnedActionsFromContext.)
  useEffect(() => {
    // no-op, just to keep ESLint/tsc happy about unused param in some
    // configurations
  }, [initialPinned]);

  return { pinned, setPinned };
}

