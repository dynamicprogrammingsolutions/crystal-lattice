import type { ConnectionRecord } from './types';
import type { SessionRequestStatusSnapshot } from '../types/sessionRequestStatus';

export type ConnectionSessionStatusResult =
  | {
      status: 'ok';
      snapshot: SessionRequestStatusSnapshot;
    }
  | {
      status: 'unsupported';
    }
  | {
      status: 'unavailable';
      message?: string;
    }
  | {
      status: 'repair_required';
    }
  | {
      status: 'unauthorized';
    };

export interface ConnectionSessionStatusReader {
  getSessionRequestStatuses(
    record: ConnectionRecord,
    sessionIds: readonly string[],
    options?: { signal?: AbortSignal },
  ): Promise<ConnectionSessionStatusResult>;
}