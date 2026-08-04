import type { AgentBackend } from '../backend/backend';
import type { Unsubscribe } from '../util/subscribable';

type Listener = () => void;
const LISTENERS_BY_BACKEND: WeakMap<object, Set<Listener>> = new WeakMap();

export function subscribeApplicationActionsInvalidated(
  backend: AgentBackend,
  listener: Listener,
): Unsubscribe {
  let listeners = LISTENERS_BY_BACKEND.get(backend as object);
  if (!listeners) {
    listeners = new Set();
    LISTENERS_BY_BACKEND.set(backend as object, listeners);
  }
  listeners.add(listener);
  return () => {
    LISTENERS_BY_BACKEND.get(backend as object)?.delete(listener);
  };
}

export function emitApplicationActionsInvalidated(backend: AgentBackend): void {
  for (const listener of LISTENERS_BY_BACKEND.get(backend as object) ?? []) {
    listener();
  }
}