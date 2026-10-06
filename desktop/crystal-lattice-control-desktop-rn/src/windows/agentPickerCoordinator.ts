import { useEffect, useState } from 'react';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

export interface AgentPickerWindowState {
  id: string;
  connectionId: string;
  backend: AgentBackend;
}

let active: AgentPickerWindowState | null = null;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveAgentPickerWindow(
  next: AgentPickerWindowState,
): void {
  active = next;
  emit();
}

export function clearActiveAgentPickerWindow(id?: string): void {
  if (!active) return;
  if (id && active.id !== id) return;
  active = null;
  emit();
}

export function useActiveAgentPickerWindow(): AgentPickerWindowState | null {
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