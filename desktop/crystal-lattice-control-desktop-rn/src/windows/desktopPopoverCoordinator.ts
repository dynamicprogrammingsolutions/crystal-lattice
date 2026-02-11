import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';

import { DesktopWindowManager } from './desktopWindowManager';

export interface DesktopPopoverState {
  id: string;
  title: string;
  content: ReactNode;
  onRequestClose?: () => void;
}

let active: DesktopPopoverState | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveDesktopPopover(next: DesktopPopoverState) {
  active = next;
  emit();
}

export function clearActiveDesktopPopover(id?: string) {
  if (!active) {
    return;
  }
  if (id && active.id !== id) {
    return;
  }
  active = null;
  emit();
}

export function openDesktopPopover(params: {
  id: string;
  title: string;
  content: ReactNode;
  onRequestClose?: () => void;
  anchorTag?: number;
  width?: number;
  height?: number;
}) {
  setActiveDesktopPopover({
    id: params.id,
    title: params.title,
    content: params.content,
    onRequestClose: params.onRequestClose,
  });

  DesktopWindowManager?.openMessageLimitPopover?.({
    anchorTag: params.anchorTag,
    width: params.width,
    height: params.height,
  });
}

export function closeDesktopPopover(id?: string) {
  clearActiveDesktopPopover(id);
  DesktopWindowManager?.closeMessageLimitPopover?.();
}

export function subscribeToActiveDesktopPopover(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveDesktopPopover(): DesktopPopoverState | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveDesktopPopover(() => setState(active));
  }, []);

  return state;
}
