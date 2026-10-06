import {
  classifyChatScrollAwayMotion,
  classifyChatScrollReturnToBottom,
  isLikelyUserScrollActivity,
  refreshChatScrollMotionGeometry,
  shouldDetachForChatScrollAwayMotion,
  shouldReattachForChatScrollReturnToBottom,
  type ChatScrollMotionSample,
} from '../src/chat/chatScrollMotionDiagnostics';

describe('refreshChatScrollMotionGeometry', () => {
  it('advances geometry without inventing an offset movement', () => {
    expect(
      refreshChatScrollMotionGeometry(sample(1000, 600, 1000, 300, 1), {
        atMs: 1100,
        contentHeight: 1100,
        viewportHeight: 320,
        geometryRevision: 2,
      }),
    ).toEqual(sample(1100, 600, 1100, 320, 2));
  });
});

describe('isLikelyUserScrollActivity', () => {
  function classifyActivity(
    previous: ChatScrollMotionSample,
    current: ChatScrollMotionSample,
    overrides: Partial<Parameters<typeof isLikelyUserScrollActivity>[0]> = {},
  ) {
    return isLikelyUserScrollActivity({
      previous,
      current,
      minMovementPx: 0.5,
      geometryEpsilonPx: 0.5,
      lastGeometryChangeAtMs: 0,
      geometrySettleMs: 100,
      lastSemanticContentChangeAtMs: 0,
      semanticContentSettleMs: 250,
      recentProgrammaticWrite: null,
      programmaticWriteWindowMs: 500,
      activeOperation: false,
      ...overrides,
    });
  }

  it('accepts stable unexplained wheel or trackpad movement', () => {
    expect(classifyActivity(sample(1000, 500), sample(1020, 480))).toBe(true);
  });

  it('ignores movement caused by content, layout, or active navigation', () => {
    expect(
      classifyActivity(
        sample(1000, 500, 1000, 300, 1),
        sample(1020, 480, 1020, 300, 2),
      ),
    ).toBe(false);
    expect(
      classifyActivity(sample(1000, 500), sample(1020, 480), {
        lastSemanticContentChangeAtMs: 950,
      }),
    ).toBe(false);
    expect(
      classifyActivity(sample(1000, 500), sample(1020, 480), {
        activeOperation: true,
      }),
    ).toBe(false);
  });

  it('ignores compatible programmatic movement but accepts movement opposing it', () => {
    const recentBottomWrite = {
      atMs: 990,
      operationId: 4,
      purpose: 'navigation' as const,
      edge: 'bottom' as const,
      targetOffsetY: 700,
    };
    expect(
      classifyActivity(sample(1000, 650), sample(1020, 680), {
        recentProgrammaticWrite: recentBottomWrite,
      }),
    ).toBe(false);
    expect(
      classifyActivity(sample(1000, 680), sample(1020, 650), {
        recentProgrammaticWrite: recentBottomWrite,
      }),
    ).toBe(true);
  });
});

function sample(
  atMs: number,
  offsetY: number,
  contentHeight = 1000,
  viewportHeight = 300,
  geometryRevision = 1,
): ChatScrollMotionSample {
  return {
    atMs,
    offsetY,
    contentHeight,
    viewportHeight,
    geometryRevision,
  };
}

function classify(
  previous: ChatScrollMotionSample,
  current: ChatScrollMotionSample,
  overrides: Partial<Parameters<typeof classifyChatScrollAwayMotion>[0]> = {},
) {
  return classifyChatScrollAwayMotion({
    previous,
    current,
    minAwayMovementPx: 2,
    geometryEpsilonPx: 0.5,
    lastGeometryChangeAtMs: 0,
    geometrySettleMs: 100,
    lastSemanticContentChangeAtMs: 0,
    semanticContentSettleMs: 250,
    recentProgrammaticWrite: null,
    programmaticWriteWindowMs: 500,
    ...overrides,
  });
}

