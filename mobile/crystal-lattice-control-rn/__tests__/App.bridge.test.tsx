import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert, Keyboard, Modal } from 'react-native';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import * as sdk from '@crystal-lattice/frontend-sdk';
import App from '../App';
import { DEVELOPMENT_SETTINGS_STORAGE_KEY } from '../src/settings/developmentSettings';

const url = 'wss://bridge.test/ws/websocket';
const fetchBefore = global.fetch;
const socketBefore = global.WebSocket;

function response(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => 'application/json' },
    text: async () => JSON.stringify(data),
  } as unknown as Response;
}

async function openBridge(screen: ReturnType<typeof render>) {
  await screen.findByTestId('connections-new-connection', {}, { timeout: 5000 });
  fireEvent.press(screen.getByTestId('connections-new-connection'));
  fireEvent.press(screen.getByTestId('connection-method-bridge'));
}

beforeEach(async () => {
  await AsyncStorage.clear();
  jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  global.WebSocket = jest.fn(() => { throw new Error('Unexpected frontend socket'); }) as any;
  global.fetch = jest.fn(async () => response({ protocol_version: 1, servers: [] }));
});
afterEach(() => {
  global.fetch = fetchBefore;
  global.WebSocket = socketBefore;
  jest.restoreAllMocks();
});

it('saves empty successful discovery before pairing and reuses/removes endpoints across relaunch', async () => {
  const first = render(<App />);
  await openBridge(first);
  expect(first.queryByTestId('bridge-transport-mode-websocket')).toBeNull();
  expect(first.queryByTestId('bridge-url-input')).toBeNull();
  fireEvent.press(first.getByTestId('bridge-add-new'));
  fireEvent.changeText(first.getByTestId('bridge-url-input'), url);
  fireEvent.press(first.getByTestId('bridge-connect-button'));
  await waitFor(async () => {
    expect(await sdk.loadSavedBridgeUrls({
      get: AsyncStorage.getItem, set: AsyncStorage.setItem, delete: AsyncStorage.removeItem,
    })).toEqual([{ url, lastUsedAt: expect.any(Number) }]);
  });
  expect(global.WebSocket).not.toHaveBeenCalled();
  first.unmount();
  const reopened = render(<App />);
  await openBridge(reopened);
  fireEvent.press(reopened.getByTestId(`saved-bridge-open-${url}`));
  await reopened.findByText('Available Servers (0)');
  fireEvent.press(reopened.getByTestId('connection-wizard-modal-close'));
  fireEvent.press(reopened.getByTestId('connections-new-connection'));
  fireEvent.press(reopened.getByTestId('connection-method-bridge'));
  await AsyncStorage.setItem(sdk.CONNECTIONS_STORAGE_KEY, 'paired-records-unchanged');
  fireEvent.press(reopened.getByTestId(`saved-bridge-remove-${url}`));
  await waitFor(() => expect(reopened.queryByTestId(`saved-bridge-open-${url}`)).toBeNull());
  expect(await AsyncStorage.getItem(sdk.CONNECTIONS_STORAGE_KEY)).toBe('paired-records-unchanged');
  expect(JSON.parse((await AsyncStorage.getItem(sdk.SAVED_BRIDGES_STORAGE_KEY))!)).toEqual([]);
}, 15000);

it('does not save failed discovery or automatically open a legacy transport', async () => {
  global.fetch = jest.fn(async (address) => String(address).endsWith('/capabilities')
    ? response({ protocol_version: 1 })
    : response({ error: 'discovery_failed' }, 503));
  const screen = render(<App />);
  await openBridge(screen);
  fireEvent.press(screen.getByTestId('bridge-add-new'));
  fireEvent.changeText(screen.getByTestId('bridge-url-input'), url);
  fireEvent.press(screen.getByTestId('bridge-connect-button'));
  await waitFor(() => expect(Alert.alert).toHaveBeenCalledWith(
    'Bridge Connection Error', expect.stringContaining('503'), expect.any(Array),
  ));
  expect(await AsyncStorage.getItem(sdk.SAVED_BRIDGES_STORAGE_KEY)).toBeNull();
  expect(global.WebSocket).not.toHaveBeenCalled();
}, 10000);

