import { AppState } from 'react-native';
import { useEffect, useMemo, useState } from 'react';
import type {
  ConnectionRecord,
  ConnectionSessionStatusReader,
  SessionRequestStatus,
} from '@crystal-lattice/frontend-sdk';

export type SessionStatusesByConnection = Record<
  string,
  Record<string, SessionRequestStatus>
>;

export function useSessionRequestStatuses(options: {
  enabled: boolean;
  connections: readonly ConnectionRecord[];
  sessionIdsByConnection: Readonly<Record<string, readonly string[]>>;
  reader: ConnectionSessionStatusReader;
  intervalMs?: number;
  maxBackoffMs?: number;
  onMissingSessionIds?: (
    connectionId: string,
    sessionIds: readonly string[],
  ) => void;
}): SessionStatusesByConnection {
  const {
    enabled,
    connections,
    sessionIdsByConnection,
    reader,
    intervalMs = 10_000,
    maxBackoffMs = 60_000,
    onMissingSessionIds,
  } = options;
  const [foreground, setForeground] = useState(AppState.currentState === 'active');
  const [statuses, setStatuses] = useState<SessionStatusesByConnection>({});
  const connectionById = useMemo(
    () => new Map(connections.map((connection) => [connection.id, connection])),
    [connections],
  );
  const requestKey = useMemo(
    () =>
      Object.entries(sessionIdsByConnection)
        .map(([connectionId, sessionIds]) => [
          connectionId,
          [...new Set(sessionIds)].sort(),
        ] as const)
        .filter(([, sessionIds]) => sessionIds.length > 0)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([connectionId, sessionIds]) => `${connectionId}:${sessionIds.join(',')}`)
        .join('|'),
    [sessionIdsByConnection],
  );

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      setForeground(state === 'active');
    });
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    if (!enabled || !foreground || !requestKey) return;
    let cancelled = false;
    const timers = new Map<string, ReturnType<typeof setTimeout>>();
    const failureCounts = new Map<string, number>();
    const controller = new AbortController();
    const groups = Object.entries(sessionIdsByConnection)
      .map(([connectionId, sessionIds]) => ({
        connectionId,
        sessionIds: [...new Set(sessionIds)],
        connection: connectionById.get(connectionId),
      }))
      .filter(
        (
          group,
        ): group is {
          connectionId: string;
          sessionIds: string[];
          connection: ConnectionRecord;
        } => !!group.connection && group.sessionIds.length > 0,
      );

    const pollGroup = async (group: (typeof groups)[number]) => {
      const result = await reader.getSessionRequestStatuses(
        group.connection,
        group.sessionIds,
        { signal: controller.signal },
      );
      if (cancelled) return;
      if (
        result.status === 'ok' &&
        result.snapshot.missing_session_ids.length > 0
      ) {
        onMissingSessionIds?.(
          group.connectionId,
          result.snapshot.missing_session_ids,
        );
      }
      setStatuses((current) => {
        const next = { ...current };
        if (result.status === 'ok') {
          next[group.connectionId] = Object.fromEntries(
            result.snapshot.statuses.map((status) => [
              status.session_id,
              status,
            ]),
          );
        } else {
          const prior = next[group.connectionId] ?? {};
          next[group.connectionId] = Object.fromEntries(
            Object.entries(prior).filter(
              ([, status]) => status.state !== 'running',
            ),
          );
        }
        return next;
      });

      if (result.status === 'unsupported') return;
      const failureCount =
        result.status === 'ok'
          ? 0
          : (failureCounts.get(group.connectionId) ?? 0) + 1;
      failureCounts.set(group.connectionId, failureCount);
      const delay =
        result.status === 'ok'
          ? intervalMs
          : Math.min(maxBackoffMs, intervalMs * 2 ** failureCount);
      timers.set(
        group.connectionId,
        setTimeout(() => {
          void pollGroup(group);
        }, delay),
      );
    };

    for (const group of groups) {
      void pollGroup(group);
    }
    return () => {
      cancelled = true;
      controller.abort();
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, [
    connectionById,
    enabled,
    foreground,
    intervalMs,
    maxBackoffMs,
    onMissingSessionIds,
    reader,
    requestKey,
    sessionIdsByConnection,
  ]);

  return statuses;
}