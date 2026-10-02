import { toIsoUtc, type HumanTimeSpan } from "./spans";

export type { HumanTimeSpan };

export const DEFAULT_SPAN_INACTIVITY_MS = 30_000;

interface OpenSpan {
  sessionId: string | null;
  fromMs: number;
  lastActivityMs: number;
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
  private inactivityMs: number;
  private readonly now: () => number;
  private openSpan: OpenSpan | null = null;
  private inactivityTimer: ReturnType<typeof setTimeout> | null = null;
  private disposed = false;

  constructor(options: HumanTimeSpanTrackerOptions) {
    this.onSpanClosed = options.onSpanClosed;
    this.inactivityMs = normalizeInactivityMs(options.inactivityMs);
    this.now = options.now ?? (() => Date.now());
  }

  recordActivity(sessionId: string | null, atMs?: number): void {
    if (this.disposed) return;
    const at = atMs ?? this.now();
    if (this.openSpan && this.openSpan.sessionId !== sessionId) {
      this.emitOpenSpan(at);
    }
    if (!this.openSpan) {
      this.openSpan = { sessionId, fromMs: at, lastActivityMs: at };
    } else {
      this.openSpan.lastActivityMs = Math.max(
        this.openSpan.lastActivityMs,
        at,
      );
    }
    this.scheduleInactivityClose();
  }

  /** Close the open span immediately (app background, disconnect, teardown). */
  close(atMs?: number): void {
    if (!this.openSpan) return;
    this.emitOpenSpan(atMs ?? this.now());
  }

  /**
   * Apply a new inactivity interval to subsequent activity. An open span is
   * closed first under the previous interval so changing settings never
   * silently retimes already-collected activity.
   */
  setInactivityMs(inactivityMs: number, atMs?: number): void {
    const normalized = normalizeInactivityMs(inactivityMs);
    if (normalized === this.inactivityMs) return;
    this.close(atMs);
    this.inactivityMs = normalized;
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
      to: toIsoUtc(open.lastActivityMs),
    };
  }

  /** Stop tracking; drops the open span without emitting. */
  dispose(): void {
    this.disposed = true;
    this.cancelInactivityClose();
    this.openSpan = null;
  }

  private emitOpenSpan(closeAtMs: number): void {
    const open = this.openSpan;
    if (!open) return;
    this.cancelInactivityClose();
    this.openSpan = null;
    const inactivityDeadlineMs = open.lastActivityMs + this.inactivityMs;
    const toMs = Math.max(
      open.lastActivityMs,
      Math.min(closeAtMs, inactivityDeadlineMs),
    );
    const span: HumanTimeSpan = {
      sessionId: open.sessionId,
      from: toIsoUtc(open.fromMs),
      to: toIsoUtc(toMs),
    };
    try {
      this.onSpanClosed(span);
    } catch {
      // Telemetry must never break the caller.
    }
  }

  private scheduleInactivityClose(): void {
    this.cancelInactivityClose();
    const inactivityDeadlineMs =
      (this.openSpan?.lastActivityMs ?? this.now()) + this.inactivityMs;
    this.inactivityTimer = setTimeout(() => {
      this.inactivityTimer = null;
      if (this.openSpan) {
        this.emitOpenSpan(inactivityDeadlineMs);
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

function normalizeInactivityMs(value: number | undefined): number {
  return Number.isFinite(value) && (value ?? 0) > 0
    ? Math.floor(value as number)
    : DEFAULT_SPAN_INACTIVITY_MS;
}
