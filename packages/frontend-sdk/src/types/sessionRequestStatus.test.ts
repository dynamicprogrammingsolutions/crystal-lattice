import { describe, expect, it } from 'vitest';

import { normalizeSessionRequestStatusSnapshot } from './sessionRequestStatus';

describe('normalizeSessionRequestStatusSnapshot', () => {
  it('keeps supported safe projections and drops malformed or unknown entries', () => {
    expect(
      normalizeSessionRequestStatusSnapshot({
        version: 99,
        authority: 'persisted',
        generated_at: '2026-08-29T12:00:00Z',
        statuses: [
          {
            session_id: 'one',
            request_id: 'request-1',
            state: 'running',
            basis: 'active_request',
            session_modified: 10,
            content: 'must not be copied',
          },
          {
            session_id: 'future',
            request_id: null,
            state: 'paused',
            basis: 'session_tail',
            session_modified: 11,
          },
          { session_id: '', state: 'idle' },
        ],
        missing_session_ids: ['missing', '', 1],
      }),
    ).toEqual({
      version: 1,
      authority: 'persisted',
      generated_at: '2026-08-29T12:00:00Z',
      statuses: [
        {
          session_id: 'one',
          request_id: 'request-1',
          state: 'running',
          basis: 'active_request',
          session_modified: 10,
        },
      ],
      missing_session_ids: ['missing'],
    });
  });

  it('normalizes invalid envelopes to an empty transient snapshot', () => {
    expect(normalizeSessionRequestStatusSnapshot(null)).toEqual({
      version: 1,
      authority: 'derived_transient',
      statuses: [],
      missing_session_ids: [],
    });
  });
});