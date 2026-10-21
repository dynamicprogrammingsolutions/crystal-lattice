import type { KeyValueStore } from '../storage/keyValueStore';
import type { SavedBridgeUrl } from './types';

export const SAVED_BRIDGES_STORAGE_KEY = 'clc_saved_bridges_v1';

export async function loadSavedBridgeUrls(store: KeyValueStore): Promise<SavedBridgeUrl[]> {
  const raw = await store.get(SAVED_BRIDGES_STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (entry): entry is SavedBridgeUrl =>
        entry !== null &&
        typeof entry === 'object' &&
        typeof entry.url === 'string' &&
        entry.url.length > 0 &&
        typeof entry.lastUsedAt === 'number' &&
        Number.isFinite(entry.lastUsedAt) &&
        (entry.label === undefined || typeof entry.label === 'string'),
    );
  } catch {
    return [];
  }
}

export async function saveSavedBridgeUrls(
  store: KeyValueStore,
  bridges: readonly SavedBridgeUrl[],
): Promise<void> {
  await store.set(SAVED_BRIDGES_STORAGE_KEY, JSON.stringify(bridges));
}