import type { SessionOpenMode } from '../settings/desktopGlobalSettings';
import { useCallback, useRef } from 'react';

export const SESSION_ITEM_DOUBLE_CLICK_MS = 350;

export interface SessionItemClickMemory {
  key: string;
  atMs: number;
}

export function resolveSessionItemClick(options: {
  previous: SessionItemClickMemory | null;
  key: string;
  nowMs: number;
  doubleClickAction: SessionOpenMode;
  thresholdMs?: number;
}): {
  next: SessionItemClickMemory;
  openMode: SessionOpenMode | null;
} {
  const next = { key: options.key, atMs: options.nowMs };
  const thresholdMs = options.thresholdMs ?? SESSION_ITEM_DOUBLE_CLICK_MS;
  const isDoubleClick =
    options.previous?.key === options.key &&
    options.nowMs - options.previous.atMs >= 0 &&
    options.nowMs - options.previous.atMs <= thresholdMs;
  return {
    next,
    openMode: isDoubleClick ? options.doubleClickAction : null,
  };
}

export function useSessionItemPress(options: {
  key: string;
  doubleClickAction: SessionOpenMode;
  onSelect: () => void;
  onOpen: (mode: SessionOpenMode) => void;
}): () => void {
  const { key, doubleClickAction, onSelect, onOpen } = options;
  const previousRef = useRef<SessionItemClickMemory | null>(null);
  return useCallback(() => {
    onSelect();
    const result = resolveSessionItemClick({
      previous: previousRef.current,
      key,
      nowMs: Date.now(),
      doubleClickAction,
    });
    previousRef.current = result.next;
    if (result.openMode) onOpen(result.openMode);
  }, [doubleClickAction, key, onOpen, onSelect]);
}
