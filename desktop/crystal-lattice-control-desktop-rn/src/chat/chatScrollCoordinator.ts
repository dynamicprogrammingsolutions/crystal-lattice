/**
 * Pure policy for transcript scrolling.
 *
 * Navigation is a fixed-deadline request to reach an edge. Content follow is
 * a separate lease that can only be opened or renewed by a semantic content
 * revision. Geometry events may reconcile an existing operation/lease, but
 * can never grant or extend follow permission.
 */
export type ChatScrollBottomAffinity = 'pinned' | 'detached';

export type ChatScrollInteraction = 'idle' | 'dragging' | 'momentum';

export type ChatScrollEdge = 'top' | 'bottom';

export type ChatScrollOperationPurpose = 'navigation' | 'contentFollow';

export type ChatScrollNavigationSource =
  | 'manual'
  | 'initialRestore'
  | 'anchorRestore';

export type ChatScrollOperation = {
  id: number;
  purpose: ChatScrollOperationPurpose;
  edge: ChatScrollEdge;
  source: ChatScrollNavigationSource | 'semanticContent';
  reason: string;
  startedAtMs: number;
  deadlineMs: number;
};

export type ChatScrollFollowLease = {
  revision: unknown;
  startedAtMs: number;
  expiresAtMs: number;
  correctionCount: number;
};

export type ChatScrollCoordinatorState = {
  bottomAffinity: ChatScrollBottomAffinity;
  interaction: ChatScrollInteraction;
  followLease: ChatScrollFollowLease | null;
  operation: ChatScrollOperation | null;
  nextOperationId: number;
  lastSemanticRevision: unknown;
};

export type ChatScrollCoordinatorEffect =
  | { type: 'cancelRuntimeOperation'; operationId: number; reason: string }
  | { type: 'scheduleRuntimeOperation'; operationId: number };

export type ChatScrollCoordinatorDiagnostic = {
  event: string;
  reason?: string;
  details?: Record<string, unknown>;
};

export type ChatScrollCoordinatorTransition = {
  state: ChatScrollCoordinatorState;
  effects: ChatScrollCoordinatorEffect[];
  diagnostics: ChatScrollCoordinatorDiagnostic[];
};

export type ChatScrollCoordinatorEvent =
  | {
      type: 'startNavigation';
      edge: ChatScrollEdge;
      source: ChatScrollNavigationSource;
      reason: string;
      nowMs: number;
      maxDurationMs: number;
    }
  | {
      type: 'semanticContentChanged';
      revision: unknown;
      reason: string;
      nowMs: number;
      leaseMs: number;
      followEnabled: boolean;
      restoreComplete: boolean;
    }
  | { type: 'geometryChanged'; nowMs: number; reason: string }
  | {
      type: 'interactionBegan';
      interaction: Exclude<ChatScrollInteraction, 'idle'>;
      reason: string;
      nowMs: number;
    }
  | { type: 'interactionEnded'; atBottom: boolean; reason: string; nowMs: number }
  | {
      type: 'setBottomAffinity';
      bottomAffinity: ChatScrollBottomAffinity;
      reason: string;
      nowMs: number;
    }
  | { type: 'operationCorrectionIssued'; operationId: number; nowMs: number }
  | { type: 'operationCompleted'; operationId: number; reason: string; nowMs: number }
  | {
      type: 'operationStopped';
      operationId: number;
      outcome: 'expired' | 'cancelled' | 'correctionLimit' | 'unavailable';
      reason: string;
      nowMs: number;
    }
  | { type: 'clear'; reason: string; nowMs: number };

export type ChatScrollEdgeObservation = {
  targetOffsetY: number;
  edgeGapPx: number;
  withinEpsilon: boolean;
};

export type ChatScrollOperationBudgetDecision =
  | 'continue'
  | 'expired'
  | 'correctionLimit';

function normalizedDuration(value: number): number {
  return Math.max(1, Math.round(Number.isFinite(value) ? value : 1));
}

function transition(
  state: ChatScrollCoordinatorState,
  options?: {
    effects?: ChatScrollCoordinatorEffect[];
    diagnostics?: ChatScrollCoordinatorDiagnostic[];
  },
): ChatScrollCoordinatorTransition {
  return {
    state,
    effects: options?.effects ?? [],
    diagnostics: options?.diagnostics ?? [],
  };
}

