import React, { useMemo } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from "@crystal-lattice/frontend-sdk";
import type { ApplicationActionDialogFieldRenderers } from "@crystal-lattice/frontend-rn-components";

import ActionDisplayCard from "../components/ActionDisplayCard";
import { useTheme, type Theme } from "../theme";

interface OpenAIAuthenticationSettingsProps {
  authMode: "api" | "chatgpt";
  onAuthModeChanged: (authMode: "api" | "chatgpt") => void;
  apiKeyField: React.ReactNode;
  authState: string | null;
  activeActionId: string | null;
  display: ActionDisplayPayload | null;
  loginDetails: { url: string; code: string } | null;
  onRunAction: (actionId: string) => void;
  onDismissDisplay: () => void;
  onFollowupAction: (
    action: ActionDisplayFollowupAction,
    formValues?: Record<string, any>
  ) => void;
  fieldRenderers: ApplicationActionDialogFieldRenderers;
}

export default function OpenAIAuthenticationSettings({
  authMode,
  onAuthModeChanged,
  apiKeyField,
  authState,
  activeActionId,
  display,
  loginDetails,
  onRunAction,
  onDismissDisplay,
  onFollowupAction,
  fieldRenderers,
}: OpenAIAuthenticationSettingsProps) {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View testID="embedded-openai-auth-settings" style={styles.section}>
      <Text style={styles.title}>Authentication</Text>
      <View testID="embedded-provider-openai-default-authentication">
        <Text style={styles.label}>Default authentication</Text>
        <Text style={styles.explanation}>
          Sessions use this authentication method unless overridden in Session Settings.
        </Text>
        <View style={styles.actions}>
          {(["api", "chatgpt"] as const).map((mode) => (
            <TouchableOpacity
              key={mode}
              testID={`embedded-provider-openai-auth-${mode}`}
              accessibilityRole="radio"
              accessibilityLabel={mode === "api" ? "API key" : "ChatGPT"}
              accessibilityState={{ selected: mode === authMode }}
              accessibilityActions={[{ name: "activate", label: "Select authentication" }]}
              onAccessibilityAction={(event) => {
                if (event.nativeEvent.actionName === "activate") {
                  onAuthModeChanged(mode);
                }
              }}
              onPress={() => onAuthModeChanged(mode)}
              style={[styles.button, mode === authMode && styles.selectedButton]}
            >
              <Text style={[styles.buttonText, mode === authMode && styles.selectedText]}>
                {mode === "api" ? "API key" : "ChatGPT"}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text testID="embedded-provider-openai-auth-selected" style={styles.explanation}>
          {`Default authentication: ${authMode === "api" ? "API key" : "ChatGPT"}`}
        </Text>
      </View>

      {apiKeyField}

      <View testID="embedded-provider-openai-chatgpt-account" style={styles.account}>
        <Text style={styles.label}>ChatGPT account</Text>
        <Text testID="embedded-provider-openai-chatgpt-auth-state" style={styles.explanation}>
          {`ChatGPT status: ${authState ?? "not checked"}`}
        </Text>
        <View style={styles.actions}>
          {[
            ["login_start", "Sign in with ChatGPT"],
            ["check_status", "Check status"],
            ["cancel_login", "Cancel"],
            ["logout", "Log out"],
          ].map(([actionId, label]) => (
            <TouchableOpacity
              key={actionId}
              testID={`embedded-provider-openai-chatgpt-${actionId}`}
              accessibilityRole="button"
              accessibilityLabel={label}
              accessibilityActions={[{ name: "activate", label }]}
              onAccessibilityAction={(event) => {
                if (event.nativeEvent.actionName === "activate" && activeActionId === null) {
                  onRunAction(actionId);
                }
              }}
              disabled={activeActionId !== null}
              onPress={() => onRunAction(actionId)}
              style={[styles.button, activeActionId !== null && styles.disabled]}
            >
              <Text style={styles.buttonText}>
                {activeActionId === actionId ? "Working…" : label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        {display ? (
          <ActionDisplayCard
            display={display}
            activeActionId={activeActionId}
            bodyTestID="embedded-provider-openai-chatgpt-display"
            onDismiss={onDismissDisplay}
            onFollowupAction={onFollowupAction}
            fieldRenderers={fieldRenderers}
            compact
            bounded
          />
        ) : null}
        {loginDetails ? (
          <View>
            <Text style={styles.explanation}>Complete login in another browser:</Text>
            <Text
              testID="embedded-provider-openai-chatgpt-login-url"
              style={styles.explanation}
              selectable
            >
              {loginDetails.url}
            </Text>
            <Text
              testID="embedded-provider-openai-chatgpt-login-code"
              style={styles.explanation}
              selectable
            >
              {loginDetails.code}
            </Text>
          </View>
        ) : null}
      </View>
    </View>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    section: { marginTop: 12, gap: 10 },
    title: { color: theme.text, fontWeight: "700", fontSize: theme.typography.fontSize.normal },
    label: { color: theme.textSecondary, fontWeight: "600", fontSize: theme.typography.fontSize.small },
    explanation: { color: theme.textSecondary, fontSize: theme.typography.fontSize.small, marginTop: 4 },
    account: { gap: 8 },
    actions: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 8 },
    button: {
      borderRadius: 8,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      paddingHorizontal: 12,
      paddingVertical: 8,
    },
    selectedButton: { borderColor: theme.primary, backgroundColor: theme.primary },
    buttonText: { color: theme.primary, fontWeight: "600" },
    selectedText: { color: theme.textOnPrimary },
    disabled: { opacity: 0.45 },
  });