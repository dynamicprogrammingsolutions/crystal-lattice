import { useCallback } from 'react';
import {
  loadSavedBridgeUrls,
  saveSavedBridgeUrls,
  type KeyValueStore,
  type SavedBridgeUrl,
} from '@crystal-lattice/frontend-sdk';
import { usePersistedValue } from '../settings/usePersistedValue';

const EMPTY_BRIDGES: SavedBridgeUrl[] = [];

export function useSavedBridgeUrls(store: KeyValueStore) {
  const { value, hydrated, error, update } = usePersistedValue(
    store, EMPTY_BRIDGES, loadSavedBridgeUrls, saveSavedBridgeUrls,
  );
  const remember = useCallback((url: string) => update((current) => {
    const existing = current.find((entry) => entry.url === url);
    return [
      { ...existing, url, lastUsedAt: Date.now() },
      ...current.filter((entry) => entry.url !== url),
    ];
  }), [update]);
  const remove = useCallback(
    (url: string) => update((current) => current.filter((entry) => entry.url !== url)),
    [update],
  );
  return { bridges: value, hydrated, error, remember, remove };
}