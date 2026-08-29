import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import type { ConnectionRecord, Transport } from '@crystal-lattice/frontend-sdk';

import ConnectionsScreen from '../src/ConnectionsScreen';
import { PinnedActionsProvider } from '../src/PinnedActionsContext';

const records: ConnectionRecord[] = [
  {
    id: 'closed',
    kind: 'manual',
    name: 'Closed server',
    host: '127.0.0.1',
    port: 8080,
    lastUsedAt: 1,
  },
  {
    id: 'active',
    kind: 'manual',
    name: 'Active server',
    host: '127.0.0.1',
    port: 8081,
    lastUsedAt: 2,
  },
];

function renderScreen(overrides: Record<string, unknown> = {}) {
  const props = {
    connections: records,
    activeConnectionId: 'active',
    transport: {
      request: jest.fn(async () => ({ data: { message: 'healthy' } })),
    } as unknown as Transport,
    onConnectionCardPress: jest.fn(),
    onOpenConnection: jest.fn(),
    onNewConnection: jest.fn(),
    onOpenGlobalSettings: jest.fn(),
    onOpenServerSettings: jest.fn(),
    onDisconnect: jest.fn(),
    onDeleteConnection: jest.fn(),
    ...overrides,
  };
  return {
    props,
    screen: render(
      <PinnedActionsProvider>
        <ConnectionsScreen {...props} />
      </PinnedActionsProvider>,
    ),
  };
}

beforeEach(async () => {
  await AsyncStorage.clear();
});

test('renders compact cards with status and without legacy metadata', async () => {
  const { screen } = renderScreen();
  expect(screen.getByText('Connections')).toBeTruthy();
  expect(screen.queryByText('Connected to')).toBeNull();
  expect(screen.queryByText(/Last used:/)).toBeNull();
  expect(screen.getByTestId('connection-status-active').props.children).toBe('Open');
  expect(screen.getByTestId('connection-status-closed').props.children).toBe('Closed');
  await waitFor(() => expect(screen.getByLabelText('New connection')).toBeTruthy());
});

test('routes header and state-dependent card actions', async () => {
  const { screen, props } = renderScreen();
  await waitFor(() => expect(screen.getByLabelText('New connection')).toBeTruthy());
  fireEvent.press(screen.getByLabelText('New connection'));
  const settings = screen.getAllByLabelText('Settings');
  fireEvent.press(settings[0]);
  fireEvent.press(settings[1]);
  fireEvent.press(screen.getByLabelText('Open'));
  fireEvent.press(screen.getByLabelText('Disconnect'));
  fireEvent.press(screen.getByLabelText('Health check'));

  expect(props.onNewConnection).toHaveBeenCalled();
  expect(props.onOpenGlobalSettings).toHaveBeenCalled();
  expect(props.onOpenServerSettings).toHaveBeenCalled();
  expect(props.onOpenConnection).toHaveBeenCalledWith(records[0]);
  expect(props.onConnectionCardPress).not.toHaveBeenCalled();
  expect(props.onDisconnect).toHaveBeenCalled();
  await waitFor(() => expect(screen.getByText(/OK:.*healthy/s)).toBeTruthy());
});

test('routes both open and closed card presses independently from action icons', () => {
  const { screen, props } = renderScreen();

  fireEvent.press(screen.getByTestId('connection-card-active'));
  fireEvent.press(screen.getByTestId('connection-card-closed'));

  expect(props.onConnectionCardPress).toHaveBeenNthCalledWith(1, records[1]);
  expect(props.onConnectionCardPress).toHaveBeenNthCalledWith(2, records[0]);
  expect(props.onOpenConnection).not.toHaveBeenCalled();
});