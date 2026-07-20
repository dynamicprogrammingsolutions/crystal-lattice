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
});
