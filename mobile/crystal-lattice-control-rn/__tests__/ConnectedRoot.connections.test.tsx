import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import type { ConnectionRecord, Transport } from '@crystal-lattice/frontend-sdk';

import ConnectedRoot from '../src/ConnectedRoot';
import { PinnedActionsProvider } from '../src/PinnedActionsContext';
import { ThemeProvider, lightTheme } from '../src/theme';
import { HomeWorkspaceProvider } from '../src/HomeWorkspaceContext';
import type { SessionsCache } from '../App';

const records: ConnectionRecord[] = [
  {
    id: 'active',
    kind: 'manual',
    name: 'Active server',
    host: '127.0.0.1',
    port: 8080,
    lastUsedAt: 2,
  },
  {
    id: 'closed',
    kind: 'manual',
    name: 'Closed server',
    host: '127.0.0.1',
    port: 8081,
    lastUsedAt: 1,
  },
];

const transport = {
  request: jest.fn(),
} as unknown as Transport;

function renderRoot(
  onSelectConnectionRecord = jest.fn(),
  sessionsCache: SessionsCache = {
    active: {
      connectionId: 'active',
      sessions: [],
      lastLoadedAt: 1,
    },
  },
) {
  const screen = render(
    <SafeAreaProvider>
      <ThemeProvider theme={lightTheme}>
        <PinnedActionsProvider>
        <HomeWorkspaceProvider>
          <ConnectedRoot
            backend={null}
            transport={transport}
            onDisconnect={() => {}}
            connections={records}
            connectionsLoading={false}
            onSelectConnectionRecord={onSelectConnectionRecord}
            onNewConnectionRequested={() => {}}
            renderConnectionWizard={() => null}
            onCloseConnectionWizard={() => {}}
            onDeleteConnectionRecord={() => {}}
            activeConnectionId="active"
            sessionsCache={sessionsCache}
            onUpdateSessionsCache={() => {}}
            messagesCache={{}}
            onUpdateMessagesCache={() => {}}
            onSaveMessagesComposeText={() => {}}
            onSaveMessagesScrollAnchor={() => {}}
            onSaveMessagesHistoryRange={() => {}}
            debugTimeline={[]}
            onAppendDebugTimelineEntry={() => {}}
          />
        </HomeWorkspaceProvider>
        </PinnedActionsProvider>
      </ThemeProvider>
    </SafeAreaProvider>,
  );
  return { screen, onSelectConnectionRecord };
}

function isHidden(style: unknown): boolean {
  return (StyleSheet.flatten(style) as { display?: string } | undefined)?.display === 'none';
}

beforeEach(async () => {
  await AsyncStorage.clear();
});

test('an open card navigates to Sessions without reconnecting', async () => {
  const { screen, onSelectConnectionRecord } = renderRoot();

  expect(screen.queryByTestId('connections-tab')).toBeNull();
  await screen.findByTestId('connection-card-active');
  fireEvent.press(screen.getByTestId('connection-card-active'));

  expect(isHidden(screen.getByTestId('sessions-tab-content').props.style)).toBe(false);
  expect(screen.getByTestId('sessions-screen-title').props.children).toBe(
    'Active server',
  );
  expect(onSelectConnectionRecord).not.toHaveBeenCalled();
});

test('a closed card navigates before its connection attempt resolves', async () => {
  const neverResolves = jest.fn(() => new Promise<void>(() => {}));
  const { screen } = renderRoot(neverResolves);
  await screen.findByTestId('connection-card-closed');

  fireEvent.press(screen.getByTestId('connection-card-closed'));

  expect(isHidden(screen.getByTestId('sessions-tab-content').props.style)).toBe(false);
  expect(neverResolves).toHaveBeenCalledWith(records[1]);
});

test('the Open action starts the connection and remains on Home', async () => {
  const openConnection = jest.fn();
  const { screen } = renderRoot(openConnection);
  await waitFor(() => expect(screen.getByLabelText('Open')).toBeTruthy());

  fireEvent.press(screen.getByLabelText('Open'));

  expect(openConnection).toHaveBeenCalledWith(records[1]);
  expect(isHidden(screen.getByTestId('home-tab-content').props.style)).toBe(false);
});

test('a Home session waits for its closed connection before navigating to Messages', async () => {
  let resolveOpen!: (value: boolean) => void;
  const openPromise = new Promise<boolean>((resolve) => {
    resolveOpen = resolve;
  });
  const openConnection = jest.fn(() => openPromise);
  const { screen } = renderRoot(openConnection, {
    closed: {
      connectionId: 'closed',
      sessions: [
        {
          session_id: 'home-session',
          modified: Date.now() / 1000,
          preview: 'Home session',
        },
      ],
      lastLoadedAt: Date.now(),
    },
  });
  await waitFor(() =>
    expect(screen.getByTestId('home-recent-open-closed-home-session')).toBeTruthy(),
  );

  fireEvent.press(screen.getByTestId('home-recent-open-closed-home-session'));

  expect(openConnection).toHaveBeenCalledWith(records[1]);
  expect(screen.queryByTestId('messages-tab-content')).toBeNull();

  resolveOpen(true);
  await waitFor(() =>
    expect(isHidden(screen.getByTestId('messages-tab-content').props.style)).toBe(false),
  );
});

test('a card plus waits for connection opening before showing the agent picker', async () => {
  let resolveOpen!: (value: boolean) => void;
  const openConnection = jest.fn(() => new Promise<boolean>((resolve) => {
    resolveOpen = resolve;
  }));
  const { screen } = renderRoot(openConnection);
  await screen.findByTestId('connection-new-session-closed');
  fireEvent.press(screen.getByTestId('connection-new-session-closed'));
  expect(openConnection).toHaveBeenCalledWith(records[1]);
  expect(isHidden(screen.getByTestId('home-tab-content').props.style)).toBe(false);
  resolveOpen(true);
  await screen.findByText('No agents are available from the server.');
  expect(isHidden(screen.getByTestId('sessions-tab-content').props.style)).toBe(false);
});

test('a failed connection does not show the New session picker', async () => {
  const openConnection = jest.fn(async () => false);
  const { screen } = renderRoot(openConnection);
  await screen.findByTestId('connection-new-session-closed');
  fireEvent.press(screen.getByTestId('connection-new-session-closed'));
  await waitFor(() => expect(openConnection).toHaveBeenCalledWith(records[1]));
  expect(isHidden(screen.getByTestId('home-tab-content').props.style)).toBe(false);
  expect(screen.queryByText('Choose an agent to start a new session.')).toBeNull();
});