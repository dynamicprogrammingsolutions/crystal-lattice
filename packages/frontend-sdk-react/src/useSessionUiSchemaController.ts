import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type { SessionUiSchemaControllerState } from '@crystal-lattice/frontend-sdk';
import { SessionUiSchemaController } from '@crystal-lattice/frontend-sdk';

import { useBackend, useRuntime, useConnectionScopeKey } from './sdkRuntimeContext';

export interface UseSessionUiSchemaControllerOptions {
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
  const { sessionId, enabled = true } = options;
  const backend = useBackend();
  const runtime = useRuntime();
  const scopeKey = useConnectionScopeKey();
  const cacheKey = scopeKey ?? 'default';

  const controller = useMemo(() => {
    if (!backend || !sessionId) {
      return null;
    }

    return new SessionUiSchemaController({
      backend,
      cacheKey,
      sessionId,
      enabled,
      bus: runtime?.bus,
      scopeKey: scopeKey ?? cacheKey,
    });
  }, [backend, cacheKey, enabled, runtime?.bus, scopeKey, sessionId]);

  useEffect(() => {
    controller?.setEnabled(enabled);
  }, [controller, enabled]);

  useEffect(() => {
    if (!controller) return;
    if (!enabled) return;
    controller.load();
  }, [controller, enabled]);

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
