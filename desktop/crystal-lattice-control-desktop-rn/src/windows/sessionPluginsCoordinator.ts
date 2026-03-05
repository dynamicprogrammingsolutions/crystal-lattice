import { useEffect, useState } from 'react';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

export interface SessionPluginsWindowState {
  id: string;
  connectionId: string;
  connectionName?: string;
  sessionId: string;
  backend: AgentBackend;
}

export interface ActiveSessionPluginsWindow {
  state: SessionPluginsWindowState;
}

let active: ActiveSessionPluginsWindow | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveSessionPluginsWindow(next: ActiveSessionPluginsWindow) {
  active = next;
  emit();
}

export function clearActiveSessionPluginsWindow(id?: string) {
  if (!active) {
    return;
  }
  if (id && active.state.id !== id) {
    return;
  }
  active = null;
  emit();
}

export function getActiveSessionPluginsWindow(): ActiveSessionPluginsWindow | null {
  return active;
}

export function subscribeToActiveSessionPluginsWindow(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveSessionPluginsWindow(): ActiveSessionPluginsWindow | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveSessionPluginsWindow(() => setState(active));
  }, []);

  return state;
}
