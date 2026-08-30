import {
  deriveHomeSessionCollections,
  moveWatchedSession,
  normalizeSessionNotes,
  normalizeWatchlist,
} from '../homeWorkspaceState';

describe('home workspace state', () => {
  const connections = [
    {
      id: 'one',
      kind: 'manual' as const,
      name: 'One',
      host: 'one.test',
      port: 8000,
      lastUsedAt: 1,
    },
    {
      id: 'two',
      kind: 'manual' as const,
      name: 'Two',
      host: 'two.test',
      port: 8000,
      lastUsedAt: 2,
    },
  ];

  it('normalizes composite Watchlist order and session-id notes separately', () => {
    expect(
      normalizeWatchlist([
        { connectionId: 'one', sessionId: 'shared' },
        { connectionId: 'two', sessionId: 'shared' },
        { connectionId: 'one', sessionId: 'shared' },
      ]),
    ).toEqual([
      { connectionId: 'one', sessionId: 'shared' },
      { connectionId: 'two', sessionId: 'shared' },
    ]);
    expect(normalizeSessionNotes({ shared: 'same note', empty: ' ' })).toEqual({
      shared: 'same note',
    });
  });

  it('derives ordered watched tiles and keeps watched sessions in strict recents', () => {
    const nowMs = Date.UTC(2026, 7, 29, 12);
    const recent = nowMs / 1000 - 60;
    const old = nowMs / 1000 - 2 * 24 * 60 * 60;
    const result = deriveHomeSessionCollections({
      connections,
      sessionsCache: {
        one: {
          sessions: [
            { session_id: 'shared', modified: old, preview: 'old watched' },
            { session_id: 'recent-one', modified: recent, preview: 'recent one' },
          ],
        },
        two: {
          sessions: [
            { session_id: 'shared', modified: recent - 1, preview: 'shared two' },
            { session_id: 'recent-two', modified: recent + 1, preview: 'recent two' },
          ],
        },
      },
      watchlist: [{ connectionId: 'two', sessionId: 'shared' }],
      notes: { shared: 'same note on both connections' },
      recentSessionsWindow: '24h',
      nowMs,
    });

    expect(result.watchlist.map((item) => item.key)).toEqual(['two::shared']);
    expect(result.watchlist[0].note).toBe('same note on both connections');
    expect(result.recent.map((item) => item.sessionId)).toEqual([
      'recent-two',
      'recent-one',
      'shared',
    ]);
    expect(result.recent[2].note).toBe('same note on both connections');
  });

  it('moves Watchlist entries deterministically', () => {
    expect(
      moveWatchedSession(
        [
          { connectionId: 'one', sessionId: 'a' },
          { connectionId: 'one', sessionId: 'b' },
          { connectionId: 'one', sessionId: 'c' },
        ],
        2,
        0,
      ).map((item) => item.sessionId),
    ).toEqual(['c', 'a', 'b']);
  });
});
