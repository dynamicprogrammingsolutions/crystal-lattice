import { useCallback } from 'react';
import type { BridgeTransportMode, KeyValueStore } from '@crystal-lattice/frontend-sdk';
import {
  DEFAULT_DEVELOPMENT_SETTINGS,
  getDevelopmentBridgeMode,
  loadDevelopmentSettings,
  saveDevelopmentSettings,
  withDevelopmentBridgeMode,
} from './developmentSettings';
import { usePersistedValue } from './usePersistedValue';

export function useDevelopmentSettings(store: KeyValueStore) {
  const { value, hydrated, error, update } = usePersistedValue(
    store, DEFAULT_DEVELOPMENT_SETTINGS, loadDevelopmentSettings, saveDevelopmentSettings,
  );
  const setBridgeMode = useCallback(
    (mode: BridgeTransportMode) => update((current) => withDevelopmentBridgeMode(current, mode)),
    [update],
  );
  return { settings: value, hydrated, error, mode: getDevelopmentBridgeMode(value), setBridgeMode };
}

export type DevelopmentSettingsState = ReturnType<typeof useDevelopmentSettings>;