import type { AgentBackend } from '../backend/backend';
import type { Event } from '../types/events';

export type PollingStatus = 'idle' | 'running' | 'error';

export interface PollingEventSourceOptions {
  intervalMs?: number;
  backoffMs?: number;
}

export class PollingEventSource {
  private backend: AgentBackend;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private sessionId: string | null = null;
  private sinceId: string | null = null;
  private onEvents: ((events: Event[]) => void) | null = null;
  private lastEventId: string | null = null;
  private status: PollingStatus = 'idle';
  private stopped = false;
  private generation = 0;
  private readonly intervalMs: number;
  private readonly backoffMs: number;

  constructor(backend: AgentBackend, options: PollingEventSourceOptions = {}) {
    this.backend = backend;
    this.intervalMs = options.intervalMs ?? 1000;
    this.backoffMs = options.backoffMs ?? 5000;
  }

  start(options: {
    sessionId: string | null;
    initialSinceId: string | null;
    onEvents: (events: Event[]) => void;
  }): void {
    this.stop();
    this.generation += 1;
    this.sessionId = options.sessionId;
    this.onEvents = options.onEvents;
    this.sinceId = options.initialSinceId;
    this.lastEventId = options.initialSinceId;
    this.stopped = false;
    this.status = 'running';
    if (options.initialSinceId == null) {
      void this.bootstrapCursorAndSchedulePoll(this.generation);
    } else {
      this.schedulePoll(0);
    }
  }

  stop(): void {
    this.stopped = true;
    this.generation += 1;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.status = 'idle';
  }

  getLastEventId(): string | null {
    return this.lastEventId;
  }

  getStatus(): PollingStatus {
    return this.status;
  }

  private schedulePoll(delayMs: number): void {
    if (this.stopped) return;
    if (this.timer) {
      clearTimeout(this.timer);
    }
    this.timer = setTimeout(() => {
      this.pollOnce().catch(() => {
        // Errors are handled inside pollOnce.
      });
    }, delayMs);
  }

  private async bootstrapCursorAndSchedulePoll(generation: number): Promise<void> {
    let latestEventId: string | null = null;
    try {
      latestEventId = await this.backend.getLatestEventId();
    } catch {
      latestEventId = null;
    }

    if (this.stopped || generation !== this.generation) {
      return;
    }

    const stabilizedSinceId =
      (typeof latestEventId === 'string' && latestEventId) ? latestEventId : '0';
    this.sinceId = stabilizedSinceId;
    this.lastEventId = stabilizedSinceId;
    this.schedulePoll(0);
  }

  private async pollOnce(): Promise<void> {
    if (this.stopped) return;
    const generation = this.generation;
    if (!this.sessionId || !this.onEvents) {
      this.schedulePoll(this.intervalMs);
      return;
    }

    try {
      const result = await this.backend.listEvents({
        sessionId: this.sessionId,
        sinceId: this.sinceId ?? undefined,
      });
      const events = result.events;
      const latestEventId = result.latestEventId;

      if (this.stopped || generation !== this.generation) {
        return;
      }

      if (events.length > 0) {
        let maxId: string | null = this.sinceId;
        for (const ev of events) {
          const raw = (ev as any).event_id;
          if (typeof raw !== 'string') continue;
          if (maxId == null) {
            maxId = raw;
          } else {
            const current = parseInt(maxId, 10);
            const next = parseInt(raw, 10);
            if (!Number.isNaN(next) && (Number.isNaN(current) || next > current)) {
              maxId = raw;
            }
          }
        }

        this.lastEventId = maxId;
        this.sinceId = maxId;
        this.onEvents(events);
      } else if (typeof latestEventId === 'string' && latestEventId) {
        this.lastEventId = latestEventId;
        this.sinceId = latestEventId;
      }

      this.status = 'running';
      this.schedulePoll(this.intervalMs);
    } catch {
      this.status = 'error';
      this.schedulePoll(this.backoffMs);
    }
  }
}
