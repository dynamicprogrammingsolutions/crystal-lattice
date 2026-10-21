import React, { useMemo, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import type { BridgeTransportMode } from "@crystal-lattice/frontend-sdk";
import PanelModalFrame from "./PanelModalFrame";
import { useTheme } from "../theme";
import type { DevelopmentSettingsState } from "../settings/useDevelopmentSettings";
import {
  DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY,
  TRANSCRIPT_ANCHOR_STRATEGY_OPTIONS,
  type TranscriptAnchorStrategy,
} from "../transcriptAnchorStrategy";

interface Props {
  visible: boolean;
  onRequestClose: () => void;
  preferences: DevelopmentSettingsState;
}

const MODES: ReadonlyArray<{ value: BridgeTransportMode; label: string }> = [
  { value: "http", label: "HTTP — Product default" },
  { value: "websocket", label: "WebSocket — Legacy diagnostic" },
  { value: "hybrid", label: "Hybrid — Legacy diagnostic" },
];

export default function DevelopmentSettingsModal({
  visible,
  onRequestClose,
  preferences,
}: Props) {
  const theme = useTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        section: { gap: 12 },
        heading: { color: theme.text, fontSize: 18, fontWeight: "600" },
        description: {
          color: theme.textSecondary,
          fontSize: 14,
          lineHeight: 20,
        },
        option: {
          padding: 12,
          borderWidth: 1,
          borderColor: theme.border,
          borderRadius: 8,
        },
        selected: {
          borderColor: theme.primary,
          backgroundColor: theme.surface,
        },
        label: { color: theme.text, fontSize: 15 },
        reset: { color: theme.primary, fontSize: 15 },
        scrollContent: { paddingBottom: 32 },
      }),
    [theme]
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const select = async (mode: BridgeTransportMode) => {
    setSaving(true);
    setError(null);
    try {
      await preferences.setBridgeMode(mode);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setSaving(false);
    }
  };
  const selectTranscriptAnchorStrategy = async (
    strategy: TranscriptAnchorStrategy
  ) => {
    setSaving(true);
    setError(null);
    try {
      await preferences.setTranscriptAnchorStrategy(strategy);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setSaving(false);
    }
  };

  return (
    <PanelModalFrame
      visible={visible}
      title="Development Settings"
      testID="development-settings-modal"
      onRequestClose={onRequestClose}
      scroll
      scrollTestID="development-settings-scroll"
      scrollContentStyle={styles.scrollContent}
      showSpinner={saving || !preferences.hydrated}
      statusText={error ?? preferences.error?.message}
      statusTone="error"
    >
      <View style={styles.section} testID="development-settings-bridge-section">
        <Text style={styles.heading}>Bridge</Text>
        <Text style={styles.description}>
          Applies the next time a bridge connection is opened. Open connections
          stay unchanged.
        </Text>
        {MODES.map(({ value, label }) => (
          <TouchableOpacity
            key={value}
            testID={`development-bridge-mode-${value}`}
            accessibilityRole="radio"
            accessibilityLabel={`${label}${
              preferences.mode === value ? " selected" : ""
            }`}
            accessibilityState={{ checked: preferences.mode === value }}
            style={[
              styles.option,
              preferences.mode === value && styles.selected,
            ]}
            disabled={saving || !preferences.hydrated}
            onPress={() => {
              void select(value);
            }}
          >
            <Text style={styles.label}>{label}</Text>
          </TouchableOpacity>
        ))}
        <TouchableOpacity
          testID="development-bridge-reset"
          accessibilityRole="button"
          accessibilityLabel="Reset bridge transport"
          disabled={saving || !preferences.hydrated}
          onPress={() => {
            void select("http");
          }}
        >
          <Text style={styles.reset}>Reset bridge transport</Text>
        </TouchableOpacity>
      </View>
      <View
        style={styles.section}
        testID="development-settings-transcript-anchor-section"
      >
        <Text style={styles.heading}>Transcript range navigation</Text>
        <Text style={styles.description}>
          Controls viewport restoration when older or newer message ranges are
          loaded. The legacy option is intended only for controlled diagnosis.
        </Text>
        {TRANSCRIPT_ANCHOR_STRATEGY_OPTIONS.map(
          ({ value, label, description }) => (
            <TouchableOpacity
              key={value}
              testID={`development-transcript-anchor-${value}`}
              accessibilityRole="radio"
              accessibilityLabel={`${label}${
                preferences.transcriptAnchorStrategy === value
                  ? " selected"
                  : ""
              }`}
              accessibilityState={{
                checked: preferences.transcriptAnchorStrategy === value,
              }}
              style={[
                styles.option,
                preferences.transcriptAnchorStrategy === value &&
                  styles.selected,
              ]}
              disabled={saving || !preferences.hydrated}
              onPress={() => {
                void selectTranscriptAnchorStrategy(value);
              }}
            >
              <Text style={styles.label}>{label}</Text>
              <Text style={styles.description}>{description}</Text>
            </TouchableOpacity>
          )
        )}
        <TouchableOpacity
          testID="development-transcript-anchor-reset"
          accessibilityRole="button"
          accessibilityLabel="Reset transcript range navigation"
          disabled={saving || !preferences.hydrated}
          onPress={() => {
            void selectTranscriptAnchorStrategy(
              DEFAULT_TRANSCRIPT_ANCHOR_STRATEGY
            );
          }}
        >
          <Text style={styles.reset}>Reset transcript range navigation</Text>
        </TouchableOpacity>
      </View>
    </PanelModalFrame>
  );
}
