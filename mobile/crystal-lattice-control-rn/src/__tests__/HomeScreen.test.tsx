import React from 'react';
import { StyleSheet } from 'react-native';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

import HomeScreen from '../HomeScreen';
import { HomeWorkspaceProvider } from '../HomeWorkspaceContext';
import { PinnedActionsProvider } from '../PinnedActionsContext';
import { ThemeProvider, lightTheme } from '../theme';

function createStore(): KeyValueStore {
  const values = new Map<string, string>();
  return {
    get: async (key) => values.get(key) ?? null,
    set: async (key, value) => {
      values.set(key, value);
    },
    delete: async (key) => {
      values.delete(key);
    },
  };
}

const connections = [
  {
    id: 'one',
    kind: 'manual' as const,
    name: 'Office',
    host: 'one.test',
    port: 8000,
    lastUsedAt: 1,
  },
  {
    id: 'two',
    kind: 'manual' as const,
    name: 'Laptop',
    host: 'two.test',
    port: 8000,
    lastUsedAt: 2,
  },
];

function renderHome() {
  const now = Date.now() / 1000;
  const onOpenGlobalSettings = jest.fn();
  const onSelectSession = jest.fn();
  const screen = render(
    <ThemeProvider theme={lightTheme}>
      <PinnedActionsProvider>
        <HomeWorkspaceProvider store={createStore()}>
          <HomeScreen
            connections={connections}
            sessionsCache={{
              one: {
                connectionId: 'one',
                lastLoadedAt: Date.now(),
                sessions: [
                  {
                    session_id: 'shared',
                    modified: now - 20,
                    preview: 'Office shared session',
                  },
                  {
                    session_id: 'office-next',
                    modified: now - 30,
                    preview: 'Office next session',
                  },
                ],
              },
              two: {
                connectionId: 'two',
                lastLoadedAt: Date.now(),
                sessions: [
                  {
                    session_id: 'shared',
                    modified: now - 10,
                    preview: 'Laptop shared session',
                  },
                  {
                    session_id: 'laptop-next',
                    modified: now - 40,
                    preview: 'Laptop next session',
                  },
                ],
              },
            }}
            statusesByConnection={{
              one: {
                shared: {
                  session_id: 'shared',
                  request_id: null,
                  state: 'succeeded',
                  basis: 'session_tail',
                  session_modified: now - 20,
                },
              },
            }}
            hasActiveBackend
            isActive
            onOpenGlobalSettings={onOpenGlobalSettings}
            onNewConnection={() => {}}
            onNewSession={() => {}}
            onSelectSession={onSelectSession}
          />
        </HomeWorkspaceProvider>
      </PinnedActionsProvider>
    </ThemeProvider>,
  );
  return { ...screen, onOpenGlobalSettings, onSelectSession };
}

function panEvent(options: {
  previousX: number;
  previousY: number;
  currentX: number;
  currentY: number;
  timestamp: number;
}) {
  return {
    nativeEvent: {
      pageX: options.currentX,
      pageY: options.currentY,
      touches: [{ pageX: options.currentX, pageY: options.currentY }],
    },
    touchHistory: {
      touchBank: [
        {
          touchActive: true,
          startPageX: options.previousX,
          startPageY: options.previousY,
          startTimeStamp: 1,
          currentPageX: options.currentX,
          currentPageY: options.currentY,
          currentTimeStamp: options.timestamp,
          previousPageX: options.previousX,
          previousPageY: options.previousY,
          previousTimeStamp: options.timestamp - 1,
        },
      ],
      numberActiveTouches: 1,
      indexOfSingleActiveTouch: 0,
      mostRecentTimeStamp: options.timestamp,
    },
  };
}

function directWatchlistChildIDs(
  screen: ReturnType<typeof renderHome>,
): string[] {
  return screen
    .getByTestId('home-watchlist-grid')
    .findAll(
      (node) =>
        typeof node.props.testID === 'string' &&
        (node.props.testID.startsWith('home-watchlist-tile-') ||
          node.props.testID.startsWith('home-watchlist-placeholder-')),
    )
    .map((node) => node.props.testID)
    .filter((testID, index, values) => values.indexOf(testID) === index);
}

