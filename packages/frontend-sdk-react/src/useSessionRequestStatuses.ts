import { useEffect, useMemo, useRef, useState } from "react";

import type {
  ConnectionRecord,
  ConnectionSessionStatusReader,
  ConnectionSessionStatusResult,
  SessionRequestStatus,
} from "@crystal-lattice/frontend-sdk";

export type SessionStatusesByConnection = Record<
  string,
  Record<string, SessionRequestStatus>
>;

export const DEFAULT_SESSION_STATUS_BATCH_SIZE = 100;
export const DEFAULT_RUNNING_STATUS_STALE_MS = 60_000;

export interface UseSessionRequestStatusesOptions {
  active: boolean;
  connections: readonly ConnectionRecord[];
  sessionIdsByConnection: Readonly<Record<string, readonly string[]>>;
  reader: ConnectionSessionStatusReader;
  intervalMs?: number;
  maxBackoffMs?: number;
  batchSize?: number;
  runningStatusStaleMs?: number;
  onMissingSessionIds?: (
    connectionId: string,
    sessionIds: readonly string[]
  ) => void;
}

export interface SessionStatusRequestGroup {
  connectionId: string;
  connection: ConnectionRecord;
  sessionIds: string[];
  batches: string[][];
}

interface StatusObservationTimes {
  [connectionId: string]: Record<string, number>;
}

function uniqueSessionIds(sessionIds: readonly string[]): string[] {
  const seen = new Set<string>();
  const unique: string[] = [];
  for (const sessionId of sessionIds) {
    if (!sessionId || seen.has(sessionId)) continue;
    seen.add(sessionId);
    unique.push(sessionId);
  }
  return unique;
}

export function splitSessionStatusBatches(
  sessionIds: readonly string[],
  batchSize: number
): string[][] {
  const safeBatchSize = Number.isFinite(batchSize)
    ? Math.max(1, Math.floor(batchSize))
    : DEFAULT_SESSION_STATUS_BATCH_SIZE;
  const batches: string[][] = [];
  for (let index = 0; index < sessionIds.length; index += safeBatchSize) {
    batches.push(sessionIds.slice(index, index + safeBatchSize));
  }
  return batches;
}

export function buildSessionStatusRequestGroups(
  connections: readonly ConnectionRecord[],
  sessionIdsByConnection: Readonly<Record<string, readonly string[]>>,
  batchSize: number
): SessionStatusRequestGroup[] {
  const connectionById = new Map(
    connections.map((connection) => [connection.id, connection])
  );
  return Object.entries(sessionIdsByConnection)
    .sort(([left], [right]) => left.localeCompare(right))
    .flatMap(([connectionId, rawSessionIds]) => {
      const connection = connectionById.get(connectionId);
      const sessionIds = uniqueSessionIds(rawSessionIds);
      if (!connection || sessionIds.length === 0) return [];
      return [
        {
          connectionId,
          connection,
          sessionIds,
          batches: splitSessionStatusBatches(sessionIds, batchSize),
        },
      ];
    });
}

export function mergeSuccessfulStatusBatch(
  current: Readonly<Record<string, SessionRequestStatus>>,
  requestedSessionIds: readonly string[],
  statuses: readonly SessionRequestStatus[]
): Record<string, SessionRequestStatus> {
  const requested = new Set(requestedSessionIds);
  const next = { ...current };
  for (const sessionId of requested) delete next[sessionId];
  for (const status of statuses) {
    if (requested.has(status.session_id)) {
      next[status.session_id] = status;
    }
  }
  return next;
}

export function removeExpiredRunningStatuses(
  current: Readonly<Record<string, SessionRequestStatus>>,
  requestedSessionIds: readonly string[],
  observedAtBySessionId: Readonly<Record<string, number>>,
  nowMs: number,
  staleAfterMs: number,
  force = false
): Record<string, SessionRequestStatus> {
  let next: Record<string, SessionRequestStatus> | null = null;
  for (const sessionId of requestedSessionIds) {
    const status = current[sessionId];
    if (
      status?.state !== "running" ||
      (!force &&
        nowMs - (observedAtBySessionId[sessionId] ?? nowMs) < staleAfterMs)
    ) {
      continue;
    }
    next ??= { ...current };
    delete next[sessionId];
  }
  return next ?? (current as Record<string, SessionRequestStatus>);
}

export function pruneSessionStatusesToRequests(
  current: SessionStatusesByConnection,
  groups: readonly SessionStatusRequestGroup[]
): SessionStatusesByConnection {
  const requestedByConnection = new Map(
    groups.map((group) => [group.connectionId, new Set(group.sessionIds)])
  );
  let next: SessionStatusesByConnection | null = null;

  for (const [connectionId, statuses] of Object.entries(current)) {
    const requested = requestedByConnection.get(connectionId);
    if (!requested) {
      next ??= { ...current };
      delete next[connectionId];
      continue;
    }
    const retained = Object.fromEntries(
      Object.entries(statuses).filter(([sessionId]) => requested.has(sessionId))
    );
    if (Object.keys(retained).length !== Object.keys(statuses).length) {
      next ??= { ...current };
      next[connectionId] = retained;
    }
  }

  return next ?? current;
}