function startOperation(
  state: ChatScrollCoordinatorState,
  input: Omit<ChatScrollOperation, 'id'>,
): {
  state: ChatScrollCoordinatorState;
  operation: ChatScrollOperation;
} {
  const operation: ChatScrollOperation = {
    ...input,
    id: state.nextOperationId,
  };
  return {
    state: {
      ...state,
      operation,
      nextOperationId: state.nextOperationId + 1,
    },
    operation,
  };
}

function cancelOperationEffect(
  operation: ChatScrollOperation | null,
  reason: string,
): ChatScrollCoordinatorEffect[] {
  return operation
    ? [{ type: 'cancelRuntimeOperation', operationId: operation.id, reason }]
    : [];
}

function expireFollowLeaseIfNeeded(
  state: ChatScrollCoordinatorState,
  nowMs: number,
): {
  state: ChatScrollCoordinatorState;
  diagnostic: ChatScrollCoordinatorDiagnostic | null;
} {
  if (!state.followLease || nowMs <= state.followLease.expiresAtMs) {
    return { state, diagnostic: null };
  }
  return {
    state: {
      ...state,
      followLease: null,
    },
    diagnostic: {
      event: 'followLeaseExpired',
      details: {
        revision: state.followLease.revision,
        expiredAtMs: state.followLease.expiresAtMs,
      },
    },
  };
}

export function createChatScrollCoordinatorState(options?: {
  bottomAffinity?: ChatScrollBottomAffinity;
  initialSemanticRevision?: unknown;
}): ChatScrollCoordinatorState {
  return {
    bottomAffinity: options?.bottomAffinity ?? 'pinned',
    interaction: 'idle',
    followLease: null,
    operation: null,
    nextOperationId: 1,
    lastSemanticRevision: options?.initialSemanticRevision,
  };
}