describe('HomeScreen', () => {
  it('renders a distinct Recent Sessions timeline and Settings-only Home menu', async () => {
    const screen = renderHome();
    await waitFor(() =>
      expect(screen.getByTestId('home-recent-timeline')).toBeTruthy(),
    );

    fireEvent.press(screen.getByTestId('home-menu'));
    fireEvent.press(screen.getByTestId('home-menu-global-settings'));

    expect(screen.onOpenGlobalSettings).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Recent Sessions')).toBeTruthy();
    expect(screen.getByText('Last 3 days')).toBeTruthy();
  });

  it('uses exactly two reorderable Watchlist columns and shares notes by session ID', async () => {
    const screen = renderHome();
    await waitFor(() =>
      expect(screen.getByTestId('home-recent-one-shared')).toBeTruthy(),
    );

    fireEvent.press(screen.getByTestId('home-recent-watch-one-shared'));
    fireEvent.press(screen.getByTestId('home-recent-watch-two-shared'));
    await waitFor(() =>
      expect(screen.getByTestId('home-watchlist-tile-one-shared')).toBeTruthy(),
    );
    expect(screen.getByTestId('home-recent-one-shared')).toBeTruthy();
    expect(
      screen.getByTestId('home-recent-watch-one-shared').props
        .accessibilityState,
    ).toEqual({ disabled: true });

    const firstTile = screen.getByTestId('home-watchlist-tile-one-shared');
    const secondTile = screen.getByTestId('home-watchlist-tile-two-shared');
    expect(StyleSheet.flatten(firstTile.props.style).width).toBe('48.5%');
    expect(StyleSheet.flatten(secondTile.props.style).width).toBe('48.5%');
    expect(
      screen
        .getByTestId('home-watchlist-remove-one-shared')
        .findAllByProps({ name: 'x' }),
    ).toHaveLength(1);

    fireEvent.press(screen.getByTestId('home-watchlist-note-one-shared'));
    fireEvent.changeText(
      screen.getByTestId('session-note-input'),
      'Shared permanent note',
    );
    fireEvent.press(screen.getByTestId('session-note-save'));

    await waitFor(() => {
      expect(
        screen.getByTestId('home-watchlist-note-preview-one-shared').props
          .children,
      ).toBe('Shared permanent note');
      expect(
        screen.getByTestId('home-watchlist-note-preview-two-shared').props
          .children,
      ).toBe('Shared permanent note');
    });

    fireEvent(
      screen.getByTestId('home-watchlist-drag-one-shared'),
      'accessibilityAction',
      { nativeEvent: { actionName: 'increment' } },
    );
    const tileOrderWithDuplicates = screen
      .getByTestId('home-watchlist-grid')
      .findAll(
        (node) =>
          typeof node.props.testID === 'string' &&
          node.props.testID.startsWith('home-watchlist-tile-'),
      )
      .map((node) => node.props.testID);
    const tileOrder = tileOrderWithDuplicates.filter(
      (testID, index) => tileOrderWithDuplicates.indexOf(testID) === index,
    );
    expect(tileOrder).toEqual([
      'home-watchlist-tile-two-shared',
      'home-watchlist-tile-one-shared',
    ]);
  });

  it('captures vertical handle drags and previews the measured target slot', async () => {
    const screen = renderHome();
    await waitFor(() =>
      expect(screen.getByTestId('home-recent-one-shared')).toBeTruthy(),
    );
    [
      'home-recent-watch-one-shared',
      'home-recent-watch-two-shared',
      'home-recent-watch-one-office-next',
      'home-recent-watch-two-laptop-next',
    ].forEach((testID) => fireEvent.press(screen.getByTestId(testID)));

    const layouts = [
      {
        testID: 'home-watchlist-tile-one-shared',
        layout: { x: 0, y: 0, width: 100, height: 120 },
      },
      {
        testID: 'home-watchlist-tile-two-shared',
        layout: { x: 112, y: 0, width: 100, height: 150 },
      },
      {
        testID: 'home-watchlist-tile-one-office-next',
        layout: { x: 0, y: 162, width: 100, height: 180 },
      },
      {
        testID: 'home-watchlist-tile-two-laptop-next',
        layout: { x: 112, y: 162, width: 100, height: 100 },
      },
    ];
    layouts.forEach(({ testID, layout }) => {
      fireEvent(screen.getByTestId(testID), 'layout', {
        nativeEvent: { layout },
      });
    });

    const grantEvent = panEvent({
      previousX: 50,
      previousY: 60,
      currentX: 50,
      currentY: 60,
      timestamp: 1,
    });
    let handle = screen.getByTestId('home-watchlist-drag-one-shared');
    expect(handle.props.onStartShouldSetResponderCapture(grantEvent)).toBe(
      true,
    );
    fireEvent(handle, 'responderGrant', grantEvent);

    expect(screen.getByTestId('home-scroll').props.scrollEnabled).toBe(false);
    expect(directWatchlistChildIDs(screen).slice(0, 4)).toEqual([
      'home-watchlist-tile-one-shared',
      'home-watchlist-placeholder-one::shared',
      'home-watchlist-tile-two-shared',
      'home-watchlist-tile-one-office-next',
    ]);

    const moveEvent = panEvent({
      previousX: 50,
      previousY: 60,
      currentX: 53,
      currentY: 250,
      timestamp: 2,
    });
    handle = screen.getByTestId('home-watchlist-drag-one-shared');
    fireEvent(handle, 'responderMove', moveEvent);

    expect(directWatchlistChildIDs(screen).slice(0, 4)).toEqual([
      'home-watchlist-tile-one-shared',
      'home-watchlist-tile-two-shared',
      'home-watchlist-tile-one-office-next',
      'home-watchlist-placeholder-one::shared',
    ]);

    handle = screen.getByTestId('home-watchlist-drag-one-shared');
    fireEvent(handle, 'responderRelease', moveEvent);
    expect(screen.getByTestId('home-scroll').props.scrollEnabled).toBe(true);
    expect(directWatchlistChildIDs(screen).slice(0, 4)).toEqual([
      'home-watchlist-tile-two-shared',
      'home-watchlist-tile-one-office-next',
      'home-watchlist-tile-one-shared',
      'home-watchlist-tile-two-laptop-next',
    ]);
  });
});
