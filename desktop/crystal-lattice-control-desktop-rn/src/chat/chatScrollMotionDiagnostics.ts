import type { ChatScrollEdge, ChatScrollOperationPurpose } from './chatScrollCoordinator';

export type ChatScrollMotionSample = {
  atMs: number;
  offsetY: number;
  contentHeight: number;
  viewportHeight: number;
  geometryRevision: number;
};

export type ChatScrollProgrammaticWrite = {
  atMs: number;
  operationId: number;
  purpose: ChatScrollOperationPurpose;
  edge: ChatScrollEdge;
  targetOffsetY: number;
};

export type ChatScrollAwayMotionDiagnostic =
  | {
      kind: 'candidate';
      reason: 'stableGeometryAwayMotion';
      details: Record<string, unknown>;
    }
  | {
      kind: 'ignored';
      reason: 'geometryChanged' | 'recentGeometryChange' | 'semanticContentPending';
      details: Record<string, unknown>;
    };

export type ChatScrollReturnToBottomDiagnostic =
  | {
      kind: 'candidate';
      reason: 'stableGeometryReachedBottom';
      details: Record<string, unknown>;
    }
  | {
      kind: 'ignored';
      reason: 'geometryChanged' | 'recentGeometryChange';
      details: Record<string, unknown>;
    };

function maxOffsetY(sample: ChatScrollMotionSample): number {
  return Math.max(0, sample.contentHeight - sample.viewportHeight);
}

function bottomGapPx(sample: ChatScrollMotionSample): number {
  return Math.max(0, maxOffsetY(sample) - sample.offsetY);
}

export function refreshChatScrollMotionGeometry(
  sample: ChatScrollMotionSample | null,
  geometry: {
    atMs: number;
    contentHeight: number | null;
    viewportHeight: number | null;
    geometryRevision: number;
  },
): ChatScrollMotionSample | null {
  if (!sample) {
    return null;
  }
  return {
    ...sample,
    atMs: geometry.atMs,
    contentHeight: geometry.contentHeight ?? sample.contentHeight,
    viewportHeight: geometry.viewportHeight ?? sample.viewportHeight,
    geometryRevision: geometry.geometryRevision,
  };
}

export function classifyChatScrollAwayMotion(input: {
  previous: ChatScrollMotionSample;
  current: ChatScrollMotionSample;
  minAwayMovementPx: number;
  geometryEpsilonPx: number;
  lastGeometryChangeAtMs: number;
  geometrySettleMs: number;
  lastSemanticContentChangeAtMs: number;
  semanticContentSettleMs: number;
  recentProgrammaticWrite: ChatScrollProgrammaticWrite | null;
  programmaticWriteWindowMs: number;
}): ChatScrollAwayMotionDiagnostic | null {
  const previousBottomGapPx = bottomGapPx(input.previous);
  const currentBottomGapPx = bottomGapPx(input.current);
  const deltaBottomGapPx = currentBottomGapPx - previousBottomGapPx;
  const minAwayMovementPx = Math.max(0, input.minAwayMovementPx);
  if (deltaBottomGapPx < minAwayMovementPx) {
    return null;
  }

  const deltaOffsetY = input.current.offsetY - input.previous.offsetY;
  const contentHeightDelta =
    input.current.contentHeight - input.previous.contentHeight;
  const viewportHeightDelta =
    input.current.viewportHeight - input.previous.viewportHeight;
  const geometryEpsilonPx = Math.max(0, input.geometryEpsilonPx);
  const geometryChanged =
    input.current.geometryRevision !== input.previous.geometryRevision ||
    Math.abs(contentHeightDelta) > geometryEpsilonPx ||
    Math.abs(viewportHeightDelta) > geometryEpsilonPx;
  const msSinceGeometryChange = Math.max(
    0,
    input.current.atMs - input.lastGeometryChangeAtMs,
  );
  const msSinceSemanticContentChange = Math.max(
    0,
    input.current.atMs - input.lastSemanticContentChangeAtMs,
  );
  const write = input.recentProgrammaticWrite;
  const programmaticWriteAgeMs = write
    ? Math.max(0, input.current.atMs - write.atMs)
    : null;
  const recentProgrammaticWrite =
    write != null &&
    programmaticWriteAgeMs != null &&
    programmaticWriteAgeMs <= Math.max(0, input.programmaticWriteWindowMs);
  const movementOpposesProgrammaticTarget =
    recentProgrammaticWrite && write
      ? write.edge === 'bottom'
        ? deltaOffsetY < -geometryEpsilonPx
        : deltaOffsetY > geometryEpsilonPx
      : false;

  const details: Record<string, unknown> = {
    deltaBottomGapPx: Math.round(deltaBottomGapPx * 10) / 10,
    deltaOffsetY: Math.round(deltaOffsetY * 10) / 10,
    previousOffsetY: Math.round(input.previous.offsetY * 10) / 10,
    currentOffsetY: Math.round(input.current.offsetY * 10) / 10,
    previousBottomGapPx: Math.round(previousBottomGapPx * 10) / 10,
    currentBottomGapPx: Math.round(currentBottomGapPx * 10) / 10,
    contentHeightDelta: Math.round(contentHeightDelta * 10) / 10,
    viewportHeightDelta: Math.round(viewportHeightDelta * 10) / 10,
    previousGeometryRevision: input.previous.geometryRevision,
    geometryRevision: input.current.geometryRevision,
    msSinceGeometryChange,
    msSinceSemanticContentChange,
    recentProgrammaticWrite,
    programmaticWriteAgeMs,
    programmaticOperationId: write?.operationId ?? null,
    programmaticPurpose: write?.purpose ?? null,
    programmaticEdge: write?.edge ?? null,
    programmaticTargetOffsetY:
      write == null ? null : Math.round(write.targetOffsetY * 10) / 10,
    movementOpposesProgrammaticTarget,
  };

  if (geometryChanged) {
    return { kind: 'ignored', reason: 'geometryChanged', details };
  }
  if (msSinceGeometryChange < Math.max(0, input.geometrySettleMs)) {
    return { kind: 'ignored', reason: 'recentGeometryChange', details };
  }
  if (
    msSinceSemanticContentChange <
    Math.max(0, input.semanticContentSettleMs)
  ) {
    return { kind: 'ignored', reason: 'semanticContentPending', details };
  }
  return {
    kind: 'candidate',
    reason: 'stableGeometryAwayMotion',
    details,
  };
}