it('prefers a bare-domain placeholder, uses HTTPS, and saves the entered address', async () => {
  const screen = render(<App />);
  await openBridge(screen);
  fireEvent.press(screen.getByTestId('bridge-add-new'));
  const input = screen.getByTestId('bridge-url-input');
  expect(input.props.placeholder).toBe('bridge.example.com');
  expect(input.props.value).toBe('');
  fireEvent.changeText(input, ' bridge.example.com ');
  fireEvent.press(screen.getByTestId('bridge-connect-button'));
  await screen.findByText('Available Servers (0)');
  expect(global.fetch).toHaveBeenCalledWith(
    'https://bridge.example.com/bridge/v1/capabilities', expect.any(Object),
  );
  expect(JSON.parse((await AsyncStorage.getItem(sdk.SAVED_BRIDGES_STORAGE_KEY))!))
    .toEqual([{ url: 'bridge.example.com', lastUsedAt: expect.any(Number) }]);
  expect(global.WebSocket).not.toHaveBeenCalled();
}, 10000);

it('uses the same bare-domain normalization for Test Connectivity', async () => {
  const screen = render(<App />);
  await openBridge(screen);
  fireEvent.press(screen.getByTestId('bridge-add-new'));
  fireEvent.changeText(screen.getByTestId('bridge-url-input'), 'bridge.example.com');
  fireEvent.press(screen.getByText('Test Connectivity'));
  await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
    'https://bridge.example.com/health', expect.any(Object),
  ));
}, 10000);

it.each(['https://bridge.test', 'http://localhost:4000'])(
  'connects an explicit %s HTTP address',
  async (address) => {
    const screen = render(<App />);
    await openBridge(screen);
    fireEvent.press(screen.getByTestId('bridge-add-new'));
    fireEvent.changeText(screen.getByTestId('bridge-url-input'), address);
    fireEvent.press(screen.getByTestId('bridge-connect-button'));
    await screen.findByText('Available Servers (0)');
    expect(global.fetch).toHaveBeenCalledWith(
      `${address}/bridge/v1/capabilities`, expect.any(Object),
    );
    expect(global.WebSocket).not.toHaveBeenCalled();
  }, 10000,
);

it.each([undefined, 'websocket', 'hybrid', 'http', 'malformed'])(
  'reopens historical %s records using HTTP with unchanged identity and credentials',
  async (transportMode) => {
    const record = {
      id: 'paired', kind: 'bridge', name: 'Paired server', lastUsedAt: 1,
      bridgeUrl: url, serverId: 'server', serverName: 'Server', pairingToken: 'saved-token',
      ...(transportMode ? { transportMode } : {}),
    };
    await AsyncStorage.setItem(sdk.CONNECTIONS_STORAGE_KEY, JSON.stringify([record]));
    const screen = render(<App />);
    await screen.findByTestId('connection-card-paired', {}, { timeout: 5000 });
    fireEvent.press(screen.getByTestId('connection-card-paired'));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      'https://bridge.test/bridge/v1/pairings/resume',
      expect.objectContaining({
        headers: { 'Content-Type': 'application/json', 'X-Crystal-Bridge-Token': 'saved-token' },
        body: JSON.stringify({ server_id: 'server' }),
      }),
    ));
    expect(global.WebSocket).not.toHaveBeenCalled();
    await waitFor(async () => {
      const stored = JSON.parse((await AsyncStorage.getItem(sdk.CONNECTIONS_STORAGE_KEY))!);
      expect(stored.find((entry: any) => entry.id === record.id))
        .toMatchObject({ ...record, lastUsedAt: expect.any(Number) });
      expect(stored.find((entry: any) => entry.id === record.id).lastUsedAt).toBeGreaterThan(1);
    });
  }, 10000,
);

