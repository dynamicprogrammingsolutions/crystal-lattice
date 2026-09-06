import { describe, expect, it } from 'vitest';

import type {
  ConnectionRecord,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

import {
  deriveHomeSessionCollections,
  normalizeSessionNotes,
  normalizeWatchlist,
  watchedSessionKey,
} from './homeWorkspace';

const connection = {
  id: 'connection',
  name: 'Local',
  kind: 'manual',
  host: '127.0.0.1',
  port: 9000,
} as ConnectionRecord;

function session(id: string, modified: number): SessionSummary {
  return {
    session_id: id,
    modified,
    preview: id,
  } as SessionSummary;
}

describe('portable Home workspace model', () => {
  it('normalizes composite watch identities and session-ID notes', () => {
    expect(
      normalizeWatchlist([
        { connectionId: 'connection', sessionId: 'session' },
        { connectionId: 'connection', sessionId: 'session' },
        { connectionId: '', sessionId: 'ignored' },
      ]),
    ).toEqual([{ connectionId: 'connection', sessionId: 'session' }]);
    expect(
      normalizeSessionNotes({ shared: 'note', empty: ' ', invalid: 3 }),
    ).toEqual({ shared: 'note' });
    expect(watchedSessionKey('a/b', 'c d')).toBe('a%2Fb::c%20d');
  });

  it('keeps Watchlist order while Recent includes watched sessions in range', () => {
    const nowMs = 10 * 24 * 60 * 60 * 1000;
    const newer = session('newer', nowMs / 1000 - 10);
    const older = session('older', nowMs / 1000 - 20);
    const outside = session('outside', nowMs / 1000 - 8 * 24 * 60 * 60);
    const collections = deriveHomeSessionCollections({
      connections: [connection],
      sessionsCache: {
        connection: { sessions: [older, outside, newer] },
      },
      watchlist: [
        { connectionId: 'connection', sessionId: 'older' },
        { connectionId: 'connection', sessionId: 'newer' },
      ],
      notes: { older: 'shared note' },
      recentSessionsWindow: '1w',
      nowMs,
    });

    expect(collections.watchlist.map(item => item.sessionId)).toEqual([
      'older',
      'newer',
    ]);
    expect(collections.watchlist[0].note).toBe('shared note');
    expect(collections.recent.map(item => item.sessionId)).toEqual([
      'newer',
      'older',
    ]);
  });
});
