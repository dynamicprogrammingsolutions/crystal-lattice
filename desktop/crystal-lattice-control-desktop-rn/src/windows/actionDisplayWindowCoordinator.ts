import { useEffect, useState } from 'react';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from '@crystal-lattice/frontend-sdk';

export interface ActionDisplayWindowState {
  id: string;
  display: ActionDisplayPayload;
  contextLabel?: string;
}

export interface ActionDisplayWindowHandlers {
  onDismiss: () => void | Promise<void>;
  onFollowupAction: (
    action: ActionDisplayFollowupAction,
    formValues?: Record<string, any>,
  ) => void | Promise<void>;
}

export interface ActiveActionDisplayWindow {
  state: ActionDisplayWindowState;
  handlers: ActionDisplayWindowHandlers;
}

let active: ActiveActionDisplayWindow | null = null;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveActionDisplayWindow(
  next: ActiveActionDisplayWindow,
): void {
  active = next;
  emit();
}

export function clearActiveActionDisplayWindow(id?: string): void {
  if (!active || (id && active.state.id !== id)) {
    return;
  }
  active = null;
  emit();
}

export function getActiveActionDisplayWindow(): ActiveActionDisplayWindow | null {
  return active;
}

export function dismissActiveActionDisplayWindowFromSystem(): void {
  const current = active;
  if (!current) {
    return;
  }
  clearActiveActionDisplayWindow(current.state.id);
  void current.handlers.onDismiss();
}

export function subscribeToActiveActionDisplayWindow(
  listener: () => void,
): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveActionDisplayWindow(): ActiveActionDisplayWindow | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveActionDisplayWindow(() => setState(active));
  }, []);

  return state;
}
