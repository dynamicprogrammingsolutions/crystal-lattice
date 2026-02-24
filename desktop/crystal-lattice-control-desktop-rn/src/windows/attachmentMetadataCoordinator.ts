import { useEffect, useState } from 'react';

import type { AttachmentMetadataUi } from '../chat/AttachmentMetadataPopoverContent';

import { DesktopWindowManager } from './desktopWindowManager';

export interface AttachmentMetadataWindowState {
  id: string;
  title: string;
  attachmentType: string;
  attachmentContent: any;
  metadataUi: AttachmentMetadataUi | null;
  initialMetadata: Record<string, any>;
  onCancel: () => void;
  onSave: (metadata: Record<string, any>) => void;
}

export interface ActiveAttachmentMetadataWindow {
  state: AttachmentMetadataWindowState;
}

let active: ActiveAttachmentMetadataWindow | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setActiveAttachmentMetadataWindow(next: ActiveAttachmentMetadataWindow) {
  active = next;
  emit();
}

export function clearActiveAttachmentMetadataWindow(id?: string) {
  if (!active) {
    return;
  }
  if (id && active.state.id !== id) {
    return;
  }
  active = null;
  emit();
}

export function getActiveAttachmentMetadataWindow(): ActiveAttachmentMetadataWindow | null {
  return active;
}

export function subscribeToActiveAttachmentMetadataWindow(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useActiveAttachmentMetadataWindow(): ActiveAttachmentMetadataWindow | null {
  const [state, setState] = useState(() => active);

  useEffect(() => {
    return subscribeToActiveAttachmentMetadataWindow(() => setState(active));
  }, []);

  return state;
}

export function openAttachmentMetadataWindow(params: AttachmentMetadataWindowState) {
  setActiveAttachmentMetadataWindow({ state: params });
  DesktopWindowManager?.openReactWindow({
    windowKey: 'attachmentMetadata',
    moduleName: 'AttachmentMetadataWindow',
    title: params.title,
    width: 640,
    height: 760,
    initialProps: {},
  });
}

export function closeAttachmentMetadataWindow(id?: string) {
  clearActiveAttachmentMetadataWindow(id);
  DesktopWindowManager?.closeReactWindow({ windowKey: 'attachmentMetadata' });
}

export function cancelAttachmentMetadataWindowFromSystem() {
  const current = active;
  if (!current) {
    return;
  }
  try {
    current.state.onCancel();
  } finally {
    clearActiveAttachmentMetadataWindow(current.state.id);
  }
}
