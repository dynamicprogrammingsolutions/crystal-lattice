import type {
  SessionRequestStatus,
  SessionRequestStatusState,
} from '@crystal-lattice/frontend-sdk';

export type SessionRequestStatusTone =
  | 'neutral'
  | 'primary'
  | 'success'
  | 'warning';

export const SESSION_REQUEST_STATUS_LABELS: Record<
  SessionRequestStatusState,
  string
> = {
  idle: 'Idle',
  not_started: 'Not started',
  running: 'In progress',
  succeeded: 'Completed',
  interrupted: 'Interrupted',
};

export const SESSION_REQUEST_STATUS_TONES: Record<
  SessionRequestStatusState,
  SessionRequestStatusTone
> = {
  idle: 'neutral',
  not_started: 'neutral',
  running: 'primary',
  succeeded: 'success',
  interrupted: 'warning',
};

export function getSessionRequestStatusPresentation(
  status: SessionRequestStatus | null | undefined,
): {
  label: string;
  tone: SessionRequestStatusTone;
} | null {
  if (!status) return null;
  return {
    label: SESSION_REQUEST_STATUS_LABELS[status.state],
    tone: SESSION_REQUEST_STATUS_TONES[status.state],
  };
}
