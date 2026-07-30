import {
  createChatScrollCoordinatorState,
  evaluateChatScrollOperationBudget,
  observeChatScrollEdge,
  reduceChatScrollCoordinator,
  type ChatScrollCoordinatorState,
  type ChatScrollCoordinatorEvent,
} from '../src/chat/chatScrollCoordinator';

function apply(
  state: ChatScrollCoordinatorState,
  event: ChatScrollCoordinatorEvent,
): ChatScrollCoordinatorState {
  return reduceChatScrollCoordinator(state, event).state;
}

describe('chatScrollCoordinator', () => {
  it('keeps bottom navigation separate from content-follow leases', () => {
    const transition = reduceChatScrollCoordinator(
      createChatScrollCoordinatorState({ bottomAffinity: 'detached' }),
      {
        type: 'startNavigation',
        edge: 'bottom',
        source: 'manual',
        reason: 'button',
        nowMs: 100,
        maxDurationMs: 5000,
      },
    );

    expect(transition.state.operation).toMatchObject({
      purpose: 'navigation',
      edge: 'bottom',
      deadlineMs: 5100,
    });
    expect(transition.state.followLease).toBeNull();

    const completed = reduceChatScrollCoordinator(transition.state, {
      type: 'operationCompleted',
      operationId: transition.state.operation!.id,
      reason: 'stable',
      nowMs: 300,
    });
    expect(completed.state.bottomAffinity).toBe('pinned');
    expect(completed.state.followLease).toBeNull();
  });

  it('starts a bounded lease only for semantic content while pinned', () => {
    const transition = reduceChatScrollCoordinator(
      createChatScrollCoordinatorState({ bottomAffinity: 'pinned' }),
      {
        type: 'semanticContentChanged',
        revision: 2,
        reason: 'streamDelta',
        nowMs: 1000,
        leaseMs: 1000,
        followEnabled: true,
        restoreComplete: true,
      },
    );

    expect(transition.state.followLease).toEqual({
      revision: 2,
      startedAtMs: 1000,
      expiresAtMs: 2000,
      correctionCount: 0,
    });
    expect(transition.state.operation).toMatchObject({
      purpose: 'contentFollow',
      edge: 'bottom',
      deadlineMs: 2000,
    });
    expect(transition.diagnostics[0]?.event).toBe('followLeaseStarted');
  });

  it('does not follow semantic content while detached', () => {
    const transition = reduceChatScrollCoordinator(
      createChatScrollCoordinatorState({ bottomAffinity: 'detached' }),
      {
        type: 'semanticContentChanged',
        revision: 2,
        reason: 'messageAppended',
        nowMs: 1000,
        leaseMs: 1000,
        followEnabled: true,
        restoreComplete: true,
      },
    );

    expect(transition.state.followLease).toBeNull();
    expect(transition.state.operation).toBeNull();
    expect(transition.state.lastSemanticRevision).toBe(2);
    expect(transition.diagnostics).toContainEqual({
      event: 'followLeaseSkipped',
      reason: 'messageAppended',
      details: {
        skipReason: 'detached',
        revision: 2,
      },
    });
  });

  it('renews a lease only for a new semantic revision', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'semanticContentChanged',
      revision: 1,
      reason: 'streamDelta',
      nowMs: 100,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    const operationId = state.operation!.id;

    const duplicate = reduceChatScrollCoordinator(state, {
      type: 'semanticContentChanged',
      revision: 1,
      reason: 'duplicateRender',
      nowMs: 700,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    expect(duplicate.state.followLease?.expiresAtMs).toBe(1100);
    expect(duplicate.diagnostics).toEqual([]);

    const renewed = reduceChatScrollCoordinator(duplicate.state, {
      type: 'semanticContentChanged',
      revision: 2,
      reason: 'streamDelta',
      nowMs: 700,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    expect(renewed.state.followLease?.expiresAtMs).toBe(1700);
    expect(renewed.state.operation?.id).toBe(operationId);
    expect(renewed.state.operation?.deadlineMs).toBe(1700);
    expect(renewed.diagnostics[0]?.event).toBe('followLeaseRenewed');
  });

  it('does not renew a lease from geometry feedback', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'semanticContentChanged',
      revision: 1,
      reason: 'messageAppended',
      nowMs: 100,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    const expiresAtMs = state.followLease!.expiresAtMs;

    for (const nowMs of [200, 400, 600, 800, 1000]) {
      const next = reduceChatScrollCoordinator(state, {
        type: 'geometryChanged',
        nowMs,
        reason: 'contentSizeChange',
      });
      state = next.state;
      expect(state.followLease?.expiresAtMs).toBe(expiresAtMs);
    }

    const expired = reduceChatScrollCoordinator(state, {
      type: 'geometryChanged',
      nowMs: 1101,
      reason: 'scrollInducedContentSizeChange',
    });
    expect(expired.state.followLease).toBeNull();
    expect(expired.state.operation).toBeNull();
    expect(expired.diagnostics.some((entry) => entry.event === 'followLeaseExpired')).toBe(true);
    expect(expired.diagnostics.some((entry) => entry.event === 'operationExpired')).toBe(true);
  });

  it('counts follow corrections across geometry-driven operation restarts', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'semanticContentChanged',
      revision: 1,
      reason: 'messageAppended',
      nowMs: 100,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    const firstOperationId = state.operation!.id;
    state = apply(state, {
      type: 'operationCorrectionIssued',
      operationId: firstOperationId,
      nowMs: 200,
    });
    state = apply(state, {
      type: 'operationCompleted',
      operationId: firstOperationId,
      reason: 'stable',
      nowMs: 300,
    });
    state = apply(state, {
      type: 'geometryChanged',
      nowMs: 400,
      reason: 'scrollInducedGeometry',
    });
    const secondOperationId = state.operation!.id;
    state = apply(state, {
      type: 'operationCorrectionIssued',
      operationId: secondOperationId,
      nowMs: 500,
    });

    expect(secondOperationId).not.toBe(firstOperationId);
    expect(state.followLease?.correctionCount).toBe(2);
  });

  it('cancels navigation and follow permission when interaction begins', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'semanticContentChanged',
      revision: 1,
      reason: 'streamDelta',
      nowMs: 100,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    const operationId = state.operation!.id;

    const transition = reduceChatScrollCoordinator(state, {
      type: 'interactionBegan',
      interaction: 'dragging',
      reason: 'scrollBeginDrag',
      nowMs: 200,
    });
    state = transition.state;

    expect(state.interaction).toBe('dragging');
    expect(state.followLease).toBeNull();
    expect(state.operation).toBeNull();
    expect(transition.effects).toContainEqual({
      type: 'cancelRuntimeOperation',
      operationId,
      reason: 'scrollBeginDrag',
    });

    const staleCompletion = reduceChatScrollCoordinator(state, {
      type: 'operationCompleted',
      operationId,
      reason: 'staleNativeResult',
      nowMs: 250,
    });
    expect(staleCompletion.state).toEqual(state);
  });

  it('latches manual detachment and cancels an active content-follow operation', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'semanticContentChanged',
      revision: 1,
      reason: 'streamDelta',
      nowMs: 100,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    const operationId = state.operation!.id;

    const transition = reduceChatScrollCoordinator(state, {
      type: 'manualAwayMotionDetected',
      reason: 'stableGeometryAwayMotion',
      nowMs: 200,
      deltaBottomGapPx: 11,
      deltaOffsetY: -11,
      recentProgrammaticWrite: false,
      movementOpposesProgrammaticTarget: false,
    });
    state = transition.state;

    expect(state.bottomAffinity).toBe('manuallyDetached');
    expect(state.followLease).toBeNull();
    expect(state.operation).toBeNull();
    expect(transition.effects).toContainEqual({
      type: 'cancelRuntimeOperation',
      operationId,
      reason: 'stableGeometryAwayMotion',
    });
    expect(transition.diagnostics).toContainEqual({
      event: 'manualBottomDetached',
      reason: 'stableGeometryAwayMotion',
      details: {
        deltaBottomGapPx: 11,
        deltaOffsetY: -11,
        recentProgrammaticWrite: false,
        movementOpposesProgrammaticTarget: false,
        cancelledOperationId: operationId,
        cancelledOperationPurpose: 'contentFollow',
      },
    });
  });

  it('does not reattach a manual detachment merely because interaction ends near bottom', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'manualAwayMotionDetected',
      reason: 'stableGeometryAwayMotion',
      nowMs: 100,
      deltaBottomGapPx: 3,
      deltaOffsetY: -3,
      recentProgrammaticWrite: false,
      movementOpposesProgrammaticTarget: false,
    });

    state = apply(state, {
      type: 'interactionEnded',
      atBottom: true,
      reason: 'scrollEndDrag',
      nowMs: 150,
    });

    expect(state.bottomAffinity).toBe('manuallyDetached');
  });

  it('does not open follow leases while manually detached', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'manualAwayMotionDetected',
      reason: 'stableGeometryAwayMotion',
      nowMs: 100,
      deltaBottomGapPx: 8,
      deltaOffsetY: -8,
      recentProgrammaticWrite: false,
      movementOpposesProgrammaticTarget: false,
    });

    const transition = reduceChatScrollCoordinator(state, {
      type: 'semanticContentChanged',
      revision: 2,
      reason: 'streamDelta',
      nowMs: 200,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });
    state = transition.state;

    expect(state.bottomAffinity).toBe('manuallyDetached');
    expect(state.followLease).toBeNull();
    expect(state.operation).toBeNull();
    expect(transition.diagnostics[0]).toMatchObject({
      event: 'followLeaseSkipped',
      details: {
        skipReason: 'manuallyDetached',
      },
    });
  });

  it('re-pins without starting a lease when manual movement reaches bottom', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'manualAwayMotionDetected',
      reason: 'stableGeometryAwayMotion',
      nowMs: 100,
      deltaBottomGapPx: 40,
      deltaOffsetY: -40,
      recentProgrammaticWrite: false,
      movementOpposesProgrammaticTarget: false,
    });

    const transition = reduceChatScrollCoordinator(state, {
      type: 'manualReturnToBottomDetected',
      reason: 'stableGeometryReachedBottom',
      nowMs: 200,
      deltaTowardBottomPx: 40,
      deltaOffsetY: 40,
    });
    state = transition.state;

    expect(state.bottomAffinity).toBe('pinned');
    expect(state.followLease).toBeNull();
    expect(state.operation).toBeNull();
    expect(transition.effects).toEqual([]);
    expect(transition.diagnostics).toEqual([
      {
        event: 'manualBottomReattached',
        reason: 'stableGeometryReachedBottom',
        details: {
          deltaTowardBottomPx: 40,
          deltaOffsetY: 40,
        },
      },
    ]);
  });

  it('does not manually re-pin while navigation owns the viewport', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'manualAwayMotionDetected',
      reason: 'stableGeometryAwayMotion',
      nowMs: 100,
      deltaBottomGapPx: 40,
      deltaOffsetY: -40,
      recentProgrammaticWrite: false,
      movementOpposesProgrammaticTarget: false,
    });
    state = apply(state, {
      type: 'startNavigation',
      edge: 'bottom',
      source: 'manual',
      reason: 'scrollToBottom',
      nowMs: 150,
      maxDurationMs: 5000,
    });

    state = apply(state, {
      type: 'manualReturnToBottomDetected',
      reason: 'stableGeometryReachedBottom',
      nowMs: 200,
      deltaTowardBottomPx: 40,
      deltaOffsetY: 40,
    });

    expect(state.bottomAffinity).toBe('manuallyDetached');
    expect(state.operation?.purpose).toBe('navigation');
  });

  it('reattaches a manual detachment after explicit bottom navigation completes', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'manualAwayMotionDetected',
      reason: 'stableGeometryAwayMotion',
      nowMs: 100,
      deltaBottomGapPx: 8,
      deltaOffsetY: -8,
      recentProgrammaticWrite: false,
      movementOpposesProgrammaticTarget: false,
    });
    state = apply(state, {
      type: 'startNavigation',
      edge: 'bottom',
      source: 'manual',
      reason: 'scrollToBottom',
      nowMs: 200,
      maxDurationMs: 5000,
    });
    const operationId = state.operation!.id;
    state = apply(state, {
      type: 'operationCompleted',
      operationId,
      reason: 'stable',
      nowMs: 300,
    });

    expect(state.bottomAffinity).toBe('pinned');
  });

  it('uses interaction end to determine future follow eligibility', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'interactionBegan',
      interaction: 'dragging',
      reason: 'scrollBeginDrag',
      nowMs: 100,
    });
    state = apply(state, {
      type: 'interactionEnded',
      atBottom: false,
      reason: 'scrollEndDrag',
      nowMs: 200,
    });
    expect(state.bottomAffinity).toBe('detached');

    state = apply(state, {
      type: 'interactionBegan',
      interaction: 'dragging',
      reason: 'scrollBeginDrag',
      nowMs: 300,
    });
    state = apply(state, {
      type: 'interactionEnded',
      atBottom: true,
      reason: 'scrollEndDrag',
      nowMs: 400,
    });
    expect(state.bottomAffinity).toBe('pinned');
  });

  it('ignores semantic follow while a navigation operation is active', () => {
    let state = apply(createChatScrollCoordinatorState(), {
      type: 'startNavigation',
      edge: 'bottom',
      source: 'manual',
      reason: 'button',
      nowMs: 100,
      maxDurationMs: 5000,
    });
    const operationId = state.operation!.id;

    state = apply(state, {
      type: 'semanticContentChanged',
      revision: 2,
      reason: 'streamDelta',
      nowMs: 200,
      leaseMs: 1000,
      followEnabled: true,
      restoreComplete: true,
    });

    expect(state.operation?.id).toBe(operationId);
    expect(state.operation?.purpose).toBe('navigation');
    expect(state.followLease).toBeNull();
  });

  it('computes edge observations without issuing policy decisions', () => {
    expect(
      observeChatScrollEdge({
        edge: 'bottom',
        offsetY: 695,
        contentHeight: 1000,
        viewportHeight: 300,
        epsilonPx: 4,
      }),
    ).toEqual({
      targetOffsetY: 700,
      edgeGapPx: 5,
      withinEpsilon: false,
    });
    expect(
      observeChatScrollEdge({
        edge: 'top',
        offsetY: 3,
        contentHeight: 1000,
        viewportHeight: 300,
        epsilonPx: 4,
      }).withinEpsilon,
    ).toBe(true);
  });

  it('bounds reconciliation independently by deadline and correction count', () => {
    expect(
      evaluateChatScrollOperationBudget({
        nowMs: 999,
        deadlineMs: 1000,
        corrections: 2,
        maxCorrections: 3,
      }),
    ).toBe('continue');
    expect(
      evaluateChatScrollOperationBudget({
        nowMs: 1001,
        deadlineMs: 1000,
        corrections: 0,
        maxCorrections: 3,
      }),
    ).toBe('expired');
    expect(
      evaluateChatScrollOperationBudget({
        nowMs: 500,
        deadlineMs: 1000,
        corrections: 3,
        maxCorrections: 3,
      }),
    ).toBe('correctionLimit');
  });
});