export function reduceChatScrollCoordinator(
  previousState: ChatScrollCoordinatorState,
  event: ChatScrollCoordinatorEvent,
): ChatScrollCoordinatorTransition {
  if (event.type === 'startNavigation') {
    const effects = cancelOperationEffect(previousState.operation, 'navigationReplaced');
    const started = startOperation(
      {
        ...previousState,
        bottomAffinity: event.edge === 'top' ? 'detached' : previousState.bottomAffinity,
        followLease: null,
        interaction: 'idle',
        operation: null,
      },
      {
        purpose: 'navigation',
        edge: event.edge,
        source: event.source,
        reason: event.reason,
        startedAtMs: event.nowMs,
        deadlineMs: event.nowMs + normalizedDuration(event.maxDurationMs),
      },
    );
    return transition(started.state, {
      effects: [
        ...effects,
        { type: 'scheduleRuntimeOperation', operationId: started.operation.id },
      ],
      diagnostics: [
        {
          event: 'navigationStarted',
          reason: event.reason,
          details: {
            operationId: started.operation.id,
            edge: event.edge,
            source: event.source,
            deadlineMs: started.operation.deadlineMs,
          },
        },
      ],
    });
  }

  if (event.type === 'semanticContentChanged') {
    if (Object.is(previousState.lastSemanticRevision, event.revision)) {
      return transition(previousState);
    }

    let state: ChatScrollCoordinatorState = {
      ...previousState,
      lastSemanticRevision: event.revision,
    };

    const skipReason = !event.followEnabled
      ? 'followDisabled'
      : !event.restoreComplete
        ? 'restoreIncomplete'
        : state.interaction !== 'idle'
          ? 'userInteracting'
          : state.bottomAffinity !== 'pinned'
            ? 'detached'
            : state.operation?.purpose === 'navigation'
              ? 'navigationActive'
              : null;
    if (skipReason) {
      return transition(state, {
        diagnostics: [
          {
            event: 'followLeaseSkipped',
            reason: event.reason,
            details: {
              skipReason,
              revision: event.revision,
            },
          },
        ],
      });
    }

    const leaseMs = normalizedDuration(event.leaseMs);
    const lease: ChatScrollFollowLease = {
      revision: event.revision,
      startedAtMs: state.followLease?.startedAtMs ?? event.nowMs,
      expiresAtMs: event.nowMs + leaseMs,
      correctionCount: 0,
    };
    const renewing = state.followLease != null;
    state = {
      ...state,
      followLease: lease,
    };

    if (state.operation?.purpose === 'contentFollow') {
      const operation = {
        ...state.operation,
        deadlineMs: lease.expiresAtMs,
        reason: event.reason,
      };
      state = {
        ...state,
        operation,
      };
      return transition(state, {
        effects: [{ type: 'scheduleRuntimeOperation', operationId: operation.id }],
        diagnostics: [
          {
            event: 'followLeaseRenewed',
            reason: event.reason,
            details: {
              operationId: operation.id,
              revision: event.revision,
              expiresAtMs: lease.expiresAtMs,
            },
          },
        ],
      });
    }

    const started = startOperation(
      state,
      {
        purpose: 'contentFollow',
        edge: 'bottom',
        source: 'semanticContent',
        reason: event.reason,
        startedAtMs: event.nowMs,
        deadlineMs: lease.expiresAtMs,
      },
    );
    return transition(started.state, {
      effects: [{ type: 'scheduleRuntimeOperation', operationId: started.operation.id }],
      diagnostics: [
        {
          event: renewing ? 'followLeaseRenewed' : 'followLeaseStarted',
          reason: event.reason,
          details: {
            operationId: started.operation.id,
            revision: event.revision,
            expiresAtMs: lease.expiresAtMs,
          },
        },
      ],
    });
  }

  if (event.type === 'geometryChanged') {
    const expired = expireFollowLeaseIfNeeded(previousState, event.nowMs);
    let state = expired.state;
    const diagnostics = expired.diagnostic ? [expired.diagnostic] : [];

    if (state.operation) {
      if (event.nowMs > state.operation.deadlineMs) {
        const operation = state.operation;
        state = {
          ...state,
          operation: null,
        };
        return transition(state, {
          effects: [
            {
              type: 'cancelRuntimeOperation',
              operationId: operation.id,
              reason: 'deadlineExceededOnGeometryChange',
            },
          ],
          diagnostics: [
            ...diagnostics,
            {
              event: 'operationExpired',
              reason: event.reason,
              details: {
                operationId: operation.id,
                purpose: operation.purpose,
                edge: operation.edge,
              },
            },
          ],
        });
      }
      return transition(state, {
        effects: [{ type: 'scheduleRuntimeOperation', operationId: state.operation.id }],
        diagnostics,
      });
    }

    if (
      state.followLease &&
      state.interaction === 'idle' &&
      state.bottomAffinity === 'pinned'
    ) {
      const started = startOperation(
        state,
        {
          purpose: 'contentFollow',
          edge: 'bottom',
          source: 'semanticContent',
          reason: event.reason,
          startedAtMs: event.nowMs,
          deadlineMs: state.followLease.expiresAtMs,
        },
      );
      return transition(started.state, {
        effects: [{ type: 'scheduleRuntimeOperation', operationId: started.operation.id }],
        diagnostics,
      });
    }

    return transition(state, { diagnostics });
  }

  if (event.type === 'interactionBegan') {
    const operation = previousState.operation;
    return transition(
      {
        ...previousState,
        interaction: event.interaction,
        followLease: null,
        operation: null,
      },
      {
        effects: cancelOperationEffect(operation, event.reason),
        diagnostics: [
          {
            event: 'interactionBegan',
            reason: event.reason,
            details: {
              interaction: event.interaction,
              cancelledOperationId: operation?.id ?? null,
            },
          },
        ],
      },
    );
  }

  if (event.type === 'interactionEnded') {
    return transition(
      {
        ...previousState,
        interaction: 'idle',
        bottomAffinity: event.atBottom ? 'pinned' : 'detached',
        followLease: null,
        operation: null,
      },
      {
        diagnostics: [
          {
            event: 'interactionEnded',
            reason: event.reason,
            details: {
              atBottom: event.atBottom,
              bottomAffinity: event.atBottom ? 'pinned' : 'detached',
            },
          },
        ],
      },
    );
  }

  if (event.type === 'setBottomAffinity') {
    const operation = previousState.operation;
    return transition(
      {
        ...previousState,
        bottomAffinity: event.bottomAffinity,
        followLease: null,
        operation: null,
      },
      {
        effects: cancelOperationEffect(operation, event.reason),
        diagnostics: [
          {
            event: 'bottomAffinityChanged',
            reason: event.reason,
            details: {
              bottomAffinity: event.bottomAffinity,
              cancelledOperationId: operation?.id ?? null,
            },
          },
        ],
      },
    );
  }

  if (event.type === 'operationCorrectionIssued') {
    const operation = previousState.operation;
    if (
      !operation ||
      operation.id !== event.operationId ||
      operation.purpose !== 'contentFollow' ||
      !previousState.followLease
    ) {
      return transition(previousState);
    }
    return transition({
      ...previousState,
      followLease: {
        ...previousState.followLease,
        correctionCount: previousState.followLease.correctionCount + 1,
      },
    });
  }

  if (event.type === 'operationCompleted') {
    const operation = previousState.operation;
    if (!operation || operation.id !== event.operationId) {
      return transition(previousState);
    }
    const bottomAffinity =
      operation.purpose === 'navigation'
        ? operation.edge === 'bottom'
          ? 'pinned'
          : 'detached'
        : previousState.bottomAffinity;
    return transition(
      {
        ...previousState,
        bottomAffinity,
        operation: null,
      },
      {
        diagnostics: [
          {
            event: 'operationCompleted',
            reason: event.reason,
            details: {
              operationId: operation.id,
              purpose: operation.purpose,
              edge: operation.edge,
              bottomAffinity,
              durationMs: Math.max(0, event.nowMs - operation.startedAtMs),
            },
          },
        ],
      },
    );
  }

  if (event.type === 'operationStopped') {
    const operation = previousState.operation;
    if (!operation || operation.id !== event.operationId) {
      return transition(previousState);
    }
    const clearFollowLease =
      operation.purpose === 'contentFollow' &&
      (event.outcome === 'expired' ||
        event.outcome === 'correctionLimit' ||
        event.outcome === 'unavailable');
    return transition(
      {
        ...previousState,
        followLease: clearFollowLease ? null : previousState.followLease,
        operation: null,
      },
      {
        diagnostics: [
          {
            event:
              event.outcome === 'expired'
                ? 'operationExpired'
                : event.outcome === 'correctionLimit'
                  ? 'operationCorrectionLimit'
                  : event.outcome === 'unavailable'
                    ? 'operationUnavailable'
                    : 'operationCancelled',
            reason: event.reason,
            details: {
              operationId: operation.id,
              purpose: operation.purpose,
              edge: operation.edge,
              outcome: event.outcome,
              durationMs: Math.max(0, event.nowMs - operation.startedAtMs),
            },
          },
        ],
      },
    );
  }

  const operation = previousState.operation;
  return transition(
    {
      ...previousState,
      interaction: 'idle',
      followLease: null,
      operation: null,
    },
    {
      effects: cancelOperationEffect(operation, event.reason),
      diagnostics: operation
        ? [
            {
              event: 'operationCancelled',
              reason: event.reason,
              details: {
                operationId: operation.id,
                purpose: operation.purpose,
                edge: operation.edge,
              },
            },
          ]
        : [],
    },
  );
}

