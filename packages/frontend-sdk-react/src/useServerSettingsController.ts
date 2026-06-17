import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type {
  AgentBackend,
  ServerSettingsControllerState,
} from '@crystal-lattice/frontend-sdk';
import {
  ServerSettingsController,
  subscribeServerSettingsInvalidated,
} from '@crystal-lattice/frontend-sdk';

export interface UseServerSettingsControllerOptions {
  backend: AgentBackend | null;
  cacheKey: string;
  enabled?: boolean;
}

export interface UseServerSettingsControllerResult {
  controller: ServerSettingsController | null;
  state: ServerSettingsControllerState | null;
}

export function useServerSettingsController(
  options: UseServerSettingsControllerOptions,
): UseServerSettingsControllerResult {
  const { backend, cacheKey, enabled = true } = options;

  const controller = useMemo(() => {
    if (!backend) {
      return null;
    }
    return new ServerSettingsController({ backend, cacheKey });
  }, [backend, cacheKey]);

  useEffect(() => {
    if (!controller || !enabled) {
      return;
    }
    controller.load().catch(() => {
      // State captures errors.
    });
  }, [controller, enabled]);

  useEffect(() => {
    if (!controller || !enabled || !backend) {
      return;
    }

    return subscribeServerSettingsInvalidated(backend, () => {
      controller.invalidate();
      controller.load().catch(() => {
        // State captures errors.
      });
    });
  }, [backend, controller, enabled]);

  useEffect(() => {
    return () => {
      controller?.dispose();
    };
  }, [controller]);

  const state = useSyncExternalStore(
    (onStoreChange) => (controller ? controller.subscribe(onStoreChange) : () => {}),
    () => (controller ? controller.getSnapshot() : null),
    () => (controller ? controller.getSnapshot() : null),
  );

  return { controller, state };
}