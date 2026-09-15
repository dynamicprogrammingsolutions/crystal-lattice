import React from 'react';
import { StyleSheet } from 'react-native';
import { fireEvent, render, screen } from '@testing-library/react-native';

import type {
  ConnectionRecord,
  SessionRequestStatus,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import {
  ThemeProvider,
  deriveHomeSessionCollections,
} from '@crystal-lattice/frontend-rn-components';

import { DesktopActivityRail } from '../src/layout/DesktopActivityRail';
import { DesktopHomeView } from '../src/home/DesktopHomeView';
import { HistoryPanel } from '../src/panels/HistoryPanel';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

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

const longSessionId =
  'session-with-a-deliberately-long-identifier-for-truncation';

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

  it('renders complete independently truncating Home fields and one preview fallback', () => {
    const theme = buildDesktopTheme(null);
    const longConnection = {
      ...connection,
      name: 'Desktop connection with a deliberately long display name',
    };
    const now = Date.now() / 1000;
    const longSummary = {
      session_id: longSessionId,
      modified: now,
      preview: 'A distinct message preview',
      presentation: {
        title: 'A complete session title',
        subtitle: 'A complete session subtitle',
        meta: null,
      },
    } as SessionSummary;
    const fallbackSummary = {
      session_id: 'preview-only',
      modified: now - 1,
      preview: 'Preview rendered exactly once',
    } as SessionSummary;
    const collections = deriveHomeSessionCollections({
      connections: [longConnection],
      sessionsCache: {
        connection: { sessions: [longSummary, fallbackSummary] },
      },
      watchlist: [
        { connectionId: 'connection', sessionId: longSessionId },
        { connectionId: 'connection', sessionId: 'preview-only' },
      ],
      notes: { [longSessionId]: 'Local note' },
      recentSessionsWindow: '3d',
    });
    const longStatus = {
      ...status,
      session_id: longSessionId,
      session_modified: now,
    };

    render(
      <ThemeProvider theme={theme}>
        <DesktopHomeView
          collections={collections}
          statuses={{ connection: { [longSessionId]: longStatus } }}
          doubleClickAction="preview"
          onOpenSession={() => {}}
          onToggleWatch={() => {}}
          onEditNote={() => {}}
          onMoveWatchlistItem={() => {}}
        />
      </ThemeProvider>,
    );

    expect(
      screen.getByTestId(`desktop-tile-title-connection-${longSessionId}`).props
        .children,
    ).toBe('A complete session title');
    expect(
      screen.getByTestId(`desktop-tile-subtitle-connection-${longSessionId}`)
        .props.children,
    ).toBe('A complete session subtitle');
    expect(
      screen.getByTestId(`desktop-tile-session-id-connection-${longSessionId}`)
        .props.children,
    ).toBe(longSessionId);

    const historyConnection = screen.getByTestId(
      `desktop-home-recent-connection-connection-${longSessionId}`,
    );
    const historyConnectionHost = screen.getByTestId(
      `desktop-home-recent-connection-connection-${longSessionId}-native`,
    );
    const historyTime = screen.getByTestId(
      `desktop-home-recent-time-connection-${longSessionId}`,
    );
    const historyTimeHost = screen.getByTestId(
      `desktop-home-recent-time-connection-${longSessionId}-native`,
    );
    const historyActions = screen.getByTestId(
      `desktop-home-recent-actions-connection-${longSessionId}`,
    );
    expect(historyConnection.props.numberOfLines).toBe(1);
    expect(historyTime.props.numberOfLines).toBe(1);
    expect(StyleSheet.flatten(historyConnectionHost.props.style)).toMatchObject(
      {
        flex: 1,
        minWidth: 0,
      },
    );
    expect(StyleSheet.flatten(historyTimeHost.props.style).flexShrink).toBe(0);
    expect(StyleSheet.flatten(historyActions.props.style).flexShrink).toBe(0);
    expect(
      StyleSheet.flatten(
        screen.getByTestId(
          `desktop-home-recent-dot-connection-${longSessionId}`,
        ).props.style,
      ).backgroundColor,
    ).toBe(theme.textMuted);
    expect(
      StyleSheet.flatten(
        screen.getByTestId(
          `desktop-home-recent-title-connection-${longSessionId}`,
        ).props.style,
      ),
    ).toMatchObject({
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    });

    const historyRoot = screen.getByTestId(
      `desktop-history-session-connection-${longSessionId}`,
    );
    const orderedFieldIds = historyRoot
      .findAll(
        node =>
          typeof node.props.testID === 'string' &&
          [
            'title',
            'subtitle',
            'session-id',
            'status',
            'note',
            'metadata',
          ].some(field =>
            node.props.testID.startsWith(`desktop-home-recent-${field}-`),
          ),
      )
      .map(node => node.props.testID)
      .filter(testID => !testID.endsWith('-native'))
      .filter((testID, index, values) => values.indexOf(testID) === index);
    expect(orderedFieldIds).toEqual([
      `desktop-home-recent-title-connection-${longSessionId}`,
      `desktop-home-recent-subtitle-connection-${longSessionId}`,
      `desktop-home-recent-session-id-connection-${longSessionId}`,
      `desktop-home-recent-status-connection-${longSessionId}`,
      `desktop-home-recent-note-connection-${longSessionId}`,
      `desktop-home-recent-metadata-connection-${longSessionId}`,
    ]);

    expect(
      screen.getByTestId('desktop-tile-title-connection-preview-only').props
        .children,
    ).toBe('Preview rendered exactly once');
    expect(
      screen.queryByTestId('desktop-tile-subtitle-connection-preview-only'),
    ).toBeNull();
    expect(
      screen.getByTestId('desktop-home-recent-title-connection-preview-only')
        .props.children,
    ).toBe('Preview rendered exactly once');
    expect(
      screen.queryByTestId(
        'desktop-home-recent-subtitle-connection-preview-only',
      ),
    ).toBeNull();
  });

  it('uses the desktop-owned timeline hierarchy in the History panel', () => {
    const collections = deriveHomeSessionCollections({
      connections: [connection],
      sessionsCache: {
        connection: { sessions: [summary] },
      },
      watchlist: [],
      notes: {},
      recentSessionsWindow: '3d',
    });
    render(
      <HistoryPanel
        collections={collections}
        statuses={{ connection: { session: status } }}
        doubleClickAction="preview"
        onOpenSession={() => {}}
        onToggleWatch={() => {}}
        onEditNote={() => {}}
      />,
    );

    expect(
      screen.getByTestId('desktop-panel-history-title-connection-session'),
    ).toBeTruthy();
    expect(
      screen.getByTestId('desktop-panel-history-session-id-connection-session')
        .props.numberOfLines,
    ).toBe(1);
    expect(
      screen.getByTestId('desktop-panel-history-connection-connection-session')
        .props.numberOfLines,
    ).toBe(1);
    expect(
      screen.getByTestId('desktop-panel-history-time-connection-session').props
        .numberOfLines,
    ).toBe(1);
    expect(
      screen.getByTestId('desktop-panel-history-status-connection-session'),
    ).toBeTruthy();
    expect(
      screen.getByTestId('desktop-panel-history-dot-connection-session'),
    ).toBeTruthy();
    expect(
      StyleSheet.flatten(
        screen.getByTestId('desktop-history-panel').props.style,
      ),
    ).not.toHaveProperty('borderTopWidth');
  });
});