describe('classifyChatScrollAwayMotion', () => {
  it('identifies stable-geometry movement away from the bottom', () => {
    const result = classify(sample(1000, 700), sample(1020, 692));

    expect(result).toMatchObject({
      kind: 'candidate',
      reason: 'stableGeometryAwayMotion',
      details: {
        deltaBottomGapPx: 8,
        deltaOffsetY: -8,
        recentProgrammaticWrite: false,
      },
    });
  });

  it('ignores an increased bottom gap explained by content growth', () => {
    const result = classify(
      sample(1000, 700, 1000, 300, 1),
      sample(1020, 700, 1010, 300, 2),
    );

    expect(result).toMatchObject({
      kind: 'ignored',
      reason: 'geometryChanged',
      details: {
        deltaBottomGapPx: 10,
        contentHeightDelta: 10,
      },
    });
  });

  it('keeps movement in the geometry settling window observational', () => {
    const result = classify(sample(1000, 700), sample(1020, 695), {
      lastGeometryChangeAtMs: 980,
    });

    expect(result).toMatchObject({
      kind: 'ignored',
      reason: 'recentGeometryChange',
    });
  });

  it('keeps movement after a semantic update observational until layout arrives', () => {
    const result = classify(sample(1000, 700), sample(1020, 695), {
      lastSemanticContentChangeAtMs: 950,
    });

    expect(result).toMatchObject({
      kind: 'ignored',
      reason: 'semanticContentPending',
    });
  });

  it('reports when away movement opposes a recent bottom write', () => {
    const result = classify(sample(1000, 700), sample(1020, 694), {
      recentProgrammaticWrite: {
        atMs: 990,
        operationId: 4,
        purpose: 'contentFollow',
        edge: 'bottom',
        targetOffsetY: 700,
      },
    });

    expect(result).toMatchObject({
      kind: 'candidate',
      details: {
        recentProgrammaticWrite: true,
        programmaticOperationId: 4,
        movementOpposesProgrammaticTarget: true,
      },
    });
  });

  it('does not report movement toward the bottom or subpixel noise', () => {
    expect(classify(sample(1000, 690), sample(1020, 700))).toBeNull();
    expect(classify(sample(1000, 700), sample(1020, 699.5))).toBeNull();
  });

  it('accepts only candidates without a conflicting recent programmatic explanation', () => {
    const ordinaryCandidate = classify(sample(1000, 700), sample(1020, 694));
    expect(ordinaryCandidate).not.toBeNull();
    expect(shouldDetachForChatScrollAwayMotion(ordinaryCandidate!)).toBe(true);

    const opposedBottomWrite = classify(sample(1000, 700), sample(1020, 694), {
      recentProgrammaticWrite: {
        atMs: 990,
        operationId: 4,
        purpose: 'contentFollow',
        edge: 'bottom',
        targetOffsetY: 700,
      },
    });
    expect(shouldDetachForChatScrollAwayMotion(opposedBottomWrite!)).toBe(true);

    const compatibleTopWrite = classify(sample(1000, 690), sample(1020, 684), {
      recentProgrammaticWrite: {
        atMs: 990,
        operationId: 5,
        purpose: 'navigation',
        edge: 'top',
        targetOffsetY: 0,
      },
    });
    expect(compatibleTopWrite).not.toBeNull();
    expect(shouldDetachForChatScrollAwayMotion(compatibleTopWrite!)).toBe(
      false,
    );
  });
});

describe('classifyChatScrollReturnToBottom', () => {
  function classifyReturn(
    previous: ChatScrollMotionSample,
    current: ChatScrollMotionSample,
    overrides: Partial<
      Parameters<typeof classifyChatScrollReturnToBottom>[0]
    > = {},
  ) {
    return classifyChatScrollReturnToBottom({
      previous,
      current,
      bottomThresholdPx: 4,
      minTowardMovementPx: 0.5,
      geometryEpsilonPx: 0.5,
      lastGeometryChangeAtMs: 0,
      geometrySettleMs: 100,
      lastSemanticContentChangeAtMs: 0,
      recentProgrammaticWrite: null,
      programmaticWriteWindowMs: 500,
      ...overrides,
    });
  }

  it('identifies stable movement that reaches the measured bottom', () => {
    const result = classifyReturn(sample(1000, 600), sample(1020, 700));

    expect(result).toMatchObject({
      kind: 'candidate',
      reason: 'stableGeometryReachedBottom',
      details: {
        deltaTowardBottomPx: 100,
        deltaOffsetY: 100,
        previousBottomGapPx: 100,
        currentBottomGapPx: 0,
      },
    });
    expect(shouldReattachForChatScrollReturnToBottom(result!)).toBe(true);
  });

  it('does not infer a manual return when geometry shrink reaches bottom', () => {
    const result = classifyReturn(
      sample(1000, 600, 1100, 300, 1),
      sample(1020, 600, 900, 300, 2),
    );

    expect(result).toMatchObject({
      kind: 'ignored',
      reason: 'geometryChanged',
    });
    expect(shouldReattachForChatScrollReturnToBottom(result!)).toBe(false);
  });

  it('does not reattach while a recent programmatic write explains reaching bottom', () => {
    const result = classifyReturn(sample(1000, 600), sample(1020, 700), {
      recentProgrammaticWrite: {
        atMs: 990,
        operationId: 8,
        purpose: 'navigation',
        edge: 'bottom',
        targetOffsetY: 700,
      },
    });

    expect(result).toMatchObject({
      kind: 'candidate',
      details: {
        recentProgrammaticWrite: true,
        programmaticOperationId: 8,
      },
    });
    expect(shouldReattachForChatScrollReturnToBottom(result!)).toBe(false);
  });

  it('requires reaching the bottom threshold while moving toward it', () => {
    expect(classifyReturn(sample(1000, 600), sample(1020, 650))).toBeNull();
    expect(classifyReturn(sample(1000, 700), sample(1020, 700))).toBeNull();
  });

  it('accepts a final sub-two-pixel movement from inside the bottom threshold', () => {
    const result = classifyReturn(sample(1000, 697.5), sample(1020, 699));

    expect(result).toMatchObject({
      kind: 'candidate',
      details: {
        deltaTowardBottomPx: 1.5,
        currentBottomGapPx: 1,
      },
    });
  });
});
