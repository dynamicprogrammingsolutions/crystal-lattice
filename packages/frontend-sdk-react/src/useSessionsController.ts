import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type { AgentBackend, SessionsControllerState } from '@crystal-lattice/frontend-sdk';
import { SessionsController } from '@crystal-lattice/frontend-sdk';

export interface UseSessionsControllerOptions {
  backend: AgentBackend | null;
  initialSessions?: SessionsControllerState['sessions'];
  limit?: number;
}

export interface UseSessionsControllerResult {
  controller: SessionsController | null;
  state: SessionsControllerState | null;
}

export function useSessionsController(options: UseSessionsControllerOptions): UseSessionsControllerResult {
  const { backend, initialSessions, limit } = options;

  const controller = useMemo(() => {
    if (!backend) {
      return null;
    }
    return new SessionsController({ backend, initialSessions, limit });
  }, [backend]);

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
