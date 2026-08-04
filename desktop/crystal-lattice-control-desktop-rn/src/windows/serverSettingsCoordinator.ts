import { useEffect, useState } from 'react';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

export interface ServerSettingsWindowState {
  id: string;
  connectionId: string;
  connectionName: string;
  backend: AgentBackend;
}

let active: ServerSettingsWindowState | null = null;
const listeners = new Set<() => void>();

export function setActiveServerSettingsWindow(next: ServerSettingsWindowState | null): void {
  active = next;
  for (const listener of listeners) listener();
}

export function useActiveServerSettingsWindow(): ServerSettingsWindowState | null {
  const [value, setValue] = useState(active);
  useEffect(() => {
    const listener = () => setValue(active);
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);
  return value;
}