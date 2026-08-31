import { useEffect, useState } from 'react';

import { DesktopWindowManager } from './desktopWindowManager';

export interface SessionNoteWindowState {
  id: string;
  sessionId: string;
  title: string;
  initialNote: string;
  onSave: (note: string) => void;
  onRemove: () => void;
}

let active: SessionNoteWindowState | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

export function openSessionNoteWindow(state: SessionNoteWindowState) {
  active = state;
  emit();
  DesktopWindowManager?.openReactWindow({
    windowKey: 'sessionNote',
    moduleName: 'SessionNoteWindow',
    title: 'Local Note',
    width: 520,
    height: 360,
    initialProps: {},
  });
}

export function closeSessionNoteWindow(id?: string) {
  if (id && active?.id !== id) return;
  active = null;
  emit();
  DesktopWindowManager?.closeReactWindow({ windowKey: 'sessionNote' });
}

export function clearSessionNoteWindowFromSystem() {
  active = null;
  emit();
}

export function useActiveSessionNoteWindow(): SessionNoteWindowState | null {
  const [state, setState] = useState(active);
  useEffect(() => {
    const listener = () => setState(active);
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);
  return state;
}
