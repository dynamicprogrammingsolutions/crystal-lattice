import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';

import { DesktopWindowManager } from './desktopWindowManager';

export interface DesktopPopoverState {
  id: string;
  title?: string;
  content: ReactNode;
  onRequestClose?: () => void;
  anchorTag?: number;
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

export function getActiveDesktopPopover(): DesktopPopoverState | null {
  return active;
}

export function updateActiveDesktopPopover(
  id: string,
  next: Partial<Omit<DesktopPopoverState, 'id'>>,
): boolean {
  if (!active || active.id !== id) {
    return false;
  }
  active = {
    ...active,
    ...next,
    id,
  };
  emit();
  return true;
}

export function clearActiveDesktopPopover(id?: string): boolean {
  if (!active) {
    return false;
  }
  if (id && active.id !== id) {
    return false;
  }
  active = null;
  emit();
  return true;
}

export function openDesktopPopover(params: {
  id: string;
  title?: string;
  content: ReactNode;
  onRequestClose?: () => void;
  accessibilityId?: string;
  anchorTag?: number;
  width?: number;
  height?: number;
}) {
  setActiveDesktopPopover({
    id: params.id,
    title: params.title,
    content: params.content,
    onRequestClose: params.onRequestClose,
    anchorTag: params.anchorTag,
  });

  DesktopWindowManager?.openMessageLimitPopover?.({
    popoverId: params.accessibilityId ?? params.id,
    anchorTag: params.anchorTag,
    width: params.width,
    height: params.height,
  });
}

export function closeDesktopPopover(id?: string) {
  if (id && !clearActiveDesktopPopover(id)) {
    return;
  }
  if (!id) {
    clearActiveDesktopPopover();
  }
  DesktopWindowManager?.closeMessageLimitPopover?.();
}

export function subscribeToActiveDesktopPopover(
  listener: () => void,
): () => void {
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
