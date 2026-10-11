import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert, Modal } from 'react-native';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import {
  CONNECTIONS_STORAGE_KEY,
  FetchTransport,
  RestAgentBackend,
  SAVED_BRIDGES_STORAGE_KEY,
} from '@crystal-lattice/frontend-sdk';
import {
  startBackendServer,
  startBridgeForE2E,
  waitForAsync,
  waitForStdoutMatch,
  type StartedServer,
  type StartedBridge,
} from '../../../packages/frontend-sdk/src/integration/harness';
import App from '../App';

let bridge: StartedBridge;
let started: StartedServer;
let backend: RestAgentBackend;
const serverId = `mobile-bridge-${Date.now()}`;
const originalSocket = global.WebSocket;
const originalFetch = global.fetch;

async function openBridge(screen: ReturnType<typeof render>) {
  await screen.findByTestId('connections-new-connection', {}, { timeout: 10000 });
  fireEvent.press(screen.getByTestId('home-tab'));
  fireEvent.press(screen.getByTestId('connections-new-connection'));
  fireEvent.press(screen.getByTestId('connection-method-bridge'));
}

beforeAll(async () => {
  bridge = await startBridgeForE2E();
  started = await startBackendServer({
    config: {
      agents: { default: { provider: 'deterministic_stream', model: 'fixture' } },
      plugins: ['plugins.deterministic_stream_provider.DeterministicStreamProvider'],
    },
    bridge: { url: bridge.bridgeUrl, serverId, displayName: 'Mobile integration server' },
  });
  backend = new RestAgentBackend({ transport: new FetchTransport({ baseUrl: started.baseUrl }) });
  await waitForAsync(async () => {
    const response = await fetch(
      `${bridge.bridgeUrl.replace('ws://', 'http://').replace('/ws/websocket', '')}/bridge/v1/servers`,
    );
    const data = await response.json();
    return data.servers.some((entry: any) => entry.server_id === serverId);
  }, { timeoutMs: 30000 });
});

afterAll(async () => {
  global.WebSocket = originalSocket;
  global.fetch = originalFetch;
  jest.restoreAllMocks();
  await started?.stop();
  await bridge?.stop();
});

