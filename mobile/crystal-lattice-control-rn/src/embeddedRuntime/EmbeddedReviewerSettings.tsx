import React, { useEffect, useMemo, useState } from "react";
import { StyleSheet, Switch, Text, View } from "react-native";

import { useTheme, type Theme } from "../theme";
import {
  configureEmbeddedPythonRuntime,
  getEmbeddedPythonRuntimeConfiguration,
  type EmbeddedRuntimePublicConfiguration,
} from "./embeddedPythonRuntime";

interface EmbeddedReviewerSettingsProps {
  visible: boolean;
  onSaved?: (configuration: EmbeddedRuntimePublicConfiguration) => void;
}

export default function EmbeddedReviewerSettings({
  visible,
  onSaved,
}: EmbeddedReviewerSettingsProps) {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!visible) return;
    let active = true;
    setBusy(true);
    setError("");
    void getEmbeddedPythonRuntimeConfiguration()
      .then((configuration) => {
        if (active) setEnabled(configuration.reviewerVisible);
      })
      .catch((cause) => {
        if (active) setError(cause instanceof Error ? cause.message : "Could not load reviewer settings.");
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => { active = false; };
  }, [visible]);

  const save = async (reviewerVisible: boolean) => {
    setBusy(true);
    setError("");
    try {
      const saved = await configureEmbeddedPythonRuntime({ version: 3, reviewerVisible });
      setEnabled(saved.reviewerVisible);
      onSaved?.(saved);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save reviewer settings.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <View>
      <View style={styles.row}>
        <Text style={styles.label}>Show reviewer sample provider</Text>
        <View
          testID="global-settings-reviewer-visible"
          accessible
          accessibilityRole="switch"
          accessibilityLabel="Show reviewer sample provider"
          accessibilityState={{ checked: enabled, disabled: busy }}
          accessibilityActions={[{ name: "activate", label: enabled ? "Hide reviewer" : "Show reviewer" }]}
          onAccessibilityAction={(event) => {
            if (event.nativeEvent.actionName === "activate" && !busy) void save(!enabled);
          }}
        >
          <Switch
            testID="global-settings-reviewer-visible-control"
            value={enabled}
            disabled={busy}
            onValueChange={(value) => void save(value)}
            accessible={false}
          />
        </View>
      </View>
      <Text style={styles.detail}>
        {enabled
          ? "Enter the supplied reviewer API key in Local provider settings."
          : "Enable only when using the supplied reviewer access."}
      </Text>
      {error ? <Text testID="global-settings-reviewer-error" style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    row: { flexDirection: "row", alignItems: "center", gap: 16, paddingVertical: 10 },
    label: { flex: 1, color: theme.text, fontWeight: "600", fontSize: theme.typography.fontSize.normal },
    detail: { color: theme.textSecondary, fontSize: theme.typography.fontSize.small },
    error: { color: theme.danger, fontSize: theme.typography.fontSize.small },
  });