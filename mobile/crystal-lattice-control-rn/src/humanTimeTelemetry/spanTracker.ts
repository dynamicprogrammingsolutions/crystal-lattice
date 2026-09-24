import { toIsoUtc, type HumanTimeSpan } from './spans';

export type { HumanTimeSpan };

export const DEFAULT_SPAN_INACTIVITY_MS = 30_000;

interface OpenSpan {
  sessionId: string | null;
  fromMs: number;
  toMs: number;
}

export interface HumanTimeSpanTrackerOptions {
  /** Called with each closed span; the tracker never throws into it. */
  onSpanClosed: (span: HumanTimeSpan) => void;
  /** Inactivity interval that closes the open span. Default 30s. */
  inactivityMs?: number;
  /** Injectable clock for tests. */
  now?: () => number;
}

/**
 * Tracks user activity bursts as human time spans: the first activity on a
 * surface opens a span, each further activity extends it, and inactivity
 * closes it (from = first activity, to = last activity). Switching surfaces
 * closes the current span and opens the next one.
 */
export class HumanTimeSpanTracker {
  private readonly onSpanClosed: (span: HumanTimeSpan) => void;
  private readonly inactivityMs: number;
  private readonly now: () => number;
  private openSpan: OpenSpan | null = null;
  private inactivityTimer: ReturnType<typeof setTimeout> | null = null;
  private disposed = false;

  constructor(options: HumanTimeSpanTrackerOptions) {
    this.onSpanClosed = options.onSpanClosed;
    this.inactivityMs = options.inactivityMs ?? DEFAULT_SPAN_INACTIVITY_MS;
    this.now = options.now ?? (() => Date.now());
  }

  recordActivity(sessionId: string | null, atMs?: number): void {
    if (this.disposed) return;
    const at = atMs ?? this.now();
    if (this.openSpan && this.openSpan.sessionId !== sessionId) {
      this.emitOpenSpan();
    }
    if (!this.openSpan) {
      this.openSpan = { sessionId, fromMs: at, toMs: at };
    } else {
      this.openSpan.toMs = Math.max(this.openSpan.toMs, at);
    }
    this.scheduleInactivityClose();
  }

  /** Close the open span immediately (app background, disconnect, teardown). */
  close(): void {
    if (!this.openSpan) return;
    this.emitOpenSpan();
  }

  hasOpenSpan(): boolean {
    return this.openSpan !== null;
  }

  getOpenSpan(): HumanTimeSpan | null {
    const open = this.openSpan;
    if (!open) return null;
    return {
      sessionId: open.sessionId,
      from: toIsoUtc(open.fromMs),
      to: toIsoUtc(open.toMs),
    };
  }

  /** Stop tracking; drops the open span without emitting. */
  dispose(): void {
    this.disposed = true;
    this.cancelInactivityClose();
    this.openSpan = null;
  }

  private emitOpenSpan(): void {
    const open = this.openSpan;
    if (!open) return;
    this.cancelInactivityClose();
    this.openSpan = null;
    const span: HumanTimeSpan = {
      sessionId: open.sessionId,
      from: toIsoUtc(open.fromMs),
      to: toIsoUtc(open.toMs),
    };
    try {
      this.onSpanClosed(span);
    } catch {
      // Telemetry must never break the caller.
    }
  }

  private scheduleInactivityClose(): void {
    this.cancelInactivityClose();
    this.inactivityTimer = setTimeout(() => {
      this.inactivityTimer = null;
      if (this.openSpan) {
        this.emitOpenSpan();
      }
    }, this.inactivityMs);
  }

  private cancelInactivityClose(): void {
    if (this.inactivityTimer !== null) {
      clearTimeout(this.inactivityTimer);
      this.inactivityTimer = null;
    }
  }
}