function pruneObservationTimes(
  current: StatusObservationTimes,
  groups: readonly SessionStatusRequestGroup[]
): StatusObservationTimes {
  const requestedByConnection = new Map(
    groups.map((group) => [group.connectionId, new Set(group.sessionIds)])
  );
  const next: StatusObservationTimes = {};
  for (const [connectionId, observations] of Object.entries(current)) {
    const requested = requestedByConnection.get(connectionId);
    if (!requested) continue;
    next[connectionId] = Object.fromEntries(
      Object.entries(observations).filter(([sessionId]) =>
        requested.has(sessionId)
      )
    );
  }
  return next;
}

function requestSessionIdsKey(
  sessionIdsByConnection: Readonly<Record<string, readonly string[]>>
): string {
  return JSON.stringify(
    Object.entries(sessionIdsByConnection)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([connectionId, sessionIds]) => [
        connectionId,
        uniqueSessionIds(sessionIds),
      ])
  );
}

function unavailableResult(): ConnectionSessionStatusResult {
  return { status: "unavailable" };
}

export function useSessionRequestStatuses({
  active,
  connections,
  sessionIdsByConnection,
  reader,
  intervalMs = 10_000,
  maxBackoffMs = 60_000,
  batchSize = DEFAULT_SESSION_STATUS_BATCH_SIZE,
  runningStatusStaleMs = DEFAULT_RUNNING_STATUS_STALE_MS,
  onMissingSessionIds,
}: UseSessionRequestStatusesOptions): SessionStatusesByConnection {
  const [statuses, setStatuses] = useState<SessionStatusesByConnection>({});
  const observedAtRef = useRef<StatusObservationTimes>({});
  const requestKey = requestSessionIdsKey(sessionIdsByConnection);
  const groups = useMemo(
    () =>
      buildSessionStatusRequestGroups(
        connections,
        sessionIdsByConnection,
        batchSize
      ),
    // requestKey is a complete canonical projection of the grouped IDs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [batchSize, connections, requestKey]
  );

  useEffect(() => {
    observedAtRef.current = pruneObservationTimes(
      observedAtRef.current,
      groups
    );
    setStatuses((current) => pruneSessionStatusesToRequests(current, groups));
  }, [groups]);

  useEffect(() => {
    if (!active || groups.length === 0) return;
    let cancelled = false;
    const timers = new Map<string, ReturnType<typeof setTimeout>>();
    const failureCounts = new Map<string, number>();
    const controller = new AbortController();

    const pollGroup = async (group: SessionStatusRequestGroup) => {
      const results = await Promise.all(
        group.batches.map(async (batch) => {
          try {
            return await reader.getSessionRequestStatuses(
              group.connection,
              batch,
              { signal: controller.signal }
            );
          } catch {
            return unavailableResult();
          }
        })
      );
      if (cancelled) return;

      const nowMs = Date.now();
      const missingSessionIds = new Set<string>();
      const observations = {
        ...(observedAtRef.current[group.connectionId] ?? {}),
      };
      results.forEach((result, index) => {
        if (result.status !== "ok") return;
        const batch = group.batches[index];
        for (const sessionId of batch) delete observations[sessionId];
        for (const status of result.snapshot.statuses) {
          if (batch.includes(status.session_id)) {
            observations[status.session_id] = nowMs;
          }
        }
        result.snapshot.missing_session_ids.forEach((sessionId) =>
          missingSessionIds.add(sessionId)
        );
      });
      observedAtRef.current = {
        ...observedAtRef.current,
        [group.connectionId]: observations,
      };

      setStatuses((current) => {
        let connectionStatuses = current[group.connectionId] ?? {};

        results.forEach((result, index) => {
          const batch = group.batches[index];
          if (result.status === "ok") {
            connectionStatuses = mergeSuccessfulStatusBatch(
              connectionStatuses,
              batch,
              result.snapshot.statuses
            );
            return;
          }

          const force = result.status !== "unavailable";
          connectionStatuses = removeExpiredRunningStatuses(
            connectionStatuses,
            batch,
            observations,
            nowMs,
            runningStatusStaleMs,
            force
          );
        });

        return {
          ...current,
          [group.connectionId]: connectionStatuses,
        };
      });

      if (missingSessionIds.size > 0) {
        onMissingSessionIds?.(group.connectionId, [...missingSessionIds]);
      }

      const allOk = results.every((result) => result.status === "ok");
      const unsupported = results.some(
        (result) => result.status === "unsupported"
      );
      if (unsupported) return;

      const failureCount = allOk
        ? 0
        : (failureCounts.get(group.connectionId) ?? 0) + 1;
      failureCounts.set(group.connectionId, failureCount);
      const delay = allOk
        ? intervalMs
        : Math.min(maxBackoffMs, intervalMs * 2 ** failureCount);
      timers.set(
        group.connectionId,
        setTimeout(() => {
          void pollGroup(group);
        }, delay)
      );
    };

    for (const group of groups) void pollGroup(group);
    return () => {
      cancelled = true;
      controller.abort();
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, [
    active,
    groups,
    intervalMs,
    maxBackoffMs,
    onMissingSessionIds,
    reader,
    runningStatusStaleMs,
  ]);

  return statuses;
}
