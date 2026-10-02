import React, { useMemo, useState } from "react";
import { Pressable, Settings, StyleSheet, Text, View } from "react-native";
import {
  SafeAreaProvider,
  SafeAreaView,
} from "react-native-safe-area-context";

import type { AgentBackend, IndexedMessage, SessionSummary } from "@crystal-lattice/frontend-sdk";

import { ApplicationPluginsProvider } from "../ApplicationPluginsContext";
import { PinnedActionsProvider } from "../PinnedActionsContext";
import SessionChatScreen from "../SessionChatScreen";
import SessionsScreen from "../SessionsScreen";
import { HomeWorkspaceProvider } from "../HomeWorkspaceContext";
import GlobalDisplayLayer from "../components/GlobalDisplayLayer";
import SessionPluginsModal from "../components/SessionPluginsModal";
import SessionSettingsModal from "../components/SessionSettingsModal";
import SessionSnapshotsModal from "../components/SessionSnapshotsModal";
import { ThemeProvider, darkTheme, lightTheme, type Theme } from "../theme";
import codingPlanFixture from "./fixtures/websiteCodingPlanSession.json";
import runtimeUiFixture from "./fixtures/websiteRuntimeUi.json";

const SESSION_SUMMARY = codingPlanFixture.session as SessionSummary;
const SESSION_ID = SESSION_SUMMARY.session_id;
const MESSAGES = codingPlanFixture.messages as IndexedMessage[];
const SESSION_UI_SCHEMA = runtimeUiFixture.session_ui_schema;
const SESSION_APPLICATION_UI_SCHEMA =
  runtimeUiFixture.session_application_ui_schema;
const SESSION_CONFIG_SCHEMA = runtimeUiFixture.session_config_schema;
const SESSION_BASE_CONFIG = runtimeUiFixture.session_base_config;
const SESSION_OVERRIDES = runtimeUiFixture.session_overrides;
const SNAPSHOTS = runtimeUiFixture.snapshots;
const MESSAGE_FOOTER_ELEMENTS = runtimeUiFixture.message_footer_elements;
const PROVIDER_USAGE_MESSAGE =
  runtimeUiFixture.provider_usage_message as IndexedMessage;
const MOBILE_HERO_MESSAGES =
  runtimeUiFixture.mobile_hero_messages as IndexedMessage[];
const MOBILE_HERO_UI_SCHEMA = runtimeUiFixture.mobile_hero_ui_schema;

const PROVIDER_SETTINGS_SCHEMA = [
  {
    ui_type: "config",
    plugin: "openai_responses",
    type: "select",
    key: "auth_mode",
    label: "Authentication mode",
    options: [
      { value: "auto", label: "Automatic" },
      { value: "chatgpt", label: "ChatGPT" },
      { value: "api", label: "API key" },
    ],
    order: 10,
  },
  {
    ui_type: "config",
    plugin: "openai_responses",
    type: "checkbox",
    key: "enable_flex_processing",
    label: "Enable flex processing",
    order: 20,
  },
  {
    ui_type: "config",
    plugin: "openai_responses",
    type: "select",
    key: "reasoning_effort",
    label: "Reasoning effort",
    options: [
      { value: "medium", label: "Medium" },
      { value: "high", label: "High" },
    ],
    order: 30,
  },
];

const FEATURE_PLUGINS = [
  {
    id: "openai_responses_reasoning",
    kind: "features",
    name: "Reasoning controls",
    enabled: true,
    active: true,
    source: "agent",
  },
  {
    id: "openai_responses_prompt_caching",
    kind: "features",
    name: "Prompt caching",
    enabled: true,
    active: true,
    source: "agent",
  },
  {
    id: "openai_responses_web_search",
    kind: "features",
    name: "Web search",
    enabled: true,
    active: true,
    source: "agent",
  },
  {
    id: "openai_responses_native_compaction",
    kind: "features",
    name: "Native compaction",
    enabled: false,
    active: true,
    source: "session",
  },
];

const COMPILED_MESSAGES = [
  {
    index: 0,
    message: {
      role: "system",
      content: "You are a research and operations agent.",
      metadata: {
        compiled_content:
          "You are a research and operations agent.\n\nUse the configured source-reading, web research, and structured-output tools. Preserve citations, separate facts from recommendations, and produce an actionable brief.",
      },
    },
  },
] as IndexedMessage[];

