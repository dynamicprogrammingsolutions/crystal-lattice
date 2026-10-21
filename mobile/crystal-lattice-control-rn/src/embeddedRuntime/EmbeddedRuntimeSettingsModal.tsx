import React, { useEffect, useMemo, useRef, useState } from "react";
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
import {
  runApplicationAction,
  type AgentBackend,
  type ActionUiElement,
  type ActionDisplayFollowupAction,
  type ActionDisplayPayload,
} from "@crystal-lattice/frontend-sdk";
import { useDisplayFollowupDialog } from "@crystal-lattice/frontend-sdk-react";
import { ApplicationActionDialog } from "@crystal-lattice/frontend-rn-components";
import { useMobileApplicationActionDialogFieldRenderers } from "../components/applicationActionDialogRenderers";

import OpenAIAuthenticationSettings from "./OpenAIAuthenticationSettings";
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
    Object.entries(configuration.providers).map(([profileId, profile]) => [
      profileId,
      {
        ...profile,
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
    Object.entries(drafts).map(([rawProfileId, draft]) => {
      const profileId = rawProfileId as EmbeddedProviderProfileId;
      return [
        profileId,
        {
          enabled: profileId === forceEnabledProfile ? true : draft.enabled,
          ...(profileId !== "reviewer"
            ? {
                baseUrl: draft.baseUrl.trim(),
                model: draft.model.trim(),
              }
            : {}),
          ...(profileId === "openai"
            ? { authMode: draft.authMode ?? "api" }
            : {}),
          ...(draft.apiKey ? { apiKey: draft.apiKey } : {}),
          ...(draft.clearApiKey ? { clearApiKey: true } : {}),
        },
      ];
    })
  ) as Record<EmbeddedProviderProfileId, EmbeddedProviderProfileUpdate>;
}

function configurationFromDrafts(
  drafts: Record<EmbeddedProviderProfileId, ProfileDraft>
) {
  return {
    version: 3 as const,
    providers: updatesFromDrafts(drafts),
  };
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
  const autosaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const autosaveQueueRef = useRef<Promise<void>>(Promise.resolve());
  const lastAutosavePayloadRef = useRef("");
  const latestDraftsRef = useRef(drafts);
  latestDraftsRef.current = drafts;

  useEffect(() => {
    if (!visible) {
      return;
    }
    let active = true;
    setStatus({ tone: "busy", message: "Loading provider settings…" });
    void getEmbeddedPythonRuntimeConfiguration()
      .then((loaded) => {
        if (!active) return;
        const loadedDrafts = draftsFromConfiguration(loaded);
        lastAutosavePayloadRef.current = JSON.stringify(
          configurationFromDrafts(loadedDrafts)
        );
        setConfiguration(loaded);
        setDrafts(loadedDrafts);
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
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current);
        autosaveTimerRef.current = null;
      }
    };
  }, [visible]);

  useEffect(() => {
    if (!visible || !drafts || !configuration) {
      return;
    }
    const payload = configurationFromDrafts(drafts);
    const serialized = JSON.stringify(payload);
    if (serialized === lastAutosavePayloadRef.current) {
      return;
    }
    if (autosaveTimerRef.current) {
      clearTimeout(autosaveTimerRef.current);
    }
    autosaveTimerRef.current = setTimeout(() => {
      autosaveTimerRef.current = null;
      autosaveQueueRef.current = autosaveQueueRef.current
        .catch(() => undefined)
        .then(async () => {
          setStatus({ tone: "busy", message: "Saving provider settings…" });
          try {
            const saved = await configureEmbeddedPythonRuntime(payload);
            lastAutosavePayloadRef.current = serialized;
            setConfiguration(saved);
            setDrafts((current) => {
              if (!current) return current;
              const currentSerialized = JSON.stringify(
                configurationFromDrafts(current)
              );
              const saveWasLatest = currentSerialized === serialized;
              const next = Object.fromEntries(
                Object.keys(current).map((rawProfileId) => {
                  const profileId =
                    rawProfileId as EmbeddedProviderProfileId;
                  return [
                  profileId,
                  {
                    ...current[profileId],
                    enabled: saveWasLatest ? saved.providers[profileId].enabled : current[profileId].enabled,
                    hasApiKey: saved.providers[profileId].hasApiKey,
                    apiKey:
                      saveWasLatest &&
                      payload.providers[profileId]?.apiKey ===
                        current[profileId].apiKey
                        ? ""
                        : current[profileId].apiKey,
                    clearApiKey: saveWasLatest ? false : current[profileId].clearApiKey,
                  },
                  ];
                })
              ) as Record<EmbeddedProviderProfileId, ProfileDraft>;
              if (saveWasLatest) {
                lastAutosavePayloadRef.current = JSON.stringify(
                  configurationFromDrafts(next)
                );
              }
              return next;
            });
            setStatus({
              tone: "success",
              message: "Provider settings saved.",
            });
            onSaved?.(saved);
          } catch (error) {
            setStatus({
              tone: "error",
              message:
                error instanceof Error
                  ? error.message
                  : "Could not save settings.",
            });
          }
        });
    }, 450);
    return () => {
      if (autosaveTimerRef.current) {
        clearTimeout(autosaveTimerRef.current);
        autosaveTimerRef.current = null;
      }
    };
  }, [
    configuration,
    drafts,
    onSaved,
    visible,
  ]);

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
        profileId,
        providers: updatesFromDrafts(drafts, profileId),
      });
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

  const runChatGPTAction = async (
    actionId: string,
    options?: {
      pluginId?: string;
      actionOwner?: string;
      inputs?: Record<string, unknown>;
      preserveDisplay?: boolean;
      element?: ActionUiElement;
      dialogValues?: Record<string, any>;
      formValues?: Record<string, any>;
    }
  ): Promise<void> => {
    setChatGPTActionId(actionId);
    try {
      const execute = (inputs?: Record<string, unknown>) => executeEmbeddedRuntimeApplicationAction({
        pluginId: options?.pluginId ?? "chatgpt_auth",
        actionId,
        actionOwner: options?.actionOwner,
        inputs,
      });
      const actionResult = options?.element ? await runApplicationAction({
        backend: {
          executeAction: async ({ inputs }: { inputs: Record<string, unknown> }) => ({
            status: "ok",
            plugin: options.pluginId ?? "chatgpt_auth",
            action_id: actionId,
            result: await execute(inputs),
          }),
        } as unknown as AgentBackend,
        element: options.element,
        actionsById: {},
        context: { dialogValues: options.dialogValues, formValues: options.formValues },
      }) : null;
      const result = actionResult
        ? actionResult.response?.result
        : await execute(options?.inputs);
      if (!result) {
        throw new Error(actionResult?.errorMessage || "Action failed.");
      }
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

  const actionFieldRenderers = useMobileApplicationActionDialogFieldRenderers();
  const displayFollowupDialog = useDisplayFollowupDialog<null>(
    async (element, { action, formValues }, dialogValues) => {
      await runChatGPTAction(action.action_id, {
        pluginId: action.plugin,
        actionOwner: action.action_owner,
        element,
        formValues,
        dialogValues,
        preserveDisplay: action.preserve_display === true,
      });
    }
  );

  const followChatGPTDisplayAction = async (
    action: ActionDisplayFollowupAction,
    formValues?: Record<string, any>
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
      if (chatGPTDisplay) {
        displayFollowupDialog.openForAction(action, chatGPTDisplay, null, formValues);
      }
    }
  };

  const renderApiKeyField = (profileId: EmbeddedProviderProfileId) => {
    const draft = drafts![profileId];
    return (
      <View testID={`embedded-provider-${profileId}-api-key-field`}>
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
          placeholder={draft.hasApiKey && !draft.clearApiKey
            ? "Saved in Keychain — leave blank to keep" : "Enter API key"}
          placeholderTextColor={theme.textSecondary}
          secureTextEntry
          autoCapitalize="none"
          autoCorrect={false}
        />
        {draft.hasApiKey || draft.apiKey ? (
          <TouchableOpacity
            testID={`embedded-provider-${profileId}-clear-key`}
            style={styles.clearButton}
            onPress={() => updateDraft(profileId, { apiKey: "", clearApiKey: true })}
          >
            <Text style={styles.clearButtonText}>
              {draft.clearApiKey ? "Key will be removed" : "Remove key"}
            </Text>
          </TouchableOpacity>
        ) : null}
      </View>
    );
  };

  const closeSettings = async () => {
    if (autosaveTimerRef.current) {
      clearTimeout(autosaveTimerRef.current);
      autosaveTimerRef.current = null;
    }
    await autosaveQueueRef.current;
    const current = latestDraftsRef.current;
    if (current) {
      const payload = configurationFromDrafts(current);
      if (JSON.stringify(payload) !== lastAutosavePayloadRef.current) {
        try {
          setStatus({ tone: "busy", message: "Saving provider settings…" });
          const saved = await configureEmbeddedPythonRuntime(payload);
          onSaved?.(saved);
        } catch (error) {
          setStatus({
            tone: "error",
            message: error instanceof Error ? error.message : "Could not save settings.",
          });
          return;
        }
      }
    }
    onRequestClose();
  };

  return (
    <PanelModalFrame
      visible={visible}
      testID="embedded-runtime-settings"
      title="Local provider settings"
      subtitle="Changes save automatically. Keys stay in iOS Keychain. Test validates without saving."
      onRequestClose={displayFollowupDialog.activeElement
        ? displayFollowupDialog.handleCancel : () => void closeSettings()}
      statusText={status.message}
      statusTone={status.tone === "busy" ? "busy" : status.tone}
      showSpinner={status.tone === "busy"}
      scroll
      scrollTestID="embedded-runtime-settings-scroll"
      contentStyle={styles.modal}
      overlayChildren={displayFollowupDialog.activeElement ? (
        <ApplicationActionDialog
          visible
          presentationMode="overlay"
          dialog={displayFollowupDialog.activeElement.dialog}
          titleFallback={displayFollowupDialog.activeElement.label}
          fieldRenderers={actionFieldRenderers}
          onSubmit={displayFollowupDialog.handleSubmit}
          onCancel={displayFollowupDialog.handleCancel}
        />
      ) : null}
    >
      {drafts && configuration ? (
        <>
          <View testID="embedded-provider-list">
            {configuration.profileOrder.filter(
              (profileId) => profileId !== "reviewer" || configuration.reviewerVisible
            ).map((profileId) => {
              const draft = drafts[profileId];
              const validationState = validation[profileId];
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
                    <View
                      testID={`embedded-provider-${profileId}-enabled`}
                      accessible
                      accessibilityRole="switch"
                      accessibilityLabel={`Enable ${draft.label}`}
                      accessibilityState={{ checked: draft.enabled }}
                      accessibilityActions={[
                        {
                          name: "activate",
                          label: draft.enabled
                            ? "Disable provider"
                            : "Enable provider",
                        },
                      ]}
                      onAccessibilityAction={(event) => {
                        if (event.nativeEvent.actionName === "activate") {
                          updateDraft(profileId, { enabled: !draft.enabled });
                        }
                      }}
                    >
                      <Switch
                        testID={`embedded-provider-${profileId}-enabled-control`}
                        value={draft.enabled}
                        onValueChange={(enabled) =>
                          updateDraft(profileId, { enabled })
                        }
                        accessible={false}
                      />
                    </View>
                </View>

                {profileId !== "reviewer" ? (
                  <>
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

                    <Text style={styles.label}>Default model</Text>
                    <TextInput
                      testID={`embedded-provider-${profileId}-model`}
                      style={styles.input}
                      value={draft.model}
                      onChangeText={(model) =>
                        updateDraft(profileId, { model })
                      }
                      autoCapitalize="none"
                      autoCorrect={false}
                    />
                  </>
                ) : null}

                {profileId === "openai" ? (
                  <OpenAIAuthenticationSettings
                    authMode={draft.authMode ?? "api"}
                    onAuthModeChanged={(authMode) => updateDraft("openai", { authMode })}
                    apiKeyField={renderApiKeyField(profileId)}
                    authState={chatGPTAuthState}
                    activeActionId={chatGPTActionId}
                    display={chatGPTDisplay}
                    loginDetails={chatGPTLoginDetails}
                    onRunAction={(actionId) => void runChatGPTAction(actionId)}
                    onDismissDisplay={() => setChatGPTDisplay(null)}
                    onFollowupAction={(action, formValues) =>
                      void followChatGPTDisplayAction(action, formValues)}
                    fieldRenderers={actionFieldRenderers}
                  />
                ) : renderApiKeyField(profileId)}

                <View style={styles.actions}>
                  <TouchableOpacity
                    testID={`embedded-provider-${profileId}-test`}
                    style={styles.secondaryButton}
                    onPress={() => void testProfile(profileId)}
                    accessibilityRole="button"
                    accessibilityLabel={`Test ${draft.label} provider`}
                    accessibilityActions={[
                      { name: "activate", label: "Test provider" },
                    ]}
                    onAccessibilityAction={(event) => {
                      if (event.nativeEvent.actionName === "activate") {
                        void testProfile(profileId);
                      }
                    }}
                  >
                    <Text style={styles.secondaryButtonText}>Test</Text>
                  </TouchableOpacity>
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
          </View>
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
  });

export default EmbeddedRuntimeSettingsModal;