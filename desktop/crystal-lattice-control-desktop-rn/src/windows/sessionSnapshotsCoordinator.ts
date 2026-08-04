import { useEffect, useState } from 'react';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

export interface SessionSnapshotsWindowState {
  id: string;
  connectionId: string;
  connectionName?: string;
  sessionId: string;
  backend: AgentBackend;
}

export interface ActiveSessionSnapshotsWindow {
  state: SessionSnapshotsWindowState;
}

let active: ActiveSessionSnapshotsWindow | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveSessionSnapshotsWindow(next: ActiveSessionSnapshotsWindow) {
  active = next;
  emit();
}

export function clearActiveSessionSnapshotsWindow(id?: string) {
  if (!active) {
    return;
  }
  if (id && active.state.id !== id) {
    return;
  }
  active = null;
  emit();
}

export function getActiveSessionSnapshotsWindow(): ActiveSessionSnapshotsWindow | null {
  return active;
}

export function subscribeToActiveSessionSnapshotsWindow(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveSessionSnapshotsWindow(): ActiveSessionSnapshotsWindow | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveSessionSnapshotsWindow(() => setState(active));
  }, []);

  return state;
}