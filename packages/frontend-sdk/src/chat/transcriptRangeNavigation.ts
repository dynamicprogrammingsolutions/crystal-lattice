import type { ApiMessage, IndexedMessage } from "../types/messages";

export type TranscriptViewportAnchorCandidate = {
  messageIndex: number;
  offsetFromViewportTop: number;
  message: ApiMessage;
};

export type TranscriptRangeResponseContext = {
  cursorEventId: string | null;
  snapshotId?: string | null;
};

export type TranscriptRangeRestoreAnchor = {
  messageIndex: number;
  offsetFromViewportTop: number;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function structurallyEqual(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) {
    return true;
  }
  if (Array.isArray(left) || Array.isArray(right)) {
    if (
      !Array.isArray(left) ||
      !Array.isArray(right) ||
      left.length !== right.length
    ) {
      return false;
    }
    return left.every((value, index) => structurallyEqual(value, right[index]));
  }
  if (isRecord(left) || isRecord(right)) {
    if (!isRecord(left) || !isRecord(right)) {
      return false;
    }
    const leftKeys = Object.keys(left).sort();
    const rightKeys = Object.keys(right).sort();
    if (
      leftKeys.length !== rightKeys.length ||
      leftKeys.some((key, index) => key !== rightKeys[index])
    ) {
      return false;
    }
    return leftKeys.every((key) => structurallyEqual(left[key], right[key]));
  }
  return false;
}

export function selectTranscriptRangeRestoreAnchor(options: {
  candidates: ReadonlyArray<TranscriptViewportAnchorCandidate>;
  completedMessages: ReadonlyArray<IndexedMessage>;
  previousContext: TranscriptRangeResponseContext;
  completedContext: TranscriptRangeResponseContext;
}): TranscriptRangeRestoreAnchor | null {
  const previousSnapshotId = options.previousContext.snapshotId ?? null;
  const completedSnapshotId = options.completedContext.snapshotId ?? null;
  if (
    (previousSnapshotId != null || completedSnapshotId != null) &&
    previousSnapshotId !== completedSnapshotId
  ) {
    return null;
  }

  const messageByIndex = new Map(
    options.completedMessages.map(
      (entry) => [entry.index, entry.message] as const,
    ),
  );
  for (const candidate of options.candidates) {
    const completedMessage = messageByIndex.get(candidate.messageIndex);
    if (!completedMessage) {
      continue;
    }
    if (!structurallyEqual(candidate.message, completedMessage)) {
      continue;
    }
    return {
      messageIndex: candidate.messageIndex,
      offsetFromViewportTop: candidate.offsetFromViewportTop,
    };
  }
  return null;
}