const VIBE_MESSAGES = [
  {
    index: 0,
    message: {
      role: "system",
      content:
        "You are an operations research agent. Build a cited launch brief from the supplied source notes.",
      metadata: {},
    },
  },
  {
    index: 1,
    message: {
      role: "user",
      content:
        "Compare the three launch approaches in the attached notes. Identify assumptions, research gaps, risks, and a recommended two-week validation plan.",
      metadata: {},
    },
  },
  {
    index: 2,
    message: {
      role: "assistant",
      content: "",
      metadata: {
        reasoning:
          "**Planning a source-heavy comparison**\n**Separating evidence, assumptions, and validation steps**\n**Preparing a structured recommendation**",
        openai_responses_reasoning: {
          summary_text:
            "**Planning a source-heavy comparison**\n**Separating evidence, assumptions, and validation steps**\n**Preparing a structured recommendation**",
          context: "all_turns",
        },
        has_tool_calls: false,
        phase: "analysis",
      },
    },
  },
] as IndexedMessage[];

const WORKSPACE_SESSIONS: SessionSummary[] = [
  {
    session_id: "launch-research",
    modified: 30,
    preview: "Compare launch approaches and define the validation plan.",
    metadata: {
      title: "Launch strategy research",
      subtitle: "Sources, assumptions, and validation plan",
      status: "in_progress",
      pinned: true,
    },
    presentation: {
      title: "Launch strategy research",
      subtitle: "Sources, assumptions, and validation plan",
      meta: "Status: In progress",
    },
  },
  {
    session_id: "customer-signals",
    modified: 20,
    preview: "Synthesize the latest customer interview notes.",
    metadata: {
      title: "Customer signal synthesis",
      subtitle: "Interview themes and open questions",
      status: "todo",
      pinned: false,
    },
    presentation: {
      title: "Customer signal synthesis",
      subtitle: "Interview themes and open questions",
      meta: "Status: To do",
    },
  },
  {
    session_id: "release-brief",
    modified: 10,
    preview: "Final launch brief ready for review.",
    metadata: {
      title: "Release readiness brief",
      subtitle: "Decision, risks, owners, and next steps",
      status: "done",
      pinned: false,
    },
    presentation: {
      title: "Release readiness brief",
      subtitle: "Decision, risks, owners, and next steps",
      meta: "Status: Done",
    },
  },
];

function createHarnessBackend(kind: string): AgentBackend {
  const displayedMessages =
    kind === "usage"
      ? [PROVIDER_USAGE_MESSAGE]
      : kind === "compiled"
        ? COMPILED_MESSAGES
        : kind === "vibe"
          ? VIBE_MESSAGES
      : kind === "hero"
        ? MOBILE_HERO_MESSAGES
        : MESSAGES;
  return {
    kind: "inProcess",
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: true,
      sessionConfigOverrides: true,
      sessionPlugins: kind === "plugins",
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: async () => ["codex-openai"],
    listSessions: async () => [SESSION_SUMMARY],
    getSessionSummary: async () => SESSION_SUMMARY,
    getSessionAgent: async () => "codex-openai",
    switchSessionAgent: async () => {},
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => [],
    listMessages: async () => ({
      messages: displayedMessages,
      cursorEventId: "0",
      activeRequestId: null,
    }),
    getLatestEventId: async () => "0",
    listEvents: async () => ({
      events: [],
      latestEventId: "0",
      cursorExpired: false,
    }),
    getSessionUiSchema: async () =>
      kind === "usage"
        ? MESSAGE_FOOTER_ELEMENTS
        : kind === "provider-settings"
          ? PROVIDER_SETTINGS_SCHEMA
        : kind === "hero"
          ? MOBILE_HERO_UI_SCHEMA
          : SESSION_UI_SCHEMA,
    getSessionApplicationUiSchema: async () =>
      kind === "hero" ? [] : SESSION_APPLICATION_UI_SCHEMA,
    getSessionOverrides: async () =>
      kind === "provider-settings"
        ? {}
        : SESSION_OVERRIDES,
    getSessionConfigSchema: async () =>
      kind === "provider-settings"
        ? [
            { key: "auth_mode", type: "string", default: "auto" },
            {
              key: "enable_flex_processing",
              type: "boolean",
              default: true,
            },
            {
              key: "reasoning_effort",
              type: "string",
              default: "medium",
            },
          ]
        : SESSION_CONFIG_SCHEMA,
    getSessionBaseConfig: async () =>
      kind === "provider-settings"
        ? {
            auth_mode: "auto",
            enable_flex_processing: true,
            reasoning_effort: "medium",
          }
        : SESSION_BASE_CONFIG,
    listSessionPlugins: async () => FEATURE_PLUGINS,
    setSessionPlugins: async () => {},
    clearSessionPlugins: async () => {},
    listSessionSnapshots: async () =>
      SNAPSHOTS.map((snapshot) => ({
        ...snapshot,
        session_id: SESSION_ID,
      })),
    getSelectedSessionSnapshot: async () => null,
    listSessionNotifications: async () => [],
    listApplicationNotifications: async () => [],
    patchSessionOverrides: async () => {},
    deleteSessionOverride: async () => {},
  } as unknown as AgentBackend;
}

