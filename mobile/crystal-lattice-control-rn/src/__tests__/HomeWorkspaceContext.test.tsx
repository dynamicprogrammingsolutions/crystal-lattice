import React from 'react';
import { act, renderHook, waitFor } from '@testing-library/react-native';
import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';

import {
  HomeWorkspaceProvider,
  useHomeWorkspace,
} from '../HomeWorkspaceContext';
import {
  HOME_WATCHLIST_STORAGE_KEY,
  SESSION_NOTES_STORAGE_KEY,
} from '../homeWorkspaceState';

function createStore(): KeyValueStore & { values: Map<string, string> } {
  const values = new Map<string, string>();
  return {
    values,
    get: async (key) => values.get(key) ?? null,
    set: async (key, value) => {
      values.set(key, value);
    },
    delete: async (key) => {
      values.delete(key);
    },
  };
}

describe('HomeWorkspaceProvider', () => {
  it('persists composite Watchlist order and permanent session-id notes independently', async () => {
    const store = createStore();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <HomeWorkspaceProvider store={store}>{children}</HomeWorkspaceProvider>
    );
    const first = renderHook(() => useHomeWorkspace(), { wrapper });
    await waitFor(() => expect(first.result.current.hydrated).toBe(true));

    act(() => {
      first.result.current.addToWatchlist('one', 'shared');
      first.result.current.addToWatchlist('two', 'shared');
      first.result.current.setSessionNote('shared', 'Permanent local note');
      first.result.current.moveWatchlistItem(1, 0);
      first.result.current.removeFromWatchlist('one', 'shared');
    });

    await waitFor(() => {
      expect(
        JSON.parse(store.values.get(HOME_WATCHLIST_STORAGE_KEY) ?? '[]'),
      ).toEqual([{ connectionId: 'two', sessionId: 'shared' }]);
      expect(
        JSON.parse(store.values.get(SESSION_NOTES_STORAGE_KEY) ?? '{}'),
      ).toEqual({ shared: 'Permanent local note' });
    });
    first.unmount();

    const second = renderHook(() => useHomeWorkspace(), { wrapper });
    await waitFor(() => expect(second.result.current.hydrated).toBe(true));
    expect(second.result.current.watchlist).toEqual([
      { connectionId: 'two', sessionId: 'shared' },
    ]);
    expect(second.result.current.notes.shared).toBe('Permanent local note');

    act(() => second.result.current.removeSessionNote('shared'));
    await waitFor(() =>
      expect(
        JSON.parse(store.values.get(SESSION_NOTES_STORAGE_KEY) ?? '{}'),
      ).toEqual({}),
    );
  });
});