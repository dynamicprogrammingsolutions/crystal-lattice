import { useEffect, useRef, useState } from 'react';
import type { AgentBackend, Event, PollingStatus } from '@crystal-lattice/frontend-sdk';
import { PollingEventSource } from '@crystal-lattice/frontend-sdk';

export interface UseSessionEventsOptions {
  backend: AgentBackend | null;
  sessionId: string | null;
  enabled: boolean;
  initialSinceId: string | null;
}

export interface UseSessionEventsResult {
  lastEventId: string | null;
  status: PollingStatus;
  error: Error | null;
}

export function useSessionEvents(
  options: UseSessionEventsOptions,
  onEvents: (events: Event[]) => void,
): UseSessionEventsResult {
  const { backend, sessionId, enabled, initialSinceId } = options;
  const [lastEventId, setLastEventId] = useState<string | null>(initialSinceId);
  const [status, setStatus] = useState<PollingStatus>('idle');
  const [error, setError] = useState<Error | null>(null);
  const sourceRef = useRef<PollingEventSource | null>(null);

  const onEventsRef = useRef<(events: Event[]) => void>(onEvents);

  useEffect(() => {
    onEventsRef.current = onEvents;
  }, [onEvents]);

  useEffect(() => {
    if (sourceRef.current) {
      sourceRef.current.stop();
      sourceRef.current = null;
    }

    if (!backend || !enabled || !sessionId) {
      setStatus('idle');
      return;
    }

    const source = new PollingEventSource(backend);
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
  }, [backend, sessionId, enabled, initialSinceId]);

  return { lastEventId, status, error };
}
