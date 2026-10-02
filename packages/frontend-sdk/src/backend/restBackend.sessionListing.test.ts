import { describe, expect, it, vi } from 'vitest';

import type { Transport } from '../transport/transport';
import { RestAgentBackend } from './restBackend';

const SUMMARY = {
  session_id: 'session/one',
  modified: 42,
  preview: 'preview',
  metadata: { status: 'done' },
  presentation: {
    title: 'Server title',
    subtitle: 'Server subtitle',
    meta: 'Server meta',
  },
  contributed_rank: 3,
};

describe('RestAgentBackend session listing', () => {
  it('uses the unfiltered sessions endpoint when no limit is requested', async () => {
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: { sessions: [SUMMARY] },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(backend.listSessions()).resolves.toEqual([SUMMARY]);
    expect(transport.request).toHaveBeenCalledWith({
      method: 'GET',
      path: '/sessions',
    });
  });

  it('preserves ordered application summaries and serializes limit', async () => {
    const second = {
      ...SUMMARY,
      session_id: 'session-two',
      presentation: {
        ...SUMMARY.presentation,
        title: 'Second title',
      },
    };
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: { sessions: [SUMMARY, second] },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(backend.listSessions({ limit: 2 })).resolves.toEqual([
      SUMMARY,
      second,
    ]);
    expect(transport.request).toHaveBeenCalledWith({
      method: 'GET',
      path: '/sessions?limit=2',
    });
  });

  it('encodes plugin filters and ordered JSONPath projection separately', async () => {
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: { sessions: [{ session_id: 'session/one' }] },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(
      backend.querySessions({
        filters: {
          modified_after: '2026-09-01T00:00:00Z',
          status: ['todo', 'blocked'],
        },
        applyFilterDefaults: true,
        include: ['$.sessions[*].session_id'],
        exclude: ['$.sessions[?(@.metadata.archived == true)]'],
      }),
    ).resolves.toEqual({
      sessions: [{ session_id: 'session/one' }],
    });
    expect(transport.request).toHaveBeenCalledWith({
      method: 'GET',
      path:
        '/sessions?apply_filter_defaults=true' +
        '&filter=modified_after%3D2026-09-01T00%3A00%3A00Z' +
        '&filter=status%3Dtodo%2Cblocked' +
        '&include=%24.sessions%5B*%5D.session_id' +
        '&exclude=%24.sessions%5B%3F(%40.metadata.archived%20%3D%3D%20true)%5D',
    });
  });

  it('accepts wrapped and unwrapped exact summaries', async () => {
    const transport = {
      request: vi
        .fn()
        .mockResolvedValueOnce({
          status: 200,
          data: { session: SUMMARY },
        })
        .mockResolvedValueOnce({
          status: 200,
          data: SUMMARY,
        }),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(backend.getSessionSummary('session/one')).resolves.toEqual(
      SUMMARY,
    );
    await expect(backend.getSessionSummary('session/one')).resolves.toEqual(
      SUMMARY,
    );
    expect(transport.request).toHaveBeenNthCalledWith(1, {
      method: 'GET',
      path: '/sessions/session%2Fone/summary',
    });
  });

  it('rejects an invalid exact-summary response', async () => {
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: { session: { preview: 'missing id' } },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(backend.getSessionSummary('missing')).rejects.toThrow(
      'Server did not return a session summary',
    );
  });

  it('queries request status with explicit session IDs', async () => {
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: {
          version: 1,
          authority: 'derived_transient',
          statuses: [
            {
              session_id: 'one',
              request_id: null,
              state: 'succeeded',
              basis: 'session_tail',
              session_modified: 10,
            },
          ],
          missing_session_ids: ['missing'],
        },
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(
      backend.getSessionRequestStatuses(['one', 'missing']),
    ).resolves.toMatchObject({
      statuses: [{ session_id: 'one', state: 'succeeded' }],
      missing_session_ids: ['missing'],
    });
    expect(transport.request).toHaveBeenCalledWith({
      method: 'POST',
      path: '/sessions/request-statuses',
      body: { session_ids: ['one', 'missing'] },
    });
  });
});
