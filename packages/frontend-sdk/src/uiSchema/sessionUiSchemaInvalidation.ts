import type { AgentBackend } from '../backend/backend';
import type { Unsubscribe } from '../util/subscribable';

export interface SessionUiSchemaInvalidationEvent {
  sessionId: string;
  reason: string;
}

type Listener = (event: SessionUiSchemaInvalidationEvent) => void;

const LISTENERS_BY_BACKEND: WeakMap<object, Map<string, Set<Listener>>> = new WeakMap();

function getBackendKey(backend: AgentBackend): object {
  if (backend && (typeof backend === 'object' || typeof backend === 'function')) {
    return backend as any;
  }
  return {};
}

export function subscribeSessionUiSchemaInvalidated(
  backend: AgentBackend,
  sessionId: string,
  listener: Listener,
): Unsubscribe {
  const backendKey = getBackendKey(backend);
  let bySession = LISTENERS_BY_BACKEND.get(backendKey);
  if (!bySession) {
    bySession = new Map();
    LISTENERS_BY_BACKEND.set(backendKey, bySession);
  }

  let listeners = bySession.get(sessionId);
  if (!listeners) {
    listeners = new Set();
    bySession.set(sessionId, listeners);
  }

  listeners.add(listener);

  return () => {
    const existingBySession = LISTENERS_BY_BACKEND.get(backendKey);
    if (!existingBySession) return;
    const existingListeners = existingBySession.get(sessionId);
    if (!existingListeners) return;
    existingListeners.delete(listener);
    if (existingListeners.size === 0) {
      existingBySession.delete(sessionId);
    }
  };
}

export function emitSessionUiSchemaInvalidated(
  backend: AgentBackend,
  sessionId: string,
  options: { reason?: string } = {},
): void {
  const backendKey = getBackendKey(backend);
  const bySession = LISTENERS_BY_BACKEND.get(backendKey);
  if (!bySession) return;

  const listeners = bySession.get(sessionId);
  if (!listeners || listeners.size === 0) return;

  const event: SessionUiSchemaInvalidationEvent = {
    sessionId,
    reason: options.reason ?? 'unknown',
  };

  for (const listener of listeners) {
    listener(event);
  }
}