it('discovers from the Home modal, saves before pairing, reuses credentials, and retains the active HTTP runtime', async () => {
  await AsyncStorage.clear();
  jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  global.WebSocket = jest.fn(() => { throw new Error('HTTP frontend opened a socket'); }) as any;
  const eventRequests: Array<{ signal: AbortSignal | null | undefined; complete: boolean }> = [];
  global.fetch = ((address: RequestInfo | URL, options?: RequestInit) => {
    if (!String(address).includes('/bridge/v1/proxy/events')) return originalFetch(address, options);
    const request = { signal: options?.signal, complete: false };
    eventRequests.push(request);
    return originalFetch(address, options).finally(() => { request.complete = true; });
  }) as typeof fetch;
  const first = render(<App />);
  await openBridge(first);
  fireEvent.press(first.getByTestId('bridge-add-new'));
  fireEvent.changeText(first.getByTestId('bridge-url-input'), bridge.bridgeUrl);
  fireEvent.press(first.getByTestId('bridge-connect-button'));
  await first.findByTestId(`bridge-server-${serverId}`, {}, { timeout: 30000 });
  expect(JSON.parse((await AsyncStorage.getItem(SAVED_BRIDGES_STORAGE_KEY))!))
    .toEqual([{ url: bridge.bridgeUrl, lastUsedAt: expect.any(Number) }]);
  expect(JSON.parse((await AsyncStorage.getItem(CONNECTIONS_STORAGE_KEY)) ?? '[]')
    .filter((record: any) => record.kind === 'bridge')).toEqual([]);
  fireEvent.press(first.getByTestId('connection-wizard-modal-close'));
  first.unmount();

  const reopened = render(<App />);
  await openBridge(reopened);
  fireEvent.press(reopened.getByTestId(`saved-bridge-open-${bridge.bridgeUrl}`));
  await reopened.findByTestId(`bridge-server-${serverId}`, {}, { timeout: 30000 });
  fireEvent.press(reopened.getByTestId(`bridge-server-${serverId}`));
  const code = await waitForStdoutMatch({
    stdout: started.stdout, pattern: /PAIRING CODE:\s*(\d{6})/, timeoutMs: 30000,
  });
  await waitFor(() => expect(reopened.getByTestId('bridge-submit-pairing')
    .props.accessibilityState?.disabled).not.toBe(true), { timeout: 10000 });
  await waitFor(() => expect(reopened.getByTestId('bridge-submit-pairing')
    .props.disabled).not.toBe(true), { timeout: 10000 });
  fireEvent.changeText(reopened.getByTestId('bridge-pairing-code-input'), code[1]);
  fireEvent.press(reopened.getByTestId('bridge-submit-pairing'));
  await waitFor(() => expect(reopened.queryByTestId('connection-wizard-modal')).toBeNull(),
    { timeout: 10000 });
  let record: any;
  await waitFor(async () => {
    record = JSON.parse((await AsyncStorage.getItem(CONNECTIONS_STORAGE_KEY))!)
      .find((entry: any) => entry.kind === 'bridge');
    expect(record).toMatchObject({ serverId, transportMode: 'http', pairingToken: expect.any(String) });
  });

  await waitForAsync(async () => eventRequests.some((request) => !request.complete),
    { timeoutMs: 10000 });
  const pendingEvent = eventRequests.find((request) => !request.complete)!;
  fireEvent.press(reopened.getByTestId('home-menu'));
  fireEvent.press(reopened.getByTestId('home-menu-development-settings'));
  fireEvent(reopened.UNSAFE_getAllByType(Modal).find((modal) => modal.props.onDismiss)!, 'dismiss');
  await reopened.findByTestId('development-settings-modal');
  fireEvent.press(reopened.getByTestId('development-bridge-mode-websocket'));
  await waitFor(() => expect(reopened.getByTestId('development-bridge-mode-websocket')
    .props.accessibilityState.checked).toBe(true));
  expect(pendingEvent.signal?.aborted).toBe(false);
  fireEvent.press(reopened.getByTestId('development-settings-modal-close'));
  fireEvent.press(reopened.getByTestId(`connection-new-session-${record.id}`));
  fireEvent.press(await reopened.findByTestId('new-session-agent-default'));
  await reopened.findByTestId('message-composer-input', {}, { timeout: 30000 });
  expect(await backend.listSessions()).toHaveLength(1);
  expect(global.WebSocket).not.toHaveBeenCalled();
  fireEvent.changeText(reopened.getByTestId('message-composer-input'), 'Mobile bridge smoke');
  await waitFor(() => expect(reopened.getByTestId('composer-send')
    .props.accessibilityState?.disabled).not.toBe(true));
  fireEvent.press(reopened.getByTestId('composer-send'));
  await waitFor(async () => {
    const sessions = await backend.listSessions();
    const messages = await backend.listMessages(sessions[0].session_id);
    expect(messages.messages.some((entry) => entry.message.role === 'assistant')).toBe(true);
  }, { timeout: 30000 });

  fireEvent.press(reopened.getByTestId('home-tab'));
  fireEvent.press(reopened.getByTestId('home-menu'));
  fireEvent.press(reopened.getByTestId('home-menu-development-settings'));
  fireEvent(reopened.UNSAFE_getAllByType(Modal).find((modal) => modal.props.onDismiss)!, 'dismiss');
  await reopened.findByTestId('development-settings-modal');
  fireEvent.press(reopened.getByTestId('development-bridge-reset'));
  await waitFor(() => expect(reopened.getByTestId('development-bridge-mode-http')
    .props.accessibilityState.checked).toBe(true));
  fireEvent.press(reopened.getByTestId('development-settings-modal-close'));
  reopened.unmount();
  const third = render(<App />);
  await third.findByTestId(`connection-card-${record.id}`, {}, { timeout: 10000 });
  fireEvent.press(third.getByTestId(`connection-new-session-${record.id}`));
  fireEvent.press(await third.findByTestId('new-session-agent-default', {}, { timeout: 30000 }));
  await third.findByTestId('message-composer-input', {}, { timeout: 30000 });
  expect(await backend.listSessions()).toHaveLength(2);
  const after = JSON.parse((await AsyncStorage.getItem(CONNECTIONS_STORAGE_KEY))!)
    .find((entry: any) => entry.id === record.id);
  expect(after).toMatchObject({ id: record.id, pairingToken: record.pairingToken, serverId });
  expect(global.WebSocket).not.toHaveBeenCalled();
  third.unmount();
}, 180000);