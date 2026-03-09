import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type {
  AgentBackend,
  SessionSettingsControllerState,
} from '@crystal-lattice/frontend-sdk';
import {
  SessionSettingsController,
  subscribeSessionUiSchemaInvalidated,
} from '@crystal-lattice/frontend-sdk';

export interface UseSessionSettingsControllerOptions {
  backend: AgentBackend | null;
  cacheKey: string;
  sessionId: string | null;
  enabled?: boolean;
}

export interface UseSessionSettingsControllerResult {
  controller: SessionSettingsController | null;
  state: SessionSettingsControllerState | null;
}

export function useSessionSettingsController(
  options: UseSessionSettingsControllerOptions,
): UseSessionSettingsControllerResult {
  const { backend, cacheKey, sessionId, enabled = true } = options;

  const controller = useMemo(() => {
    if (!backend || !sessionId) {
      return null;
    }
    return new SessionSettingsController({ backend, cacheKey, sessionId });
  }, [backend, cacheKey, sessionId]);

  useEffect(() => {
    if (!controller || !enabled) {
      return;
    }
    controller.load().catch(() => {
      // State captures errors.
    });
  }, [controller, enabled]);

  useEffect(() => {
    if (!controller || !enabled || !backend || !sessionId) {
      return;
    }

    return subscribeSessionUiSchemaInvalidated(backend, sessionId, () => {
      controller.invalidate();
      controller.load().catch(() => {
        // State captures errors.
      });
    });
  }, [backend, controller, enabled, sessionId]);

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