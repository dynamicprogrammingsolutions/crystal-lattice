import {
  createSingleFlightAnchorRetryController,
  type TranscriptAnchorDiagnostic,
} from "../src/components/transcriptAnchorRetry";

function flushMicrotasks(): Promise<void> {
  return Promise.resolve().then(() => {});
}

describe("single-flight transcript anchor retry", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("keeps one measurement in flight under repeated layout notifications", async () => {
    let concurrentMeasurements = 0;
    let maxConcurrentMeasurements = 0;
    let resolveMeasurement!: (value: number | null) => void;
    const diagnostics: TranscriptAnchorDiagnostic[] = [];
    const controller = createSingleFlightAnchorRetryController({
      now: () => Date.now(),
      requestFrame: (callback) => setTimeout(callback, 0),
      cancelFrame: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      setTimer: (callback, delayMs) => setTimeout(callback, delayMs),
      clearTimer: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      measure: () => {
        concurrentMeasurements += 1;
        maxConcurrentMeasurements = Math.max(
          maxConcurrentMeasurements,
          concurrentMeasurements
        );
        return new Promise<number | null>((resolve) => {
          resolveMeasurement = (value) => {
            concurrentMeasurements -= 1;
            resolve(value);
          };
        });
      },
      applyCorrection: jest.fn(),
      onDiagnostic: (diagnostic) => diagnostics.push(diagnostic),
    });

    controller.start({ key: "msg-1", offsetFromViewportTop: 20 });
    controller.notifyLayoutChanged();
    controller.notifyLayoutChanged();
    jest.advanceTimersByTime(0);
    await flushMicrotasks();
    expect(maxConcurrentMeasurements).toBe(1);

    controller.notifyLayoutChanged();
    controller.notifyLayoutChanged();
    expect(maxConcurrentMeasurements).toBe(1);
    resolveMeasurement(20);
    await flushMicrotasks();

    expect(controller.getPending()).toBeNull();
    expect(maxConcurrentMeasurements).toBe(1);
    expect(
      diagnostics.filter((entry) => entry.event === "anchorCompleted")
    ).toHaveLength(1);
  });

  test("waits for a stale measurement before starting a replacement", async () => {
    const resolvers: Array<(value: number | null) => void> = [];
    let concurrentMeasurements = 0;
    let maxConcurrentMeasurements = 0;
    const controller = createSingleFlightAnchorRetryController({
      now: () => Date.now(),
      requestFrame: (callback) => setTimeout(callback, 0),
      cancelFrame: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      setTimer: (callback, delayMs) => setTimeout(callback, delayMs),
      clearTimer: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      measure: () => {
        concurrentMeasurements += 1;
        maxConcurrentMeasurements = Math.max(
          maxConcurrentMeasurements,
          concurrentMeasurements
        );
        return new Promise<number | null>((resolve) => {
          resolvers.push((value) => {
            concurrentMeasurements -= 1;
            resolve(value);
          });
        });
      },
      applyCorrection: jest.fn(),
    });

    controller.start({ key: "msg-1", offsetFromViewportTop: 10 });
    jest.advanceTimersByTime(0);
    await flushMicrotasks();
    controller.start({ key: "msg-2", offsetFromViewportTop: 30 });
    jest.advanceTimersByTime(0);
    expect(maxConcurrentMeasurements).toBe(1);

    resolvers.shift()!(null);
    await flushMicrotasks();
    jest.advanceTimersByTime(0);
    await flushMicrotasks();
    expect(maxConcurrentMeasurements).toBe(1);
    expect(resolvers).toHaveLength(1);

    resolvers.shift()!(30);
    await flushMicrotasks();
    expect(controller.getPending()).toBeNull();
  });

  test("stops at the attempt bound and leaves no scheduled retry", async () => {
    const diagnostics: TranscriptAnchorDiagnostic[] = [];
    const applyCorrection = jest.fn();
    const controller = createSingleFlightAnchorRetryController({
      now: () => Date.now(),
      requestFrame: (callback) => setTimeout(callback, 0),
      cancelFrame: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      setTimer: (callback, delayMs) => setTimeout(callback, delayMs),
      clearTimer: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      measure: async () => null,
      applyCorrection,
      onDiagnostic: (diagnostic) => diagnostics.push(diagnostic),
      maxAttempts: 2,
      retryDelayMs: 10,
    });

    controller.start({ key: "msg-1", offsetFromViewportTop: 10 });
    for (let attempt = 0; attempt < 6; attempt += 1) {
      jest.advanceTimersByTime(20);
      await flushMicrotasks();
    }

    expect(controller.getPending()).toBeNull();
    expect(applyCorrection).toHaveBeenCalledTimes(2);
    expect(diagnostics.at(-1)).toMatchObject({
      event: "anchorStopped",
      reason: "maxAttempts",
    });
    expect(jest.getTimerCount()).toBe(0);
  });

  test("cancels timers and ignores stale async completion on unmount", async () => {
    let resolveMeasurement!: (value: number | null) => void;
    const applyCorrection = jest.fn();
    const controller = createSingleFlightAnchorRetryController({
      now: () => Date.now(),
      requestFrame: (callback) => setTimeout(callback, 0),
      cancelFrame: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      setTimer: (callback, delayMs) => setTimeout(callback, delayMs),
      clearTimer: (handle) =>
        clearTimeout(handle as ReturnType<typeof setTimeout>),
      measure: () =>
        new Promise<number | null>((resolve) => {
          resolveMeasurement = resolve;
        }),
      applyCorrection,
    });

    controller.start({ key: "msg-1", offsetFromViewportTop: 10 });
    jest.advanceTimersByTime(0);
    await flushMicrotasks();
    controller.dispose();
    resolveMeasurement(null);
    await flushMicrotasks();
    jest.runOnlyPendingTimers();

    expect(controller.getPending()).toBeNull();
    expect(applyCorrection).not.toHaveBeenCalled();
    expect(jest.getTimerCount()).toBe(0);
  });
});