function createWorkspaceBackend(): AgentBackend {
  const statusOptions = [
    { value: "todo", label: "To do", icon: "circle", tone: "muted" },
    {
      value: "in_progress",
      label: "In progress",
      icon: "clock",
      tone: "primary",
    },
    { value: "blocked", label: "Blocked", icon: "alert-circle", tone: "danger" },
    { value: "done", label: "Done", icon: "check-circle", tone: "success" },
  ];
  return {
    kind: "inProcess",
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: async () => ["codex-openai"],
    listSessions: async () => WORKSPACE_SESSIONS,
    getSessionSummary: async (sessionId: string) =>
      WORKSPACE_SESSIONS.find(session => session.session_id === sessionId) ??
      WORKSPACE_SESSIONS[0],
    listApplicationActions: async () => [
      {
        plugin: "session_status",
        id: "set_session_status",
        label: "Set session status",
        inputs: {
          session_id: { type: "string", required: true },
          status: { type: "string", required: true },
        },
      },
      {
        plugin: "session_pinned",
        id: "toggle_session_pinned",
        label: "Pin/unpin session",
        inputs: { session_id: { type: "string", required: true } },
      },
      {
        plugin: "session_title",
        id: "set_session_title",
        label: "Set session title",
        inputs: {
          session_id: { type: "string", required: true },
          title: { type: "string", required: false },
          subtitle: { type: "string", required: false },
        },
      },
    ],
    listApplicationUiSchema: async () => [
      {
        ui_type: "session_list_field",
        plugin: "session_title",
        id: "session_title_field",
        role: "title",
        data: "metadata.title",
        template: "{{data}}",
        order: 0,
      },
      {
        ui_type: "session_list_field",
        plugin: "session_title",
        id: "session_subtitle_field",
        role: "subtitle",
        data: "metadata.subtitle",
        template: "{{data}}",
        order: 0,
      },
      {
        ui_type: "session_list_field",
        plugin: "session_status",
        id: "session_status_meta",
        role: "meta",
        data: "session_status_label",
        template: "Status: {{data}}",
        order: 100,
      },
      {
        ui_type: "session_list_action",
        plugin: "session_pinned",
        id: "toggle_session_pinned",
        label: "Pin/unpin session",
        icon: "star",
        order: 10,
        action_id: "toggle_session_pinned",
        param_map: { session_id: "$session.session_id" },
        dialog: { kind: "none" },
        rich_ui: {
          kind: "toggle",
          value_path: "metadata.pinned",
          missing_value: false,
          active_value: true,
          default_pinned: true,
          placements: ["header_trailing", "actions_bar"],
          appearance: {
            active: { tone: "highlight" },
            inactive: { tone: "muted" },
          },
        },
      },
      {
        ui_type: "session_list_action",
        plugin: "session_status",
        id: "set_session_status",
        label: "Set status",
        icon: "circle",
        order: 30,
        action_id: "set_session_status",
        param_map: {
          session_id: "$session.session_id",
          status: "$dialog.status",
        },
        dialog: {
          kind: "form",
          inputs: [
            {
              name: "status",
              type: "select",
              label: "Status",
              options: statusOptions,
            },
          ],
        },
        rich_ui: {
          kind: "list",
          value_path: "metadata.status",
          missing_value: "todo",
          input_name: "status",
          default_pinned: false,
          options: statusOptions,
        },
      },
    ],
    executeAction: async () => ({
      status: "ok",
      plugin: "website_visual",
      action_id: "noop",
      result: {},
    }),
    executeSessionAction: async () => ({
      status: "ok",
      plugin: "website_visual",
      action_id: "noop",
      result: {},
    }),
  } as unknown as AgentBackend;
}

function MobileWorkspaceVisual({
  theme,
}: {
  theme: Theme;
}): React.JSX.Element {
  const backend = useMemo(() => createWorkspaceBackend(), []);
  return (
    <ThemeProvider theme={theme}>
      <PinnedActionsProvider>
        <HomeWorkspaceProvider>
          <ApplicationPluginsProvider
            backend={backend}
            connectionId="website-workspaces"
          >
            <View
              style={[styles.root, { backgroundColor: theme.background }]}
              testID="website-workspaces-ready"
            >
              <SessionsScreen
                backend={backend}
                connectionId="website-workspaces"
                connectionName="Research workspace"
                cachedSessions={WORKSPACE_SESSIONS}
                lastLoadedAt={1}
                isActive
                onUpdateCache={() => {}}
                onSelectSession={() => {}}
              />
            </View>
          </ApplicationPluginsProvider>
        </HomeWorkspaceProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
  );
}

export interface MobileWebsiteVisualHarnessProps {
  clcWebsiteVisualTheme?: string;
  clcWebsiteVisualKind?: string;
}

