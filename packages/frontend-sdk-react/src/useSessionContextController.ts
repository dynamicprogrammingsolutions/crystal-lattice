import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type {
  AgentBackend,
  SessionContextControllerState,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { SessionContextController } from '@crystal-lattice/frontend-sdk';

export interface UseSessionContextControllerOptions {
  backend: AgentBackend | null;
  cacheKey: string;
  sessionId: string | null;
  initialSummary?: SessionSummary | null;
  initialLoadedAt?: number | null;
  enabled?: boolean;
}

export interface UseSessionContextControllerResult {
  controller: SessionContextController | null;
  state: SessionContextControllerState | null;
}

export function useSessionContextController(
  options: UseSessionContextControllerOptions,
): UseSessionContextControllerResult {
  const {
    backend,
    cacheKey,
    sessionId,
    initialSummary = null,
    initialLoadedAt = null,
    enabled = true,
  } = options;

  const controller = useMemo(() => {
    if (!backend || !sessionId) {
      return null;
    }
    return new SessionContextController({
      backend,
      cacheKey,
      sessionId,
      initialSummary,
      initialLoadedAt,
    });
  }, [backend, cacheKey, sessionId]);

  useEffect(() => {
    if (!controller) {
      return;
    }
    controller.hydrateFromSummary({ summary: initialSummary, lastLoadedAt: initialLoadedAt });
  }, [controller, initialLoadedAt, initialSummary]);

  useEffect(() => {
    if (!controller || !enabled) {
      return;
    }
    controller.loadIfStale({ staleMs: 30000 }).catch(() => {
      // State captures errors.
    });
  }, [controller, enabled]);

  const state = useSyncExternalStore(
    (onStoreChange) => (controller ? controller.subscribe(onStoreChange) : () => {}),
    () => (controller ? controller.getSnapshot() : null),
    () => (controller ? controller.getSnapshot() : null),
  );

  return { controller, state };
}