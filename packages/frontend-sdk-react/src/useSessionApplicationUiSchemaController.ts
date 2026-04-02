import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type {
  AgentBackend,
  SessionApplicationUiSchemaControllerState,
} from '@crystal-lattice/frontend-sdk';
import {
  SessionApplicationUiSchemaController,
  subscribeSessionUiSchemaInvalidated,
} from '@crystal-lattice/frontend-sdk';

export interface UseSessionApplicationUiSchemaControllerOptions {
  backend: AgentBackend | null;
  cacheKey: string;
  sessionId: string | null;
  enabled?: boolean;
}

export interface UseSessionApplicationUiSchemaControllerResult {
  controller: SessionApplicationUiSchemaController | null;
  state: SessionApplicationUiSchemaControllerState | null;
}

export function useSessionApplicationUiSchemaController(
  options: UseSessionApplicationUiSchemaControllerOptions,
): UseSessionApplicationUiSchemaControllerResult {
  const { backend, cacheKey, sessionId, enabled = true } = options;

  const controller = useMemo(() => {
    if (!backend || !sessionId) {
      return null;
    }
    return new SessionApplicationUiSchemaController({ backend, cacheKey, sessionId });
  }, [backend, cacheKey, sessionId]);

  useEffect(() => {
    if (!controller) return;
    if (!enabled) return;
    controller.load();
  }, [controller, enabled]);

  // Subscribe to invalidation events (same events as core UI schema)
  useEffect(() => {
    if (!controller) return;
    if (!enabled) return;
    if (!backend || !sessionId) return;

    return subscribeSessionUiSchemaInvalidated(backend, sessionId, () => {
      controller.invalidate();
      controller.load();
    });
  }, [backend, controller, enabled, sessionId]);

  const state = useSyncExternalStore(
    (onStoreChange) => (controller ? controller.subscribe(onStoreChange) : () => {}),
    () => (controller ? controller.getSnapshot() : null),
    () => (controller ? controller.getSnapshot() : null),
  );

  return { controller, state };
}