import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import type { ConnectionRecord, Transport } from '@crystal-lattice/frontend-sdk';

import ConnectedRoot from '../src/ConnectedRoot';
import { PinnedActionsProvider } from '../src/PinnedActionsContext';
import { ThemeProvider, lightTheme } from '../src/theme';

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

function renderRoot(onSelectConnectionRecord = jest.fn()) {
  const screen = render(
    <SafeAreaProvider>
      <ThemeProvider theme={lightTheme}>
        <PinnedActionsProvider>
          <ConnectedRoot
            backend={null}
            transport={transport}
            onDisconnect={() => {}}
            connections={records}
            connectionsLoading={false}
            onSelectConnectionRecord={onSelectConnectionRecord}
            onNewConnectionRequested={() => {}}
            renderConnectionWizard={() => null}
            onDeleteConnectionRecord={() => {}}
            activeConnectionId="active"
            sessionsCache={{
              active: {
                connectionId: 'active',
                sessions: [],
                lastLoadedAt: 1,
              },
            }}
            onUpdateSessionsCache={() => {}}
            messagesCache={{}}
            onUpdateMessagesCache={() => {}}
            onSaveMessagesComposeText={() => {}}
            onSaveMessagesScrollAnchor={() => {}}
            onSaveMessagesHistoryRange={() => {}}
            debugTimeline={[]}
            onAppendDebugTimelineEntry={() => {}}
          />
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

test('an open card navigates to Sessions without reconnecting', () => {
  const { screen, onSelectConnectionRecord } = renderRoot();

  fireEvent.press(screen.getByTestId('connection-card-active'));

  expect(isHidden(screen.getByTestId('sessions-tab-content').props.style)).toBe(false);
  expect(screen.getByTestId('sessions-screen-title').props.children).toBe(
    'Active server',
  );
  expect(onSelectConnectionRecord).not.toHaveBeenCalled();
});

test('a closed card navigates before its connection attempt resolves', () => {
  const neverResolves = jest.fn(() => new Promise<void>(() => {}));
  const { screen } = renderRoot(neverResolves);

  fireEvent.press(screen.getByTestId('connection-card-closed'));

  expect(isHidden(screen.getByTestId('sessions-tab-content').props.style)).toBe(false);
  expect(neverResolves).toHaveBeenCalledWith(records[1]);
});

test('the Open action starts the connection and remains on Connections', async () => {
  const openConnection = jest.fn();
  const { screen } = renderRoot(openConnection);
  await waitFor(() => expect(screen.getByLabelText('Open')).toBeTruthy());

  fireEvent.press(screen.getByLabelText('Open'));

  expect(openConnection).toHaveBeenCalledWith(records[1]);
  expect(isHidden(screen.getByTestId('connections-tab-content').props.style)).toBe(false);
});