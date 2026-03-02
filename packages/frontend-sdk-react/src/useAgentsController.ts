import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type { AgentsControllerState } from '@crystal-lattice/frontend-sdk';
import { AgentsController } from '@crystal-lattice/frontend-sdk';

import { useBackend, useConnectionScopeKey } from './sdkRuntimeContext';

export interface UseAgentsControllerOptions {
  enabled?: boolean;
}

export interface UseAgentsControllerResult {
  controller: AgentsController | null;
  state: AgentsControllerState | null;
}

export function useAgentsController(options: UseAgentsControllerOptions): UseAgentsControllerResult {
  const { enabled = true } = options;
  const backend = useBackend();
  const scopeKey = useConnectionScopeKey();
  const cacheKey = scopeKey ?? 'default';

  const controller = useMemo(() => {
    return new AgentsController({ backend, cacheKey });
  }, [backend, cacheKey]);

  useEffect(() => {
    if (!controller) return;
    if (!enabled) return;
    controller.ensureLoaded().catch(() => {
      // UI can decide how/when to surface this.
    });
  }, [controller, enabled]);

  const state = useSyncExternalStore(
    (onStoreChange) => controller.subscribe(onStoreChange),
    () => controller.getSnapshot(),
    () => controller.getSnapshot(),
  );

  return { controller, state };
}