export function MobileWebsiteVisualHarness({
  clcWebsiteVisualTheme,
  clcWebsiteVisualKind,
}: MobileWebsiteVisualHarnessProps): React.JSX.Element {
  const [visualOpen, setVisualOpen] = useState(false);
  const configuredTheme =
    clcWebsiteVisualTheme ?? Settings.get("clcWebsiteVisualTheme");
  const configuredKind =
    clcWebsiteVisualKind ??
    Settings.get("clcWebsiteVisualKind") ??
    "settings";
  const backend = useMemo(
    () => createHarnessBackend(configuredKind),
    [configuredKind],
  );
  const theme: Theme = configuredTheme === "dark" ? darkTheme : lightTheme;

  if (configuredKind === "workspaces") {
    return <MobileWorkspaceVisual theme={theme} />;
  }

  if (!visualOpen) {
    return (
      <SafeAreaProvider>
        <ThemeProvider theme={theme}>
          <SafeAreaView
            style={[styles.root, { backgroundColor: theme.background }]}
            edges={["top", "left", "right"]}
            testID="website-visual-harness-ready"
          >
            <View style={styles.launchControl}>
              <Pressable
                testID={`website-visual-open-${configuredKind}`}
                style={styles.launchButton}
                onPress={() => setVisualOpen(true)}
              >
                <Text style={styles.launchButtonText}>
                  Open {configuredKind} visual
                </Text>
              </Pressable>
            </View>
          </SafeAreaView>
        </ThemeProvider>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <ThemeProvider theme={theme}>
        <SafeAreaView
          style={[styles.root, { backgroundColor: theme.background }]}
          edges={["top", "left", "right"]}
          testID="website-visual-harness-ready"
        >
          <PinnedActionsProvider>
            <ApplicationPluginsProvider
              backend={backend}
              connectionId="website-visual"
            >
              <GlobalDisplayLayer backend={backend} connectionId="website-visual">
                <View style={styles.screen}>
                  <SessionChatScreen
                  backend={backend}
                  connectionId="website-visual"
                  isActive={
                    configuredKind === "actions" ||
                    configuredKind === "usage" ||
                    configuredKind === "hero" ||
                    configuredKind === "compiled" ||
                    configuredKind === "vibe"
                  }
                  sessionId={SESSION_ID}
                  sessionSummary={SESSION_SUMMARY}
                  cachedMessages={
                    configuredKind === "usage"
                      ? [PROVIDER_USAGE_MESSAGE]
                      : configuredKind === "compiled"
                        ? COMPILED_MESSAGES
                        : configuredKind === "vibe"
                          ? VIBE_MESSAGES
                      : configuredKind === "hero"
                        ? MOBILE_HERO_MESSAGES
                      : MESSAGES
                  }
                  lastLoadedAt={1}
                  cachedEventsCursorId="0"
                  cachedActiveRequestId={null}
                  onUpdateCache={() => {}}
                  onUpdateSessionSummaries={() => {}}
                  onBack={() => {}}
                  onNavigateToSession={() => {}}
                  initialComposeText=""
                  initialScrollAnchor={null}
                  initialRangeStartText="-50"
                  initialRangeEndText=""
                  onSaveComposeText={() => {}}
                  onSaveScrollAnchor={() => {}}
                  onSaveHistoryRange={() => {}}
                  debugTimeline={[]}
                  onAppendDebugTimelineEntry={() => {}}
                  />
                  {configuredKind === "actions" ||
                  configuredKind === "usage" ||
                  configuredKind === "hero" ||
                  configuredKind === "compiled" ||
                  configuredKind === "vibe" ? null : configuredKind === "snapshots" ? (
                  <SessionSnapshotsModal
                    visible
                    snapshotsLoading={false}
                    snapshotItems={SNAPSHOTS}
                    selectedSnapshotId="automatic-compaction"
                    onRequestClose={() => {}}
                    onCreateSnapshot={() => {}}
                    onClearSelectedSnapshot={() => {}}
                    onSelectSnapshot={() => {}}
                    onRestoreSnapshot={() => {}}
                    onDeleteSnapshot={() => {}}
                  />
                ) : configuredKind === "plugins" ? (
                  <SessionPluginsModal
                    backend={backend}
                    sessionId={SESSION_ID}
                    visible
                    onRequestClose={() => {}}
                  />
                ) : (
                  <SessionSettingsModal
                    backend={backend}
                    cacheKey={`website-visual-${
                      configuredTheme === "dark" ? "dark" : "light"
                    }`}
                    sessionId={SESSION_ID}
                    visible
                    onRequestClose={() => {}}
                  />
                  )}
                </View>
              </GlobalDisplayLayer>
            </ApplicationPluginsProvider>
          </PinnedActionsProvider>
        </SafeAreaView>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  screen: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  launchControl: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  launchButton: {
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: "#007AFF",
  },
  launchButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
