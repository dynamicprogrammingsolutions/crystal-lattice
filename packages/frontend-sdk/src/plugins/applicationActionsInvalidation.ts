import type { AgentBackend } from '../backend/backend';
import type { Unsubscribe } from '../util/subscribable';

type Listener = (invalidationRevision: number) => void;

interface InvalidationState {
  nextRevision: number;
  pendingRevision: number | null;
  listeners: Set<Listener>;
}

const STATE_BY_BACKEND: WeakMap<object, InvalidationState> = new WeakMap();

function getState(backend: AgentBackend): InvalidationState {
  let state = STATE_BY_BACKEND.get(backend as object);
  if (!state) {
    state = {
      nextRevision: 0,
      pendingRevision: null,
      listeners: new Set(),
    };
    STATE_BY_BACKEND.set(backend as object, state);
  }
  return state;
}

export function subscribeApplicationActionsInvalidated(
  backend: AgentBackend,
  listener: Listener,
): Unsubscribe {
  const state = getState(backend);
  state.listeners.add(listener);
  if (state.pendingRevision != null) {
    listener(state.pendingRevision);
  }
  return () => {
    state.listeners.delete(listener);
  };
}

export function emitApplicationActionsInvalidated(backend: AgentBackend): void {
  const state = getState(backend);
  const revision = ++state.nextRevision;
  state.pendingRevision = revision;
  for (const listener of state.listeners) {
    listener(revision);
  }
}

export function acknowledgeApplicationActionsInvalidated(
  backend: AgentBackend,
  invalidationRevision: number,
): void {
  const state = getState(backend);
  if (state.pendingRevision === invalidationRevision) {
    state.pendingRevision = null;
  }
}
