import { useEffect, useState } from 'react';

import type { ActionDefinition, ActionKey } from './types';

export interface ActionsPopoverMenuData {
  id: string;
  title: string;
  actions: readonly ActionDefinition[];
  pinnedKeys: readonly ActionKey[];
  disabledKeys: readonly ActionKey[];
}

export interface ActionsPopoverMenuHandlers {
  onAction: (key: ActionKey) => void;
  onTogglePinned: (key: ActionKey) => void;
  onRequestClose: () => void;
}

export interface ActionsPopoverMenuState {
  data: ActionsPopoverMenuData;
  handlers: ActionsPopoverMenuHandlers;
}

let activeMenu: ActionsPopoverMenuState | null = null;
const listeners = new Set<() => void>();

let lastAnchorTag: number | null = null;

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveActionsPopoverMenu(next: ActionsPopoverMenuState) {
  activeMenu = next;
  emit();
}

export function updateActiveActionsPopoverMenuData(next: Partial<ActionsPopoverMenuData>) {
  if (!activeMenu) {
    return;
  }
  if (next.id != null && next.id !== activeMenu.data.id) {
    return;
  }
  activeMenu = {
    ...activeMenu,
    data: {
      ...activeMenu.data,
      ...next,
    },
  };
  emit();
}

export function clearActiveActionsPopoverMenu(id?: string) {
  if (!activeMenu) {
    return;
  }
  if (id && activeMenu.data.id !== id) {
    return;
  }
  activeMenu = null;
  emit();
}

export function getActiveActionsPopoverMenu(): ActionsPopoverMenuState | null {
  return activeMenu;
}

export function subscribeToActiveActionsPopoverMenu(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function actionsPopoverInvokeAction(key: ActionKey) {
  activeMenu?.handlers.onAction(key);
}

export function actionsPopoverTogglePinned(key: ActionKey) {
  activeMenu?.handlers.onTogglePinned(key);
}

export function actionsPopoverRequestClose() {
  activeMenu?.handlers.onRequestClose();
}

export function setLastActionsPopoverAnchorTag(tag: number | null) {
  lastAnchorTag = typeof tag === 'number' ? tag : null;
}

export function getLastActionsPopoverAnchorTag(): number | null {
  return lastAnchorTag;
}

export function useActiveActionsPopoverMenu(): ActionsPopoverMenuState | null {
  const [state, setState] = useState<ActionsPopoverMenuState | null>(() => activeMenu);

  useEffect(() => {
    return subscribeToActiveActionsPopoverMenu(() => setState(activeMenu));
  }, []);

  return state;
}
