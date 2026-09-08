import { describe, expect, it } from 'vitest';

import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import {
  getSessionRequestStatusPresentation,
  SESSION_REQUEST_STATUS_LABELS,
} from './sessionRequestStatus';

function status(state: SessionRequestStatus['state']): SessionRequestStatus {
  return {
    session_id: 'session',
    request_id: null,
    state,
    basis: 'session_tail',
    session_modified: 1,
  };
}

describe('request-status presentation', () => {
  it('maps every provisional state to stable text and tone', () => {
    expect(Object.keys(SESSION_REQUEST_STATUS_LABELS)).toEqual([
      'idle',
      'not_started',
      'running',
      'succeeded',
      'interrupted',
    ]);
    expect(getSessionRequestStatusPresentation(status('running'))).toEqual({
      label: 'In progress',
      tone: 'primary',
    });
    expect(getSessionRequestStatusPresentation(status('succeeded'))).toEqual({
      label: 'Completed',
      tone: 'success',
    });
    expect(getSessionRequestStatusPresentation(status('interrupted'))).toEqual({
      label: 'Interrupted',
      tone: 'warning',
    });
    expect(getSessionRequestStatusPresentation(null)).toBeNull();
  });
});
