import React, { useEffect, useMemo, useState } from "react";
import {
  Linking,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import Clipboard from "@react-native-clipboard/clipboard";
import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from "@crystal-lattice/frontend-sdk";

import ActionDisplayCard from "../components/ActionDisplayCard";
import PanelModalFrame from "../components/PanelModalFrame";
import { useTheme, type Theme } from "../theme";
import {
  configureEmbeddedPythonRuntime,
  executeEmbeddedRuntimeApplicationAction,
  getEmbeddedPythonRuntimeConfiguration,
  validateEmbeddedPythonRuntimeConfiguration,
  type EmbeddedProviderProfile,
  type EmbeddedProviderProfileId,
  type EmbeddedProviderProfileUpdate,
  type EmbeddedRuntimePublicConfiguration,
} from "./embeddedPythonRuntime";

const PROFILE_ORDER: EmbeddedProviderProfileId[] = [
  "openai",
  "reviewer",
  "compatible",
  "openrouter",
  "anthropic",
];

type ProfileDraft = EmbeddedProviderProfile & {
  apiKey: string;
  clearApiKey: boolean;
};

type ValidationState =
  | { tone: "idle"; message: string }
  | { tone: "busy"; message: string }
  | { tone: "success"; message: string }
  | { tone: "error"; message: string };

interface EmbeddedRuntimeSettingsModalProps {
  visible: boolean;
  onRequestClose: () => void;
  onSaved?: (configuration: EmbeddedRuntimePublicConfiguration) => void;
}

function draftsFromConfiguration(
  configuration: EmbeddedRuntimePublicConfiguration
): Record<EmbeddedProviderProfileId, ProfileDraft> {
  return Object.fromEntries(
    PROFILE_ORDER.map((profileId) => [
      profileId,
      {
        ...configuration.providers[profileId],
        apiKey: "",
        clearApiKey: false,
      },
    ])
  ) as Record<EmbeddedProviderProfileId, ProfileDraft>;
}

function updatesFromDrafts(
  drafts: Record<EmbeddedProviderProfileId, ProfileDraft>,
  forceEnabledProfile?: EmbeddedProviderProfileId
): Record<EmbeddedProviderProfileId, EmbeddedProviderProfileUpdate> {
  return Object.fromEntries(
    PROFILE_ORDER.map((profileId) => {
      const draft = drafts[profileId];
      return [
        profileId,
        {
          enabled:
            profileId === forceEnabledProfile ? true : draft.enabled,
          baseUrl: draft.baseUrl.trim(),
          model: draft.model.trim(),
          ...(profileId === "openai"
            ? { authMode: draft.authMode ?? "api" }
            : {}),
          ...(profileId === "reviewer"
            ? { tlsCaBundle: draft.tlsCaBundle?.trim() ?? "" }
            : {}),
          ...(draft.apiKey ? { apiKey: draft.apiKey } : {}),
          ...(draft.clearApiKey ? { clearApiKey: true } : {}),
        },
      ];
    })
  ) as Record<EmbeddedProviderProfileId, EmbeddedProviderProfileUpdate>;
}

const EmbeddedRuntimeSettingsModal: React.FC<
  EmbeddedRuntimeSettingsModalProps
> = ({ visible, onRequestClose, onSaved }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [configuration, setConfiguration] =
    useState<EmbeddedRuntimePublicConfiguration | null>(null);
  const [drafts, setDrafts] = useState<Record<
    EmbeddedProviderProfileId,
    ProfileDraft
  > | null>(null);
  const [defaultAgent, setDefaultAgent] = useState("reviewer-codex");
  const [status, setStatus] = useState<ValidationState>({
    tone: "idle",
    message: "",
  });
  const [validation, setValidation] = useState<
    Partial<Record<EmbeddedProviderProfileId, ValidationState>>
  >({});
  const [chatGPTDisplay, setChatGPTDisplay] =
    useState<ActionDisplayPayload | null>(null);
  const [chatGPTActionId, setChatGPTActionId] = useState<string | null>(null);
  const [chatGPTAuthState, setChatGPTAuthState] = useState<string | null>(
    null
  );
  const [chatGPTLoginDetails, setChatGPTLoginDetails] = useState<{
    url: string;
    code: string;
  } | null>(null);

  useEffect(() => {
    if (!visible) {
      return;
    }
    let active = true;
    setStatus({ tone: "busy", message: "Loading provider settings…" });
    void getEmbeddedPythonRuntimeConfiguration()
      .then((loaded) => {
        if (!active) return;
        setConfiguration(loaded);
        setDrafts(draftsFromConfiguration(loaded));
        setDefaultAgent(loaded.defaultAgent);
        setValidation({});
        setChatGPTDisplay(null);
        setChatGPTActionId(null);
        setChatGPTAuthState(null);
        setChatGPTLoginDetails(null);
        setStatus({ tone: "idle", message: "" });
      })
      .catch((error) => {
        if (!active) return;
        setStatus({
          tone: "error",
          message:
            error instanceof Error
              ? error.message
              : "Could not load embedded settings.",
        });
      });
    return () => {
      active = false;
    };
  }, [visible]);

  const updateDraft = (
    profileId: EmbeddedProviderProfileId,
    update: Partial<ProfileDraft>
  ): void => {
    setDrafts((current) =>
      current
        ? {
            ...current,
            [profileId]: { ...current[profileId], ...update },
          }
        : current
    );
  };

  const testProfile = async (
    profileId: EmbeddedProviderProfileId
  ): Promise<void> => {
    if (!drafts) return;
    setValidation((current) => ({
      ...current,
      [profileId]: { tone: "busy", message: "Testing…" },
    }));
    try {
      const result = await validateEmbeddedPythonRuntimeConfiguration({
        version: 3,
        defaultAgent,
        profileId,
        providers: updatesFromDrafts(drafts, profileId),
      });
      updateDraft(profileId, { enabled: true });
      setDefaultAgent(drafts[profileId].agentId);
      setValidation((current) => ({
        ...current,
        [profileId]: {
          tone: "success",
          message: `Connected to ${result.model}`,
        },
      }));
    } catch (error) {
      setValidation((current) => ({
        ...current,
        [profileId]: {
          tone: "error",
          message:
            error instanceof Error ? error.message : "Validation failed.",
        },
      }));
    }
  };

  const save = async (): Promise<void> => {
    if (!drafts) return;
    setStatus({ tone: "busy", message: "Saving provider settings…" });
    try {
      const saved = await configureEmbeddedPythonRuntime({
        version: 3,
        defaultAgent,
        providers: updatesFromDrafts(drafts),
      });
      setConfiguration(saved);
      setDrafts(draftsFromConfiguration(saved));
      setDefaultAgent(saved.defaultAgent);
      setStatus({ tone: "success", message: "Provider settings saved." });
      onSaved?.(saved);
    } catch (error) {
      setStatus({
        tone: "error",
        message:
          error instanceof Error ? error.message : "Could not save settings.",
      });
    }
  };

  const runChatGPTAction = async (
    actionId: string,
    options?: {
      pluginId?: string;
      actionOwner?: string;
      inputs?: Record<string, unknown>;
      preserveDisplay?: boolean;
    }
  ): Promise<void> => {
    setChatGPTActionId(actionId);
    try {
      const result = await executeEmbeddedRuntimeApplicationAction({
        pluginId: options?.pluginId ?? "chatgpt_auth",
        actionId,
        actionOwner: options?.actionOwner,
        inputs: options?.inputs,
      });
      if (options?.preserveDisplay !== true) {
        setChatGPTDisplay(result.display ?? null);
      }
      if (typeof result.auth_status?.state === "string") {
        setChatGPTAuthState(result.auth_status.state);
        if (
          result.auth_status.state === "pending" &&
          typeof result.auth_status.verification_url === "string" &&
          typeof result.auth_status.user_code === "string"
        ) {
          setChatGPTLoginDetails({
            url: result.auth_status.verification_url,
            code: result.auth_status.user_code,
          });
        } else {
          setChatGPTLoginDetails(null);
        }
      }
      setStatus({ tone: "idle", message: "" });
    } catch (error) {
      setStatus({
        tone: "error",
        message:
          error instanceof Error ? error.message : "ChatGPT action failed.",
      });
    } finally {
      setChatGPTActionId(null);
    }
  };

  const followChatGPTDisplayAction = async (
    action: ActionDisplayFollowupAction
  ): Promise<void> => {
    if (action.kind === "dismiss") {
      setChatGPTDisplay(null);
      return;
    }
    if (action.kind === "open_url") {
      await Linking.openURL(action.url);
      return;
    }
    if (action.kind === "copy_text") {
      Clipboard.setString(action.text);
      return;
    }
    if (action.kind === "run_action") {
      await runChatGPTAction(action.action_id, {
        pluginId: action.plugin,
        actionOwner: action.action_owner,
        inputs: action.fixed_params as Record<string, unknown> | undefined,
        preserveDisplay: action.preserve_display === true,
      });
    }
  };

  return (
    <PanelModalFrame
      visible={visible}
      testID="embedded-runtime-settings"
      title="On-device Provider Settings"
      subtitle="Keys stay in iOS Keychain. Test checks a candidate without replacing saved settings."
      onRequestClose={onRequestClose}
      statusText={status.message}
      statusTone={status.tone === "busy" ? "busy" : status.tone}
      showSpinner={status.tone === "busy"}
      scroll
      scrollTestID="embedded-runtime-settings-scroll"
      contentStyle={styles.modal}
    >
      {drafts && configuration ? (
        <>
          <View style={styles.profile} testID="embedded-openai-auth-settings">
            <Text style={styles.profileTitle}>OpenAI authentication</Text>
            <Text style={styles.profileMeta}>
              Choose the default for new OpenAI Responses sessions. Individual
              sessions can override it.
            </Text>
            <View style={styles.choiceRow}>
              {(["api", "chatgpt"] as const).map((authMode) => {
                const selected =
                  (drafts.openai.authMode ?? "api") === authMode;
                return (
                  <TouchableOpacity
                    key={authMode}
                    testID={`embedded-provider-openai-auth-${authMode}`}
                    style={[
                      styles.choiceButton,
                      selected && styles.choiceButtonSelected,
                    ]}
                    onPress={() =>
                      updateDraft("openai", { authMode })
                    }
                  >
                    <Text
                      style={[
                        styles.choiceButtonText,
                        selected && styles.choiceButtonTextSelected,
                      ]}
                    >
                      {authMode === "api" ? "API key" : "ChatGPT"}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
            <Text
              testID="embedded-provider-openai-auth-selected"
              style={styles.profileMeta}
            >
              Selected authentication: {drafts.openai.authMode ?? "api"}
            </Text>
            <Text
              testID="embedded-provider-openai-chatgpt-auth-state"
              style={styles.profileMeta}
            >
              ChatGPT status: {chatGPTAuthState ?? "not checked"}
            </Text>
            <View style={styles.chatGPTPanel}>
              <Text style={styles.label}>ChatGPT account</Text>
              {(drafts.openai.authMode ?? "api") !== "chatgpt" ? (
                <Text style={styles.profileMeta}>
                  Choose ChatGPT above to manage account login.
                </Text>
              ) : null}
              <View style={styles.actions}>
                {[
                  ["login_start", "Sign in with ChatGPT"],
                  ["check_status", "Check status"],
                  ["cancel_login", "Cancel"],
                  ["logout", "Log out"],
                ].map(([actionId, label]) => {
                  const disabled =
                    (drafts.openai.authMode ?? "api") !== "chatgpt" ||
                    chatGPTActionId !== null;
                  return (
                    <TouchableOpacity
                      key={actionId}
                      testID={`embedded-provider-openai-chatgpt-${actionId}`}
                      style={[
                        styles.secondaryButton,
                        disabled && styles.buttonDisabled,
                      ]}
                      disabled={disabled}
                      onPress={() => void runChatGPTAction(actionId)}
                    >
                      <Text style={styles.secondaryButtonText}>
                        {chatGPTActionId === actionId ? "Working…" : label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
              {chatGPTDisplay ? (
                <ActionDisplayCard
                  display={chatGPTDisplay}
                  activeActionId={chatGPTActionId}
                  bodyTestID="embedded-provider-openai-chatgpt-display"
                  onDismiss={() => setChatGPTDisplay(null)}
                  onFollowupAction={(action) =>
                    void followChatGPTDisplayAction(action)
                  }
                  compact
                  bounded
                />
              ) : null}
            </View>
            {(drafts.openai.authMode ?? "api") === "chatgpt" &&
            chatGPTLoginDetails ? (
              <View style={styles.chatGPTPanel}>
                <Text style={styles.profileMeta}>
                  Complete login in another browser:
                </Text>
                <Text
                  testID="embedded-provider-openai-chatgpt-login-url"
                  style={styles.profileMeta}
                  selectable
                >
                  {chatGPTLoginDetails.url}
                </Text>
                <Text
                  testID="embedded-provider-openai-chatgpt-login-code"
                  style={styles.profileMeta}
                  selectable
                >
                  {chatGPTLoginDetails.code}
                </Text>
              </View>
            ) : null}
          </View>
          {PROFILE_ORDER.map((profileId) => {
            const draft = drafts[profileId];
            const validationState = validation[profileId];
            const isDefault = defaultAgent === draft.agentId;
            return (
              <View
                key={profileId}
                style={styles.profile}
                testID={`embedded-provider-${profileId}`}
              >
                <View style={styles.profileHeader}>
                  <View style={styles.profileTitleGroup}>
                    <Text style={styles.profileTitle}>{draft.label}</Text>
                    <Text style={styles.profileMeta}>
                      {draft.agentId} · {draft.toolFamily}
                    </Text>
                  </View>
                  <Switch
                    testID={`embedded-provider-${profileId}-enabled`}
                    value={draft.enabled}
                    onValueChange={(enabled) =>
                      updateDraft(profileId, { enabled })
                    }
                  />
                </View>

                <TouchableOpacity
                  testID={`embedded-provider-${profileId}-default`}
                  style={[
                    styles.defaultButton,
                    isDefault && styles.defaultButtonSelected,
                  ]}
                  onPress={() => setDefaultAgent(draft.agentId)}
                >
                  <Text
                    style={[
                      styles.defaultButtonText,
                      isDefault && styles.defaultButtonTextSelected,
                    ]}
                  >
                    {isDefault ? "Default agent" : "Make default"}
                  </Text>
                </TouchableOpacity>

                <Text style={styles.label}>Base URL</Text>
                <TextInput
                  testID={`embedded-provider-${profileId}-base-url`}
                  style={styles.input}
                  value={draft.baseUrl}
                  onChangeText={(baseUrl) =>
                    updateDraft(profileId, { baseUrl })
                  }
                  autoCapitalize="none"
                  autoCorrect={false}
                />

                <Text style={styles.label}>Model</Text>
                <TextInput
                  testID={`embedded-provider-${profileId}-model`}
                  style={styles.input}
                  value={draft.model}
                  onChangeText={(model) => updateDraft(profileId, { model })}
                  autoCapitalize="none"
                  autoCorrect={false}
                />

                {profileId === "reviewer" ? (
                  <>
                    <Text style={styles.label}>TLS CA bundle path</Text>
                    <TextInput
                      testID="embedded-provider-reviewer-tls-ca-bundle"
                      style={styles.input}
                      value={draft.tlsCaBundle ?? ""}
                      onChangeText={(tlsCaBundle) =>
                        updateDraft(profileId, { tlsCaBundle })
                      }
                      placeholder="Optional custom CA certificate"
                      placeholderTextColor={theme.textSecondary}
                      autoCapitalize="none"
                      autoCorrect={false}
                    />
                  </>
                ) : null}

                {profileId !== "openai" ||
                (draft.authMode ?? "api") === "api" ? (
                  <>
                    <Text style={styles.label}>API key</Text>
                    <TextInput
                      testID={`embedded-provider-${profileId}-api-key`}
                      style={styles.input}
                      value={draft.apiKey}
                      onChangeText={(apiKey) =>
                        updateDraft(profileId, {
                          apiKey,
                          clearApiKey: apiKey ? false : draft.clearApiKey,
                        })
                      }
                      placeholder={
                        draft.hasApiKey && !draft.clearApiKey
                          ? "Saved in Keychain — leave blank to keep"
                          : "Enter API key"
                      }
                      placeholderTextColor={theme.textSecondary}
                      secureTextEntry
                      autoCapitalize="none"
                      autoCorrect={false}
                    />
                  </>
                ) : null}

                <View style={styles.actions}>
                  <TouchableOpacity
                    testID={`embedded-provider-${profileId}-test`}
                    style={styles.secondaryButton}
                    onPress={() => void testProfile(profileId)}
                  >
                    <Text style={styles.secondaryButtonText}>Test</Text>
                  </TouchableOpacity>
                  {draft.hasApiKey || draft.apiKey ? (
                    <TouchableOpacity
                      testID={`embedded-provider-${profileId}-clear-key`}
                      style={styles.clearButton}
                      onPress={() =>
                        updateDraft(profileId, {
                          apiKey: "",
                          clearApiKey: true,
                        })
                      }
                    >
                      <Text style={styles.clearButtonText}>
                        {draft.clearApiKey ? "Key will be removed" : "Remove key"}
                      </Text>
                    </TouchableOpacity>
                  ) : null}
                </View>
                {validationState ? (
                  <Text
                    testID={`embedded-provider-${profileId}-validation`}
                    style={[
                      styles.validation,
                      validationState.tone === "error"
                        ? styles.validationError
                        : validationState.tone === "success"
                        ? styles.validationSuccess
                        : null,
                    ]}
                  >
                    {validationState.message}
                  </Text>
                ) : null}
              </View>
            );
          })}
          <TouchableOpacity
            testID="embedded-runtime-settings-save"
            style={styles.saveButton}
            onPress={() => void save()}
          >
            <Text style={styles.saveButtonText}>Save Settings</Text>
          </TouchableOpacity>
        </>
      ) : null}
    </PanelModalFrame>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modal: {
      width: "94%",
      maxHeight: "90%",
    },
    profile: {
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 12,
      padding: 12,
      marginBottom: 12,
      backgroundColor: theme.surfaceAlt,
    },
    profileHeader: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 12,
    },
    profileTitleGroup: {
      flex: 1,
    },
    profileTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: "700",
    },
    profileMeta: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      marginTop: 2,
    },
    defaultButton: {
      alignSelf: "flex-start",
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 999,
      paddingHorizontal: 10,
      paddingVertical: 5,
      marginTop: 10,
    },
    defaultButtonSelected: {
      backgroundColor: theme.primary,
      borderColor: theme.primary,
    },
    defaultButtonText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.small,
      fontWeight: "600",
    },
    defaultButtonTextSelected: {
      color: theme.textOnPrimary,
    },
    label: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      fontWeight: "600",
      marginTop: 10,
      marginBottom: 4,
    },
    input: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      backgroundColor: theme.surface,
    },
    actions: {
      flexDirection: "row",
      flexWrap: "wrap",
      alignItems: "center",
      gap: 10,
      marginTop: 10,
    },
    chatGPTPanel: {
      gap: 10,
    },
    choiceRow: {
      flexDirection: "row",
      gap: 8,
      marginTop: 10,
    },
    choiceButton: {
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    choiceButtonSelected: {
      backgroundColor: theme.primary,
      borderColor: theme.primary,
    },
    choiceButtonText: {
      color: theme.text,
      fontWeight: "600",
    },
    choiceButtonTextSelected: {
      color: theme.textOnPrimary,
    },
    buttonDisabled: {
      opacity: 0.45,
    },
    secondaryButton: {
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 8,
      backgroundColor: theme.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
    },
    secondaryButtonText: {
      color: theme.primary,
      fontWeight: "700",
    },
    clearButton: {
      paddingHorizontal: 4,
      paddingVertical: 8,
    },
    clearButtonText: {
      color: theme.danger,
      fontWeight: "600",
    },
    validation: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      marginTop: 8,
    },
    validationError: {
      color: theme.danger,
    },
    validationSuccess: {
      color: theme.success,
    },
    saveButton: {
      alignItems: "center",
      borderRadius: 10,
      paddingHorizontal: 14,
      paddingVertical: 12,
      backgroundColor: theme.primary,
      marginBottom: 8,
    },
    saveButtonText: {
      color: theme.textOnPrimary,
      fontWeight: "700",
    },
  });

export default EmbeddedRuntimeSettingsModal;