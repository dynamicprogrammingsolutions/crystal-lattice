import {
  HumanTimeSpanTracker,
  type HumanTimeSpan,
} from '../src/humanTimeTelemetry/spanTracker';

describe('HumanTimeSpanTracker', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  function createTracker(
    onSpanClosed: (span: HumanTimeSpan) => void,
    options: { inactivityMs?: number; now?: () => number } = {},
  ) {
    return new HumanTimeSpanTracker({
      onSpanClosed,
      inactivityMs: options.inactivityMs ?? 30_000,
      now: options.now,
    });
  }

  it('opens a span on activity and closes it after inactivity with from/to = first/last activity', () => {
    const closed: HumanTimeSpan[] = [];
    let clockMs = 1_000_000;
    const tracker = createTracker((span) => closed.push(span), {
      now: () => clockMs,
    });

    tracker.recordActivity('session-1');
    clockMs += 5_000;
    tracker.recordActivity('session-1');
    expect(closed).toEqual([]);

    jest.advanceTimersByTime(30_000);
    expect(closed).toEqual([
      {
        sessionId: 'session-1',
        from: new Date(1_000_000).toISOString(),
        to: new Date(1_005_000).toISOString(),
      },
    ]);
    tracker.dispose();
  });

  it('extends the span and resets the inactivity timer on each activity', () => {
    const closed: HumanTimeSpan[] = [];
    let clockMs = 2_000_000;
    const tracker = createTracker((span) => closed.push(span), {
      now: () => clockMs,
    });

    tracker.recordActivity('session-1');
    jest.advanceTimersByTime(20_000);
    clockMs += 25_000;
    tracker.recordActivity('session-1');
    // The first inactivity window elapsed without new activity in it, but
    // the second activity reset the timer, so nothing closed yet.
    jest.advanceTimersByTime(20_000);
    expect(closed).toEqual([]);

    jest.advanceTimersByTime(10_000);
    expect(closed).toEqual([
      {
        sessionId: 'session-1',
        from: new Date(2_000_000).toISOString(),
        to: new Date(2_025_000).toISOString(),
      },
    ]);
    tracker.dispose();
  });

  it('closes the current span and opens a new one when the surface switches', () => {
    const closed: HumanTimeSpan[] = [];
    let clockMs = 3_000_000;
    const tracker = createTracker((span) => closed.push(span), {
      now: () => clockMs,
    });

    tracker.recordActivity('session-1');
    clockMs += 4_000;
    tracker.recordActivity('session-2');
    // The session-1 span closed immediately at the switch.
    expect(closed).toEqual([
      {
        sessionId: 'session-1',
        from: new Date(3_000_000).toISOString(),
        to: new Date(3_000_000).toISOString(),
      },
    ]);

    clockMs += 2_000;
    tracker.recordActivity('session-2');
    jest.advanceTimersByTime(30_000);
    expect(closed).toEqual([
      closed[0],
      {
        sessionId: 'session-2',
        from: new Date(3_004_000).toISOString(),
        to: new Date(3_006_000).toISOString(),
      },
    ]);
    tracker.dispose();
  });

  it('attributes session-less activity to a null session id', () => {
    const closed: HumanTimeSpan[] = [];
    let clockMs = 4_000_000;
    const tracker = createTracker((span) => closed.push(span), {
      now: () => clockMs,
    });

    tracker.recordActivity(null);
    clockMs += 1_500;
    tracker.recordActivity(null);
    jest.advanceTimersByTime(30_000);

    expect(closed).toEqual([
      {
        sessionId: null,
        from: new Date(4_000_000).toISOString(),
        to: new Date(4_001_500).toISOString(),
      },
    ]);
    tracker.dispose();
  });

  it('emits a zero-duration span for a single activity burst', () => {
    const closed: HumanTimeSpan[] = [];
    const tracker = createTracker((span) => closed.push(span));

    tracker.recordActivity('session-1');
    jest.advanceTimersByTime(30_000);

    expect(closed).toHaveLength(1);
    expect(closed[0].sessionId).toBe('session-1');
    expect(closed[0].from).toBe(closed[0].to);
    tracker.dispose();
  });

  it('close() emits the open span immediately and cancels the timer', () => {
    const closed: HumanTimeSpan[] = [];
    let clockMs = 5_000_000;
    const tracker = createTracker((span) => closed.push(span), {
      now: () => clockMs,
    });

    tracker.recordActivity('session-1');
    clockMs += 8_000;
    tracker.recordActivity('session-1');
    tracker.close();

    expect(closed).toEqual([
      {
        sessionId: 'session-1',
        from: new Date(5_000_000).toISOString(),
        to: new Date(5_008_000).toISOString(),
      },
    ]);

    jest.advanceTimersByTime(60_000);
    expect(closed).toHaveLength(1);
    tracker.dispose();
  });

  it('close() without an open span emits nothing', () => {
    const closed: HumanTimeSpan[] = [];
    const tracker = createTracker((span) => closed.push(span));

    tracker.close();
    expect(closed).toEqual([]);
    tracker.dispose();
  });

  it('dispose() drops the open span and cancels timers without emitting', () => {
    const closed: HumanTimeSpan[] = [];
    const tracker = createTracker((span) => closed.push(span));

    tracker.recordActivity('session-1');
    tracker.dispose();

    jest.advanceTimersByTime(60_000);
    expect(closed).toEqual([]);
  });

  it('reopens tracking after an inactivity close when activity resumes', () => {
    const closed: HumanTimeSpan[] = [];
    let clockMs = 6_000_000;
    const tracker = createTracker((span) => closed.push(span), {
      now: () => clockMs,
    });

    tracker.recordActivity('session-1');
    jest.advanceTimersByTime(30_000);
    clockMs += 120_000;
    tracker.recordActivity('session-1');
    clockMs += 3_000;
    tracker.recordActivity('session-1');
    jest.advanceTimersByTime(30_000);

    expect(closed).toEqual([
      {
        sessionId: 'session-1',
        from: new Date(6_000_000).toISOString(),
        to: new Date(6_000_000).toISOString(),
      },
      {
        sessionId: 'session-1',
        from: new Date(6_120_000).toISOString(),
        to: new Date(6_123_000).toISOString(),
      },
    ]);
    tracker.dispose();
  });
});