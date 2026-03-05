import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type {
  AgentBackend,
  SessionUiSchemaControllerState,
} from '@crystal-lattice/frontend-sdk';
import { SessionUiSchemaController } from '@crystal-lattice/frontend-sdk';

export interface UseSessionUiSchemaControllerOptions {
  backend: AgentBackend | null;
  cacheKey: string;
  sessionId: string | null;
  enabled?: boolean;
}

export interface UseSessionUiSchemaControllerResult {
  controller: SessionUiSchemaController | null;
  state: SessionUiSchemaControllerState | null;
}

export function useSessionUiSchemaController(
  options: UseSessionUiSchemaControllerOptions,
): UseSessionUiSchemaControllerResult {
  const { backend, cacheKey, sessionId, enabled = true } = options;

  const controller = useMemo(() => {
    if (!backend || !sessionId) {
      return null;
    }
    return new SessionUiSchemaController({ backend, cacheKey, sessionId });
  }, [backend, cacheKey, sessionId]);

  useEffect(() => {
    if (!controller) return;
    if (!enabled) return;
    controller.load();
  }, [controller, enabled]);

  const state = useSyncExternalStore(
    (onStoreChange) => (controller ? controller.subscribe(onStoreChange) : () => {}),
    () => (controller ? controller.getSnapshot() : null),
    () => (controller ? controller.getSnapshot() : null),
  );

  return { controller, state };
}
