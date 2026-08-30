export type SessionRequestStatusState =
  | 'idle'
  | 'not_started'
  | 'running'
  | 'succeeded'
  | 'interrupted';

export type SessionRequestStatusBasis = 'active_request' | 'session_tail';

export interface SessionRequestStatus {
  session_id: string;
  request_id: string | null;
  state: SessionRequestStatusState;
  basis: SessionRequestStatusBasis;
  session_modified: number;
}

export interface SessionRequestStatusSnapshot {
  version: 1;
  authority: 'derived_transient' | 'persisted' | (string & {});
  generated_at?: string;
  statuses: SessionRequestStatus[];
  missing_session_ids: string[];
}

const STATUS_STATES = new Set<SessionRequestStatusState>([
  'idle',
  'not_started',
  'running',
  'succeeded',
  'interrupted',
]);
const STATUS_BASES = new Set<SessionRequestStatusBasis>([
  'active_request',
  'session_tail',
]);

export function normalizeSessionRequestStatusSnapshot(
  value: unknown,
): SessionRequestStatusSnapshot {
  const root = value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
  const rawStatuses = Array.isArray(root.statuses) ? root.statuses : [];
  const statuses: SessionRequestStatus[] = [];
  for (const rawStatus of rawStatuses) {
    if (!rawStatus || typeof rawStatus !== 'object') continue;
    const status = rawStatus as Record<string, unknown>;
    if (
      typeof status.session_id !== 'string' ||
      !status.session_id ||
      typeof status.state !== 'string' ||
      !STATUS_STATES.has(status.state as SessionRequestStatusState) ||
      typeof status.basis !== 'string' ||
      !STATUS_BASES.has(status.basis as SessionRequestStatusBasis) ||
      typeof status.session_modified !== 'number' ||
      !Number.isFinite(status.session_modified)
    ) {
      continue;
    }
    statuses.push({
      session_id: status.session_id,
      request_id:
        typeof status.request_id === 'string' && status.request_id
          ? status.request_id
          : null,
      state: status.state as SessionRequestStatusState,
      basis: status.basis as SessionRequestStatusBasis,
      session_modified: status.session_modified,
    });
  }

  const missingSessionIds = Array.isArray(root.missing_session_ids)
    ? root.missing_session_ids.filter(
        (sessionId): sessionId is string =>
          typeof sessionId === 'string' && sessionId.length > 0,
      )
    : [];

  return {
    version: 1,
    authority:
      typeof root.authority === 'string' && root.authority
        ? root.authority as SessionRequestStatusSnapshot['authority']
        : 'derived_transient',
    ...(typeof root.generated_at === 'string'
      ? { generated_at: root.generated_at }
      : {}),
    statuses,
    missing_session_ids: missingSessionIds,
  };
}