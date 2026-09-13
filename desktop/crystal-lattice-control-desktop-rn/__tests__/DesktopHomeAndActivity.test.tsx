import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';

import type {
  ConnectionRecord,
  SessionRequestStatus,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { deriveHomeSessionCollections } from '@crystal-lattice/frontend-rn-components';

import { DesktopActivityRail } from '../src/layout/DesktopActivityRail';
import { DesktopHomeView } from '../src/home/DesktopHomeView';

const connection = {
  id: 'connection',
  name: 'Local server',
  kind: 'manual',
  host: '127.0.0.1',
  port: 9000,
} as ConnectionRecord;
const summary = {
  session_id: 'session',
  modified: Date.now() / 1000,
  preview: 'Investigate issue',
} as SessionSummary;
const status = {
  session_id: 'session',
  request_id: null,
  state: 'running',
  basis: 'active_request',
  session_modified: summary.modified,
} as SessionRequestStatus;

describe('desktop Home and activity rail', () => {
  it('renders exactly three activity controls with independent Connections state', () => {
    const onToggleConnections = jest.fn();
    const onSelectLowerPanel = jest.fn();
    render(
      <DesktopActivityRail
        connectionsVisible
        lowerPanel="sessions"
        onToggleConnections={onToggleConnections}
        onSelectLowerPanel={onSelectLowerPanel}
      />,
    );
    expect(screen.getByTestId('desktop-activity-connections')).toBeTruthy();
    expect(screen.getByTestId('desktop-activity-sessions')).toBeTruthy();
    expect(screen.getByTestId('desktop-activity-history')).toBeTruthy();
    fireEvent.press(screen.getByTestId('desktop-activity-connections'));
    fireEvent.press(screen.getByTestId('desktop-activity-history'));
    expect(onToggleConnections).toHaveBeenCalledTimes(1);
    expect(onSelectLowerPanel).toHaveBeenCalledWith('history');
  });

  it('keeps single click light and exposes the complementary Open button', () => {
    const collections = deriveHomeSessionCollections({
      connections: [connection],
      sessionsCache: {
        connection: { sessions: [summary] },
      },
      watchlist: [{ connectionId: 'connection', sessionId: 'session' }],
      notes: { session: 'Remember this' },
      recentSessionsWindow: '3d',
    });
    const onOpenSession = jest.fn();
    render(
      <DesktopHomeView
        collections={collections}
        statuses={{ connection: { session: status } }}
        doubleClickAction="preview"
        onOpenSession={onOpenSession}
        onToggleWatch={() => {}}
        onEditNote={() => {}}
        onMoveWatchlistItem={() => {}}
      />,
    );
    const tile = screen.getByTestId('desktop-tile-session-connection-session');
    fireEvent.press(tile);
    expect(onOpenSession).not.toHaveBeenCalled();
    fireEvent.press(
      screen.getAllByTestId('desktop-session-open-connection-session')[0],
    );
    expect(onOpenSession).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 'session' }),
      'open',
    );
    expect(screen.getAllByText('In progress').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Remember this').length).toBeGreaterThan(0);
  });

  it('offers Open instead of Preview when the session already has a tab', () => {
    const collections = deriveHomeSessionCollections({
      connections: [connection],
      sessionsCache: {
        connection: { sessions: [summary] },
      },
      watchlist: [],
      notes: {},
      recentSessionsWindow: '3d',
    });
    const onOpenSession = jest.fn();
    render(
      <DesktopHomeView
        collections={collections}
        statuses={{}}
        doubleClickAction="open"
        getSessionTabKind={() => 'preview'}
        onOpenSession={onOpenSession}
        onToggleWatch={() => {}}
        onEditNote={() => {}}
        onMoveWatchlistItem={() => {}}
      />,
    );

    expect(
      screen.getByTestId('desktop-session-open-connection-session'),
    ).toBeTruthy();
    expect(
      screen.queryByTestId('desktop-session-preview-connection-session'),
    ).toBeNull();
    fireEvent.press(
      screen.getByTestId('desktop-session-open-connection-session'),
    );
    expect(onOpenSession).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 'session' }),
      'open',
    );
  });
});
