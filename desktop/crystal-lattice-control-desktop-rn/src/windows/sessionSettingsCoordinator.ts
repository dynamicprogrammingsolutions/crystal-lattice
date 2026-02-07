import { useEffect, useState } from 'react';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

export interface SessionSettingsWindowState {
  id: string;
  connectionId: string;
  connectionName?: string;
  sessionId: string;
  backend: AgentBackend;
}

export interface ActiveSessionSettingsWindow {
  state: SessionSettingsWindowState;
}

let active: ActiveSessionSettingsWindow | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveSessionSettingsWindow(next: ActiveSessionSettingsWindow) {
  active = next;
  emit();
}

export function clearActiveSessionSettingsWindow(id?: string) {
  if (!active) {
    return;
  }
  if (id && active.state.id !== id) {
    return;
  }
  active = null;
  emit();
}

export function getActiveSessionSettingsWindow(): ActiveSessionSettingsWindow | null {
  return active;
}

export function subscribeToActiveSessionSettingsWindow(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveSessionSettingsWindow(): ActiveSessionSettingsWindow | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveSessionSettingsWindow(() => setState(active));
  }, []);

  return state;
}
