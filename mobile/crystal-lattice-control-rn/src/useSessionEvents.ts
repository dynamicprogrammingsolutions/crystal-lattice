import { useEffect, useRef, useState } from 'react';
import type { ConnectionAdapter } from '../App';
import { apiListEvents, type ListEventsParams } from './api';
import type { Event } from './eventsTypes';

type SourceStatus = 'idle' | 'running' | 'error';

interface SessionEventSource {
  start(options: {
    sessionId: string | null;
    initialSinceId: string | null;
    onEvents: (events: Event[]) => void;
  }): void;
  stop(): void;
  getLastEventId(): string | null;
  getStatus(): SourceStatus;
}

class PollingEventSource implements SessionEventSource {
  private adapter: ConnectionAdapter;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private sessionId: string | null = null;
  private sinceId: string | null = null;
  private onEvents: ((events: Event[]) => void) | null = null;
  private lastEventId: string | null = null;
  private status: SourceStatus = 'idle';
  private stopped = false;
  private readonly intervalMs: number;
  private readonly backoffMs: number;

  constructor(adapter: ConnectionAdapter, intervalMs = 1000, backoffMs = 5000) {
    this.adapter = adapter;
    this.intervalMs = intervalMs;
    this.backoffMs = backoffMs;
  }

  start(options: {
    sessionId: string | null;
    initialSinceId: string | null;
    onEvents: (events: Event[]) => void;
  }): void {
    this.stop();
    this.sessionId = options.sessionId;
    this.onEvents = options.onEvents;
    this.sinceId = options.initialSinceId;
    this.lastEventId = options.initialSinceId;
    this.stopped = false;
    this.status = 'running';
    this.schedulePoll(0);
  }

  stop(): void {
    this.stopped = true;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.status = 'idle';
  }

  getLastEventId(): string | null {
    return this.lastEventId;
  }

  getStatus(): SourceStatus {
    return this.status;
  }

  private schedulePoll(delayMs: number): void {
    if (this.stopped) return;
    if (this.timer) {
      clearTimeout(this.timer);
    }
    this.timer = setTimeout(() => {
      this.pollOnce().catch(() => {
        // Errors are handled inside pollOnce; we ignore here.
      });
    }, delayMs);
  }

  private async pollOnce(): Promise<void> {
    if (this.stopped) return;
    if (!this.sessionId || !this.onEvents) {
      this.schedulePoll(this.intervalMs);
      return;
    }

    const params: ListEventsParams = {
      sessionId: this.sessionId,
      sinceId: this.sinceId ?? undefined,
      limit: 100,
    };

    try {
      const events = await apiListEvents(this.adapter, params);
      if (events.length > 0) {
        // Compute the maximum event_id as a number where possible.
        let maxId: string | null = this.sinceId;
        for (const ev of events) {
          const raw = ev.event_id;
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
      }
      this.status = 'running';
      this.schedulePoll(this.intervalMs);
    } catch (err) {
      // Keep the existing sinceId so we resume from the same point.
      this.status = 'error';
      this.schedulePoll(this.backoffMs);
    }
  }
}

export interface UseSessionEventsOptions {
  adapter: ConnectionAdapter | null;
  sessionId: string | null;
  enabled: boolean;
  initialSinceId: string | null;
}

export interface UseSessionEventsResult {
  lastEventId: string | null;
  status: SourceStatus;
  error: Error | null;
}

export function useSessionEvents(
  options: UseSessionEventsOptions,
  onEvents: (events: Event[]) => void,
): UseSessionEventsResult {
  const { adapter, sessionId, enabled, initialSinceId } = options;
  const [lastEventId, setLastEventId] = useState<string | null>(initialSinceId);
  const [status, setStatus] = useState<SourceStatus>('idle');
  const [error, setError] = useState<Error | null>(null);
  const sourceRef = useRef<SessionEventSource | null>(null);

  const onEventsRef = useRef<(events: Event[]) => void>(onEvents);

  // Keep a stable reference to the latest onEvents callback without
  // forcing the polling source to be recreated on every render.
  useEffect(() => {
    onEventsRef.current = onEvents;
  }, [onEvents]);

  useEffect(() => {
    // Tear down any existing source.
    if (sourceRef.current) {
      sourceRef.current.stop();
      sourceRef.current = null;
    }

    if (!adapter || !enabled || !sessionId) {
      setStatus('idle');
      return;
    }

    const source = new PollingEventSource(adapter);
    sourceRef.current = source;

    const handleEvents = (events: Event[]) => {
      try {
        const cb = onEventsRef.current;
        if (cb) {
          cb(events);
        }
        setLastEventId(source.getLastEventId());
        setStatus(source.getStatus());
        setError(null);
      } catch (e) {
        setError(e as Error);
      }
    };

    source.start({ sessionId, initialSinceId, onEvents: handleEvents });
    setStatus(source.getStatus());

    return () => {
      source.stop();
      sourceRef.current = null;
    };
  }, [adapter, sessionId, enabled, initialSinceId]);

  return { lastEventId, status, error };
}
