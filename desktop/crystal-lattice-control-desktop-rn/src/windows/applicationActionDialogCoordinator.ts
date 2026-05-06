import { useEffect, useState } from 'react';

export interface ApplicationActionDialogState {
  id: string;
  dialog: any;
  titleFallback?: string;
  prefillContext?: any;
}

export interface ApplicationActionDialogHandlers {
  onSubmit: (payload: {
    values: Record<string, any>;
    buttonId?: string;
  }) => void | Promise<void>;
  onCancel: () => void;
}

export interface ActiveApplicationActionDialog {
  state: ApplicationActionDialogState;
  handlers: ApplicationActionDialogHandlers;
}

let active: ActiveApplicationActionDialog | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveApplicationActionDialog(next: ActiveApplicationActionDialog) {
  active = next;
  emit();
}

export function clearActiveApplicationActionDialog(id?: string) {
  if (!active) {
    return;
  }
  if (id && active.state.id !== id) {
    return;
  }
  active = null;
  emit();
}

export function getActiveApplicationActionDialog(): ActiveApplicationActionDialog | null {
  return active;
}

export function subscribeToActiveApplicationActionDialog(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveApplicationActionDialog(): ActiveApplicationActionDialog | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveApplicationActionDialog(() => setState(active));
  }, []);

  return state;
}
