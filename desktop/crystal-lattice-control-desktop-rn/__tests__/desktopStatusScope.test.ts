import type {
  ConnectionRecord,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import type {
  HomeSessionCollections,
  HomeSessionItem,
} from '@crystal-lattice/frontend-rn-components';

import { deriveDesktopStatusSessionIds } from '../src/status/desktopStatusScope';

const connection = {
  id: 'connection',
  name: 'Connection',
  kind: 'manual',
  host: '127.0.0.1',
  port: 9000,
} as ConnectionRecord;

function item(sessionId: string): HomeSessionItem {
  return {
    key: `connection::${sessionId}`,
    connectionId: connection.id,
    sessionId,
    connection,
    summary: {
      session_id: sessionId,
      modified: 1,
    } as SessionSummary,
    note: null,
  };
}

const collections: HomeSessionCollections = {
  watchlist: [item('watched')],
  recent: [item('recent')],
};

const tab = {
  tabId: 'connection:tab',
  connectionId: connection.id,
  sessionId: 'tab',
  title: 'Tab',
};

describe('desktop request-status consumer scope', () => {
  it('keeps tabs registered while Home adds only Home consumers', () => {
    expect(
      deriveDesktopStatusSessionIds({
        tabs: [tab],
        homeActive: true,
        homeCollections: collections,
        lowerPanel: 'sessions',
        focusedConnectionId: 'connection',
        visibleSessions: {
          connectionId: 'connection',
          sessionIds: ['visible'],
        },
      }),
    ).toEqual({
      connection: ['tab', 'watched', 'recent', 'visible'],
    });
  });

  it('registers the visible Sessions window instead of every cached session', () => {
    const cachedButNotVisible = Array.from(
      { length: 500 },
      (_value, index) => `cached-${index}`,
    );
    const result = deriveDesktopStatusSessionIds({
      tabs: [tab],
      homeActive: false,
      homeCollections: collections,
      lowerPanel: 'sessions',
      focusedConnectionId: 'connection',
      visibleSessions: {
        connectionId: 'connection',
        sessionIds: ['visible'],
      },
    });

    expect(result).toEqual({ connection: ['tab', 'visible'] });
    expect(
      cachedButNotVisible.some(sessionId =>
        result.connection.includes(sessionId),
      ),
    ).toBe(false);
  });

  it('registers recent items for History without another connection focus', () => {
    expect(
      deriveDesktopStatusSessionIds({
        tabs: [tab],
        homeActive: false,
        homeCollections: collections,
        lowerPanel: 'history',
        focusedConnectionId: null,
        visibleSessions: {
          connectionId: null,
          sessionIds: [],
        },
      }),
    ).toEqual({ connection: ['tab', 'recent'] });
  });
});
