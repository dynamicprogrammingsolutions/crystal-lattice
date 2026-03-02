import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type { SessionsControllerState } from '@crystal-lattice/frontend-sdk';
import { SessionsController } from '@crystal-lattice/frontend-sdk';

import { useBackend } from './sdkRuntimeContext';

export interface UseSessionsControllerOptions {
  initialSessions?: SessionsControllerState['sessions'];
  limit?: number;
}

export interface UseSessionsControllerResult {
  controller: SessionsController | null;
  state: SessionsControllerState | null;
}

export function useSessionsController(options: UseSessionsControllerOptions): UseSessionsControllerResult {
  const { initialSessions, limit } = options;
  const backend = useBackend();

  const controller = useMemo(() => {
    if (!backend) {
      return null;
    }
    return new SessionsController({ backend, initialSessions, limit });
  }, [backend, initialSessions, limit]);

  useEffect(() => {
    // No long-lived resources today.
  }, [controller]);

  const state = useSyncExternalStore(
    (onStoreChange) => (controller ? controller.subscribe(onStoreChange) : () => {}),
    () => (controller ? controller.getSnapshot() : null),
    () => (controller ? controller.getSnapshot() : null),
  );
  return { controller, state };
}