export function observeChatScrollEdge(input: {
  edge: ChatScrollEdge;
  offsetY: number;
  contentHeight: number;
  viewportHeight: number;
  epsilonPx: number;
}): ChatScrollEdgeObservation {
  const offsetY = Number.isFinite(input.offsetY) ? input.offsetY : 0;
  const contentHeight = Number.isFinite(input.contentHeight) ? input.contentHeight : 0;
  const viewportHeight = Number.isFinite(input.viewportHeight) ? input.viewportHeight : 0;
  const maxOffsetY = Math.max(0, contentHeight - viewportHeight);
  const targetOffsetY = input.edge === 'bottom' ? maxOffsetY : 0;
  const edgeGapPx =
    input.edge === 'bottom'
      ? Math.max(0, maxOffsetY - offsetY)
      : Math.max(0, offsetY);
  const epsilonPx = Math.max(0, Number.isFinite(input.epsilonPx) ? input.epsilonPx : 0);
  return {
    targetOffsetY,
    edgeGapPx,
    withinEpsilon: edgeGapPx <= epsilonPx,
  };
}

export function evaluateChatScrollOperationBudget(input: {
  nowMs: number;
  deadlineMs: number;
  corrections: number;
  maxCorrections: number;
}): ChatScrollOperationBudgetDecision {
  if (input.nowMs > input.deadlineMs) {
    return 'expired';
  }
  const corrections = Math.max(
    0,
    Math.floor(Number.isFinite(input.corrections) ? input.corrections : 0),
  );
  const maxCorrections = Math.max(
    1,
    Math.floor(Number.isFinite(input.maxCorrections) ? input.maxCorrections : 1),
  );
  return corrections >= maxCorrections ? 'correctionLimit' : 'continue';
}