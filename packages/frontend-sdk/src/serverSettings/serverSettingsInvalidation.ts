import type { AgentBackend } from '../backend/backend';
import type { Unsubscribe } from '../util/subscribable';

export interface ServerSettingsInvalidationEvent {
  reason: string;
}

type Listener = (event: ServerSettingsInvalidationEvent) => void;

const LISTENERS_BY_BACKEND: WeakMap<object, Set<Listener>> = new WeakMap();

function getBackendKey(backend: AgentBackend): object {
  if (backend && (typeof backend === 'object' || typeof backend === 'function')) {
    return backend as any;
  }
  return {};
}

export function subscribeServerSettingsInvalidated(
  backend: AgentBackend,
  listener: Listener,
): Unsubscribe {
  const backendKey = getBackendKey(backend);
  let listeners = LISTENERS_BY_BACKEND.get(backendKey);
  if (!listeners) {
    listeners = new Set();
    LISTENERS_BY_BACKEND.set(backendKey, listeners);
  }

  listeners.add(listener);

  return () => {
    const existing = LISTENERS_BY_BACKEND.get(backendKey);
    if (!existing) return;
    existing.delete(listener);
  };
}

export function emitServerSettingsInvalidated(
  backend: AgentBackend,
  options: { reason?: string } = {},
): void {
  const backendKey = getBackendKey(backend);
  const listeners = LISTENERS_BY_BACKEND.get(backendKey);
  if (!listeners || listeners.size === 0) return;

  const event: ServerSettingsInvalidationEvent = {
    reason: options.reason ?? 'unknown',
  };

  for (const listener of listeners) {
    listener(event);
  }
}