import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import { CONNECTIONS_STORAGE_KEY } from '@crystal-lattice/frontend-sdk';
import App from '../App';

function response(data: unknown) {
  return {
    ok: true, status: 200, headers: { get: () => 'application/json' },
    text: async () => JSON.stringify(data),
  } as unknown as Response;
}

it('retains the active HTTP request through pending and cancelled repair of another server', async () => {
  const originalFetch = global.fetch;
  jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  let signal: AbortSignal | null | undefined;
  let resolveServers!: (response: Response) => void;
  const finishEvents: Array<(response: Response) => void> = [];
  global.fetch = jest.fn(async (address, options) => {
    const url = String(address);
    if (url.endsWith('/capabilities')) return response({ protocol_version: 1 });
    if (url.endsWith('/pairings/resume')) return response({ server_id: 'active-server' });
    if (url.endsWith('/servers')) {
      return new Promise<Response>((resolve) => { resolveServers = resolve; });
    }
    if (url.includes('/proxy/events')) {
      signal = options?.signal;
      return new Promise<Response>((resolve, reject) => {
        finishEvents.push(resolve);
        signal?.addEventListener('abort', () => reject(new Error('Aborted')));
      });
    }
    return response({ sessions: [], agents: [], plugins: [], events: [] });
  });
  let screen: ReturnType<typeof render> | undefined;
  try {
    await AsyncStorage.clear();
    await AsyncStorage.setItem(CONNECTIONS_STORAGE_KEY, JSON.stringify([
      {
        id: 'active', kind: 'bridge', name: 'Active', lastUsedAt: 2,
        bridgeUrl: 'ws://bridge.test/ws', serverId: 'active-server', serverName: 'Active',
        pairingToken: 'active-token',
      },
      {
        id: 'repair', kind: 'bridge', name: 'Repair', lastUsedAt: 1,
        bridgeUrl: 'ws://bridge.test/ws', serverId: 'other-server', serverName: 'Repair',
        pairingToken: null,
      },
    ]));
    screen = render(<App />);
    await screen.findByTestId('connection-card-active', {}, { timeout: 5000 });
    fireEvent.press(screen.getByTestId('connection-card-active'));
    await waitFor(() => expect(signal).toBeTruthy());
    fireEvent.press(screen.getByTestId('home-tab'));
    fireEvent.press(screen.getByTestId('connection-card-repair'));
    await waitFor(() => expect(resolveServers).toBeDefined());
    expect(signal?.aborted).toBe(false);
    resolveServers(response({ servers: [] }));
    await screen.findByTestId('connection-wizard-modal');
    fireEvent.press(screen.getByTestId('connection-wizard-modal-close'));
    expect(signal?.aborted).toBe(false);
  } finally {
    screen?.unmount();
    await act(async () => {
      resolveServers?.(response({ servers: [] }));
      for (const finish of finishEvents) finish(response({ events: [] }));
    });
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  }
}, 10000);