export function shouldDetachForChatScrollAwayMotion(
  diagnostic: ChatScrollAwayMotionDiagnostic,
): boolean {
  if (diagnostic.kind !== 'candidate') {
    return false;
  }
  const recentProgrammaticWrite =
    diagnostic.details.recentProgrammaticWrite === true;
  const movementOpposesProgrammaticTarget =
    diagnostic.details.movementOpposesProgrammaticTarget === true;
  return !recentProgrammaticWrite || movementOpposesProgrammaticTarget;
}

export function classifyChatScrollReturnToBottom(input: {
  previous: ChatScrollMotionSample;
  current: ChatScrollMotionSample;
  bottomThresholdPx: number;
  minTowardMovementPx: number;
  geometryEpsilonPx: number;
  lastGeometryChangeAtMs: number;
  geometrySettleMs: number;
  lastSemanticContentChangeAtMs: number;
  recentProgrammaticWrite: ChatScrollProgrammaticWrite | null;
  programmaticWriteWindowMs: number;
}): ChatScrollReturnToBottomDiagnostic | null {
  const previousBottomGapPx = bottomGapPx(input.previous);
  const currentBottomGapPx = bottomGapPx(input.current);
  const bottomThresholdPx = Math.max(0, input.bottomThresholdPx);
  const deltaTowardBottomPx = previousBottomGapPx - currentBottomGapPx;
  if (
    currentBottomGapPx > bottomThresholdPx ||
    deltaTowardBottomPx < Math.max(0, input.minTowardMovementPx)
  ) {
    return null;
  }

  const deltaOffsetY = input.current.offsetY - input.previous.offsetY;
  const contentHeightDelta =
    input.current.contentHeight - input.previous.contentHeight;
  const viewportHeightDelta =
    input.current.viewportHeight - input.previous.viewportHeight;
  const geometryEpsilonPx = Math.max(0, input.geometryEpsilonPx);
  const geometryChanged =
    input.current.geometryRevision !== input.previous.geometryRevision ||
    Math.abs(contentHeightDelta) > geometryEpsilonPx ||
    Math.abs(viewportHeightDelta) > geometryEpsilonPx;
  const msSinceGeometryChange = Math.max(
    0,
    input.current.atMs - input.lastGeometryChangeAtMs,
  );
  const msSinceSemanticContentChange = Math.max(
    0,
    input.current.atMs - input.lastSemanticContentChangeAtMs,
  );
  const write = input.recentProgrammaticWrite;
  const programmaticWriteAgeMs = write
    ? Math.max(0, input.current.atMs - write.atMs)
    : null;
  const recentProgrammaticWrite =
    write != null &&
    programmaticWriteAgeMs != null &&
    programmaticWriteAgeMs <= Math.max(0, input.programmaticWriteWindowMs);

  const details: Record<string, unknown> = {
    deltaTowardBottomPx: Math.round(deltaTowardBottomPx * 10) / 10,
    deltaOffsetY: Math.round(deltaOffsetY * 10) / 10,
    previousOffsetY: Math.round(input.previous.offsetY * 10) / 10,
    currentOffsetY: Math.round(input.current.offsetY * 10) / 10,
    previousBottomGapPx: Math.round(previousBottomGapPx * 10) / 10,
    currentBottomGapPx: Math.round(currentBottomGapPx * 10) / 10,
    bottomThresholdPx,
    contentHeightDelta: Math.round(contentHeightDelta * 10) / 10,
    viewportHeightDelta: Math.round(viewportHeightDelta * 10) / 10,
    previousGeometryRevision: input.previous.geometryRevision,
    geometryRevision: input.current.geometryRevision,
    msSinceGeometryChange,
    msSinceSemanticContentChange,
    recentProgrammaticWrite,
    programmaticWriteAgeMs,
    programmaticOperationId: write?.operationId ?? null,
    programmaticPurpose: write?.purpose ?? null,
    programmaticEdge: write?.edge ?? null,
    programmaticTargetOffsetY:
      write == null ? null : Math.round(write.targetOffsetY * 10) / 10,
  };

  if (geometryChanged) {
    return { kind: 'ignored', reason: 'geometryChanged', details };
  }
  if (msSinceGeometryChange < Math.max(0, input.geometrySettleMs)) {
    return { kind: 'ignored', reason: 'recentGeometryChange', details };
  }
  return {
    kind: 'candidate',
    reason: 'stableGeometryReachedBottom',
    details,
  };
}

export function shouldReattachForChatScrollReturnToBottom(
  diagnostic: ChatScrollReturnToBottomDiagnostic,
): boolean {
  return (
    diagnostic.kind === 'candidate' &&
    diagnostic.details.recentProgrammaticWrite !== true
  );
}