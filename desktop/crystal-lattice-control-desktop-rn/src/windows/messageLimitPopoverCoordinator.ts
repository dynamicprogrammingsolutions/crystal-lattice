import { useEffect, useState } from 'react';

export interface MessageLimitPopoverState {
  id: string;
  connectionId: string;
  sessionId: string;
  startText: string;
  endText: string;
  lastReloadAtMs: number | null;
}

export interface MessageLimitPopoverHandlers {
  onApply: (params: { startText: string; endText: string }) => void;
  onCancel: () => void;
}

export interface ActiveMessageLimitPopover {
  state: MessageLimitPopoverState;
  handlers: MessageLimitPopoverHandlers;
}

let active: ActiveMessageLimitPopover | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveMessageLimitPopover(next: ActiveMessageLimitPopover) {
  active = next;
  emit();
}

export function clearActiveMessageLimitPopover(id?: string) {
  if (!active) {
    return;
  }
  if (id && active.state.id !== id) {
    return;
  }
  active = null;
  emit();
}

export function subscribeToActiveMessageLimitPopover(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveMessageLimitPopover(): ActiveMessageLimitPopover | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveMessageLimitPopover(() => setState(active));
  }, []);

  return state;
}