it('opens general Development Settings from Home and persists/reset legacy overrides', async () => {
  await AsyncStorage.setItem(DEVELOPMENT_SETTINGS_STORAGE_KEY,
    JSON.stringify({ version: 1, otherDevelopmentPreference: true }));
  const screen = render(<App />);
  await screen.findByTestId('home-menu', {}, { timeout: 5000 });
  fireEvent.press(screen.getByTestId('home-menu'));
  fireEvent.press(screen.getByTestId('home-menu-development-settings'));
  const menu = screen.UNSAFE_getAllByType(Modal).find((modal) => modal.props.onDismiss);
  fireEvent(menu!, 'dismiss');
  await screen.findByTestId('development-settings-modal');
  fireEvent.press(screen.getByTestId('development-bridge-mode-hybrid'));
  await waitFor(async () => expect(JSON.parse(
    (await AsyncStorage.getItem(DEVELOPMENT_SETTINGS_STORAGE_KEY))!,
  )).toEqual({ version: 1, otherDevelopmentPreference: true, bridgeTransportOverride: 'hybrid' }));
  fireEvent.press(screen.getByTestId('development-bridge-reset'));
  await waitFor(async () => expect(JSON.parse(
    (await AsyncStorage.getItem(DEVELOPMENT_SETTINGS_STORAGE_KEY))!,
  )).toEqual({ version: 1, otherDevelopmentPreference: true }));
}, 10000);

it('repairs an existing server without replacing its connection ID or cache ownership', async () => {
  const dismissKeyboard = jest.spyOn(Keyboard, 'dismiss');
  const record = {
    id: 'repair-existing', kind: 'bridge', name: 'Repair server', lastUsedAt: 1,
    bridgeUrl: url, serverId: 'server', serverName: 'Repair server',
    pairingToken: null, transportMode: 'websocket',
  };
  await AsyncStorage.setItem(sdk.CONNECTIONS_STORAGE_KEY, JSON.stringify([record]));
  await AsyncStorage.setItem('clc_sessions_cache_v1', JSON.stringify({
    [record.id]: { connectionId: record.id, sessions: [], lastLoadedAt: 1 },
  }));
  global.fetch = jest.fn(async (address) => {
    const path = String(address);
    if (path.endsWith('/capabilities')) return response({ protocol_version: 1 });
    if (path.endsWith('/servers')) return response({ servers: [
      { server_id: 'server', display_name: 'Repair server', computer_name: 'host' },
    ] });
    if (path.endsWith('/pairings/request')) return response({ pairing_request_token: 'request' });
    if (path.endsWith('/pairings/confirm')) {
      return response({ server_id: 'server', pairing_token: 'renewed-token' });
    }
    return response({ sessions: [], agents: [], events: [] });
  });
  const screen = render(<App />);
  await screen.findByTestId('connection-card-repair-existing', {}, { timeout: 5000 });
  fireEvent.press(screen.getByTestId('connection-card-repair-existing'));
  await screen.findByTestId('bridge-pairing-code-input');
  fireEvent.changeText(screen.getByTestId('bridge-pairing-code-input'), '123456');
  fireEvent.press(screen.getByTestId('bridge-submit-pairing'));
  await waitFor(async () => {
    const stored = JSON.parse((await AsyncStorage.getItem(sdk.CONNECTIONS_STORAGE_KEY))!)
      .filter((entry: any) => entry.kind === 'bridge');
    expect(stored).toHaveLength(1);
    expect(stored[0]).toMatchObject({
      id: record.id, serverId: record.serverId, pairingToken: 'renewed-token', transportMode: 'http',
    });
  });
  expect(JSON.parse((await AsyncStorage.getItem('clc_sessions_cache_v1'))!))
    .toHaveProperty(record.id);
  expect(global.WebSocket).not.toHaveBeenCalled();
  expect(dismissKeyboard).toHaveBeenCalled();
}, 10000);

it('dismisses the keyboard when setup closes without changing saved endpoints', async () => {
  const dismissKeyboard = jest.spyOn(Keyboard, 'dismiss');
  const screen = render(<App />);
  await openBridge(screen);
  fireEvent.press(screen.getByTestId('bridge-add-new'));
  fireEvent.changeText(screen.getByTestId('bridge-url-input'), 'bridge.example.com');
  dismissKeyboard.mockClear();
  fireEvent.press(screen.getByTestId('connection-wizard-modal-close'));
  expect(dismissKeyboard).toHaveBeenCalledTimes(1);
  expect(screen.queryByTestId('connection-wizard-modal')).toBeNull();
  expect(await AsyncStorage.getItem(sdk.SAVED_BRIDGES_STORAGE_KEY)).toBeNull();
}, 10000);