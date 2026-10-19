import type {
  BridgeTransportMode,
  KeyValueStore,
} from "@crystal-lattice/frontend-sdk";
import {
  DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY,
  normalizeTranscriptAnchorStrategy,
  type TranscriptAnchorStrategy,
} from "../transcriptAnchorStrategy";

export const DEVELOPMENT_SETTINGS_STORAGE_KEY = "clc_development_settings_v1";

export interface DevelopmentSettings {
  version: 1;
  bridgeTransportOverride?: "websocket" | "hybrid";
  transcriptAnchorStrategy?: Exclude<
    TranscriptAnchorStrategy,
    typeof DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY
  >;
  [key: string]: unknown;
}

export const DEFAULT_DEVELOPMENT_SETTINGS: DevelopmentSettings = { version: 1 };

export function getDevelopmentBridgeMode(
  settings: DevelopmentSettings
): BridgeTransportMode {
  return settings.bridgeTransportOverride ?? "http";
}

export function withDevelopmentBridgeMode(
  settings: DevelopmentSettings,
  mode: BridgeTransportMode
): DevelopmentSettings {
  const { bridgeTransportOverride: _prior, ...otherSettings } = settings;
  return mode === "http"
    ? { ...otherSettings, version: 1 }
    : { ...otherSettings, version: 1, bridgeTransportOverride: mode };
}

export function getDevelopmentTranscriptAnchorStrategy(
  settings: DevelopmentSettings
): TranscriptAnchorStrategy {
  return normalizeTranscriptAnchorStrategy(settings.transcriptAnchorStrategy);
}

export function withDevelopmentTranscriptAnchorStrategy(
  settings: DevelopmentSettings,
  strategy: TranscriptAnchorStrategy
): DevelopmentSettings {
  const { transcriptAnchorStrategy: _prior, ...otherSettings } = settings;
  return strategy === DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY
    ? { ...otherSettings, version: 1 }
    : { ...otherSettings, version: 1, transcriptAnchorStrategy: strategy };
}

export async function loadDevelopmentSettings(
  store: KeyValueStore
): Promise<DevelopmentSettings> {
  const raw = await store.get(DEVELOPMENT_SETTINGS_STORAGE_KEY);
  if (!raw) return DEFAULT_DEVELOPMENT_SETTINGS;
  try {
    const parsed = JSON.parse(raw);
    if (
      !parsed ||
      typeof parsed !== "object" ||
      Array.isArray(parsed) ||
      parsed.version !== 1
    ) {
      return DEFAULT_DEVELOPMENT_SETTINGS;
    }
    const mode = parsed.bridgeTransportOverride;
    const bridgeSettings = withDevelopmentBridgeMode(
      parsed,
      mode === "websocket" || mode === "hybrid" ? mode : "http"
    );
    return withDevelopmentTranscriptAnchorStrategy(
      bridgeSettings,
      normalizeTranscriptAnchorStrategy(parsed.transcriptAnchorStrategy)
    );
  } catch {
    return DEFAULT_DEVELOPMENT_SETTINGS;
  }
}

export async function saveDevelopmentSettings(
  store: KeyValueStore,
  settings: DevelopmentSettings
): Promise<void> {
  await store.set(DEVELOPMENT_SETTINGS_STORAGE_KEY, JSON.stringify(settings));
}
