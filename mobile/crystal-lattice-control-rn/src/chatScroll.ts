export interface ChatScrollAnchor {
  bottomGapPx: number;
  pinnedToBottom: boolean;
  updatedAtMs: number;
}

export const PINNED_TO_BOTTOM_THRESHOLD_PX = 40;

export function isChatScrollAnchor(value: unknown): value is ChatScrollAnchor {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.bottomGapPx === 'number' &&
    Number.isFinite(record.bottomGapPx) &&
    record.bottomGapPx >= 0 &&
    typeof record.pinnedToBottom === 'boolean' &&
    typeof record.updatedAtMs === 'number' &&
    Number.isFinite(record.updatedAtMs) &&
    record.updatedAtMs > 0
  );
}

export function createChatScrollAnchor(input: {
  bottomGapPx: number;
  pinnedToBottom: boolean;
  updatedAtMs?: number;
}): ChatScrollAnchor {
  return {
    bottomGapPx: Math.max(0, input.bottomGapPx),
    pinnedToBottom: input.pinnedToBottom,
    updatedAtMs: input.updatedAtMs ?? Date.now(),
  };
}
