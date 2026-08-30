import React from 'react';
import { StyleSheet } from 'react-native';
import {
  fireEvent,
  render,
  waitFor,
} from '@testing-library/react-native';
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

    const firstTile = screen.getByTestId('home-watchlist-tile-one-shared');
    const secondTile = screen.getByTestId('home-watchlist-tile-two-shared');
    expect(StyleSheet.flatten(firstTile.props.style).width).toBe('48.5%');
    expect(StyleSheet.flatten(secondTile.props.style).width).toBe('48.5%');

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
});