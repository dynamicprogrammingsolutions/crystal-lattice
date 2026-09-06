import React from 'react';
import { act, renderHook, waitFor } from '@testing-library/react-native';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

import {
  DESKTOP_HOME_WATCHLIST_STORAGE_KEY,
  DESKTOP_SESSION_NOTES_STORAGE_KEY,
  DesktopHomeWorkspaceProvider,
  useDesktopHomeWorkspace,
} from '../src/home/DesktopHomeWorkspaceContext';

function createStore(initial: Record<string, string> = {}): KeyValueStore & {
  values: Map<string, string>;
} {
  const values = new Map(Object.entries(initial));
  return {
    values,
    get: async key => values.get(key) ?? null,
    set: async (key, value) => {
      values.set(key, value);
    },
    delete: async key => {
      values.delete(key);
    },
  };
}

describe('DesktopHomeWorkspaceProvider', () => {
  it('hydrates and persists composite Watchlist order plus session-ID notes', async () => {
    const store = createStore({
      [DESKTOP_HOME_WATCHLIST_STORAGE_KEY]: JSON.stringify([
        { connectionId: 'one', sessionId: 'shared' },
      ]),
      [DESKTOP_SESSION_NOTES_STORAGE_KEY]: JSON.stringify({
        shared: 'existing',
      }),
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <DesktopHomeWorkspaceProvider store={store}>
        {children}
      </DesktopHomeWorkspaceProvider>
    );
    const result = renderHook(() => useDesktopHomeWorkspace(), { wrapper });
    await waitFor(() => expect(result.result.current.hydrated).toBe(true));

    act(() => {
      result.result.current.addToWatchlist('two', 'other');
      result.result.current.setSessionNote('shared', 'updated');
    });
    await waitFor(() =>
      expect(
        JSON.parse(
          store.values.get(DESKTOP_HOME_WATCHLIST_STORAGE_KEY) ?? '[]',
        ),
      ).toEqual([
        { connectionId: 'one', sessionId: 'shared' },
        { connectionId: 'two', sessionId: 'other' },
      ]),
    );
    expect(
      JSON.parse(store.values.get(DESKTOP_SESSION_NOTES_STORAGE_KEY) ?? '{}'),
    ).toEqual({ shared: 'updated' });
  });

  it('removes deleted-connection Watchlist entries without deleting notes', async () => {
    const store = createStore();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <DesktopHomeWorkspaceProvider store={store}>
        {children}
      </DesktopHomeWorkspaceProvider>
    );
    const result = renderHook(() => useDesktopHomeWorkspace(), { wrapper });
    await waitFor(() => expect(result.result.current.hydrated).toBe(true));
    act(() => {
      result.result.current.addToWatchlist('connection', 'session');
      result.result.current.setSessionNote('session', 'keep');
      result.result.current.removeConnectionFromWatchlist('connection');
    });
    expect(result.result.current.watchlist).toEqual([]);
    expect(result.result.current.notes).toEqual({ session: 'keep' });
  });
});
