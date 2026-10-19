import { useCallback } from "react";
import type {
  BridgeTransportMode,
  KeyValueStore,
} from "@crystal-lattice/frontend-sdk";
import {
  DEFAULT_DEVELOPMENT_SETTINGS,
  getDevelopmentBridgeMode,
  getDevelopmentTranscriptAnchorStrategy,
  loadDevelopmentSettings,
  saveDevelopmentSettings,
  withDevelopmentBridgeMode,
  withDevelopmentTranscriptAnchorStrategy,
} from "./developmentSettings";
import { usePersistedValue } from "./usePersistedValue";
import type { TranscriptAnchorStrategy } from "../transcriptAnchorStrategy";

export function useDevelopmentSettings(store: KeyValueStore) {
  const { value, hydrated, error, update } = usePersistedValue(
    store,
    DEFAULT_DEVELOPMENT_SETTINGS,
    loadDevelopmentSettings,
    saveDevelopmentSettings
  );
  const setBridgeMode = useCallback(
    (mode: BridgeTransportMode) =>
      update((current) => withDevelopmentBridgeMode(current, mode)),
    [update]
  );
  const setTranscriptAnchorStrategy = useCallback(
    (strategy: TranscriptAnchorStrategy) =>
      update((current) =>
        withDevelopmentTranscriptAnchorStrategy(current, strategy)
      ),
    [update]
  );
  return {
    settings: value,
    hydrated,
    error,
    mode: getDevelopmentBridgeMode(value),
    setBridgeMode,
    transcriptAnchorStrategy: getDevelopmentTranscriptAnchorStrategy(value),
    setTranscriptAnchorStrategy,
  };
}

export type DevelopmentSettingsState = ReturnType<
  typeof useDevelopmentSettings
>;
