export type TranscriptAnchorRequest = {
  key: string;
  offsetFromViewportTop: number;
};

export type TranscriptAnchorDiagnostic = {
  event:
    | "anchorStarted"
    | "anchorProgress"
    | "anchorCompleted"
    | "anchorStopped"
    | "anchorCancelled";
  reason?: string;
  details: {
    generation: number;
    key: string;
    attempts: number;
    durationMs: number;
    requestedOffset: number;
    actualOffset?: number | null;
  };
};

type PendingAnchorOperation = TranscriptAnchorRequest & {
  generation: number;
  attempts: number;
  startedAtMs: number;
  deadlineMs: number;
};

export type SingleFlightAnchorRetryController = {
  start: (request: TranscriptAnchorRequest) => void;
  notifyLayoutChanged: () => void;
  cancel: (reason?: string) => void;
  dispose: () => void;
  getPending: () => PendingAnchorOperation | null;
};

export function createSingleFlightAnchorRetryController(options: {
  now: () => number;
  requestFrame: (callback: () => void) => unknown;
  cancelFrame: (handle: unknown) => void;
  setTimer: (callback: () => void, delayMs: number) => unknown;
  clearTimer: (handle: unknown) => void;
  measure: (key: string) => Promise<number | null>;
  applyCorrection: (
    operation: PendingAnchorOperation,
    actualOffset: number | null
  ) => void;
  onDiagnostic?: (diagnostic: TranscriptAnchorDiagnostic) => void;
  timeoutMs?: number;
  maxAttempts?: number;
  tolerancePx?: number;
  retryDelayMs?: number;
}): SingleFlightAnchorRetryController {
  const timeoutMs = Math.max(100, options.timeoutMs ?? 5000);
  const maxAttempts = Math.max(1, options.maxAttempts ?? 30);
  const tolerancePx = Math.max(0, options.tolerancePx ?? 8);
  const retryDelayMs = Math.max(0, options.retryDelayMs ?? 50);

  let generation = 0;
  let pending: PendingAnchorOperation | null = null;
  let frameHandle: unknown = null;
  let timerHandle: unknown = null;
  let scheduled = false;
  let measuring = false;
  let disposed = false;

  const emit = (
    event: TranscriptAnchorDiagnostic["event"],
    operation: PendingAnchorOperation,
    reason?: string,
    actualOffset?: number | null
  ) => {
    options.onDiagnostic?.({
      event,
      reason,
      details: {
        generation: operation.generation,
        key: operation.key,
        attempts: operation.attempts,
        durationMs: Math.max(0, options.now() - operation.startedAtMs),
        requestedOffset: operation.offsetFromViewportTop,
        ...(actualOffset !== undefined ? { actualOffset } : {}),
      },
    });
  };

  const clearScheduled = () => {
    if (frameHandle != null) {
      options.cancelFrame(frameHandle);
      frameHandle = null;
    }
    if (timerHandle != null) {
      options.clearTimer(timerHandle);
      timerHandle = null;
    }
    scheduled = false;
  };

  const finish = (
    event: "anchorCompleted" | "anchorStopped",
    operation: PendingAnchorOperation,
    reason: string,
    actualOffset?: number | null
  ) => {
    if (pending !== operation) {
      return;
    }
    pending = null;
    clearScheduled();
    emit(event, operation, reason, actualOffset);
  };

  const schedule = (delayMs = 0) => {
    if (disposed || !pending || scheduled || measuring) {
      return;
    }
    scheduled = true;
    if (delayMs > 0) {
      timerHandle = options.setTimer(() => {
        timerHandle = null;
        scheduled = false;
        schedule();
      }, delayMs);
      return;
    }
    frameHandle = options.requestFrame(() => {
      frameHandle = null;
      scheduled = false;
      void run();
    });
  };

  const run = async () => {
    const operation = pending;
    if (disposed || !operation || measuring) {
      return;
    }
    measuring = true;
    let actualOffset: number | null = null;
    try {
      actualOffset = await options.measure(operation.key);
    } catch {
      actualOffset = null;
    } finally {
      measuring = false;
    }

    if (disposed) {
      return;
    }
    if (pending !== operation) {
      schedule();
      return;
    }
    if (
      actualOffset != null &&
      Math.abs(actualOffset - operation.offsetFromViewportTop) <= tolerancePx
    ) {
      finish("anchorCompleted", operation, "stable", actualOffset);
      return;
    }
    const now = options.now();
    if (now >= operation.deadlineMs) {
      finish("anchorStopped", operation, "deadline", actualOffset);
      return;
    }
    if (operation.attempts >= maxAttempts) {
      finish("anchorStopped", operation, "maxAttempts", actualOffset);
      return;
    }

    const nextOperation: PendingAnchorOperation = {
      ...operation,
      attempts: operation.attempts + 1,
    };
    pending = nextOperation;
    try {
      options.applyCorrection(nextOperation, actualOffset);
    } catch {
      finish("anchorStopped", nextOperation, "correctionError", actualOffset);
      return;
    }
    if (nextOperation.attempts === 1 || nextOperation.attempts % 10 === 0) {
      emit("anchorProgress", nextOperation, "retry", actualOffset);
    }
    schedule(retryDelayMs);
  };

  const cancel = (reason = "cancelled") => {
    const operation = pending;
    pending = null;
    generation += 1;
    clearScheduled();
    if (operation) {
      emit("anchorCancelled", operation, reason);
    }
  };

  return {
    start: (request) => {
      if (disposed) {
        return;
      }
      cancel("replaced");
      const startedAtMs = options.now();
      const operation: PendingAnchorOperation = {
        ...request,
        generation,
        attempts: 0,
        startedAtMs,
        deadlineMs: startedAtMs + timeoutMs,
      };
      pending = operation;
      emit("anchorStarted", operation);
      schedule();
    },
    notifyLayoutChanged: () => {
      schedule();
    },
    cancel,
    dispose: () => {
      cancel("unmount");
      disposed = true;
    },
    getPending: () => pending,
  };
}
