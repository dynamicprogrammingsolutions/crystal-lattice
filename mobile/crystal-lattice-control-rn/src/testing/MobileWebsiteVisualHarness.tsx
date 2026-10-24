import React, { useMemo, useState } from "react";
import { Pressable, Settings, StyleSheet, Text, View } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";

import type {
  AgentBackend,
  ConnectionRecord,
  IndexedMessage,
  KeyValueStore,
  SessionRequestStatus,
  SessionSummary,
} from "@crystal-lattice/frontend-sdk";

import { ApplicationPluginsProvider } from "../ApplicationPluginsContext";
import type { SessionsCache } from "../../App";
import HomeScreen from "../HomeScreen";
import { PinnedActionsProvider } from "../PinnedActionsContext";
import SessionChatScreen from "../SessionChatScreen";
import SessionsScreen from "../SessionsScreen";
import { HomeWorkspaceProvider } from "../HomeWorkspaceContext";
import {
  HOME_WATCHLIST_STORAGE_KEY,
  MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY,
  SESSION_NOTES_STORAGE_KEY,
} from "../homeWorkspaceState";
import ActionResultModal from "../components/ActionResultModal";
import GlobalDisplayLayer from "../components/GlobalDisplayLayer";
import SessionPluginsModal from "../components/SessionPluginsModal";
import SessionSettingsModal from "../components/SessionSettingsModal";
import SessionSnapshotsModal from "../components/SessionSnapshotsModal";
import { ThemeProvider, darkTheme, lightTheme, type Theme } from "../theme";
import codingPlanFixture from "./fixtures/websiteCodingPlanSession.json";
import actionDisplayFixture from "./fixtures/websiteActionDisplays.json";
import runtimeUiFixture from "./fixtures/websiteRuntimeUi.json";
import vibeMessages from "./fixtures/websiteVibeMessages.json";

const SESSION_SUMMARY = codingPlanFixture.session as SessionSummary;
const SESSION_ID = SESSION_SUMMARY.session_id;
const COMPOSER_SESSION_ID = "starlette-compatibility";
const COMPOSER_SESSION_SUMMARY: SessionSummary = {
  ...SESSION_SUMMARY,
  session_id: COMPOSER_SESSION_ID,
};
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
const COMPILED_ACTION_FIXTURE = actionDisplayFixture.compiled_system_message;
const COST_ACTION_FIXTURE = actionDisplayFixture.cost_report;

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

const VIBE_MESSAGES = vibeMessages as IndexedMessage[];

const VIBE_SESSION_SUMMARY: SessionSummary = {
  session_id: SESSION_ID,
  modified: SESSION_SUMMARY.modified,
  preview: VIBE_MESSAGES[1].message.content,
  metadata: {
    agent_id: "zai",
    status: "in_progress",
    title: "Validate a launch plan",
    subtitle: "GLM-5.3 Flash · Z.ai · Research operations",
  },
  presentation: {
    title: "Validate a launch plan",
    subtitle: "GLM-5.3 Flash · Z.ai · Research operations",
    meta: "Status: In progress",
  },
};

const SYSTEM_TEMPLATE_MESSAGES: IndexedMessage[] = [
  {
    index: 0,
    message: {
      role: "system",
      content:
        "You are {{AGENT_TITLE}}. Follow the project guidance below before acting.\n\n{{PROJECT_GUIDANCE}}\n\nUse the enabled {{TOOLSET_NAME}} tools and report assumptions explicitly.",
      metadata: {},
    },
  },
  {
    index: 1,
    message: {
      role: "user",
      content:
        "Review the release notes and propose the smallest safe validation plan.",
      metadata: {},
    },
  },
];

const SYSTEM_TEMPLATE_SUMMARY: SessionSummary = {
  session_id: SESSION_ID,
  modified: SESSION_SUMMARY.modified,
  preview: SYSTEM_TEMPLATE_MESSAGES[1].message.content,
  metadata: {
    agent_id: "codex-openai",
    status: "in_progress",
  },
  presentation: {
    title: "Validate a release plan",
    subtitle: "Authored instructions remain visible",
    meta: "Status: In progress",
  },
};

const FIXTURE_NOW_SECONDS = Math.floor(Date.now() / 1000);
const WORKSPACE_PRIMARY_SESSION_ID = "starlette-compatibility";

const WORKSPACE_SESSIONS: SessionSummary[] = [
  {
    session_id: WORKSPACE_PRIMARY_SESSION_ID,
    modified: FIXTURE_NOW_SECONDS - 30,
    preview: SESSION_SUMMARY.preview,
    metadata: {
      agent_id: "codex-openai",
      title: SESSION_SUMMARY.presentation?.title,
      subtitle: SESSION_SUMMARY.presentation?.subtitle,
      status: "in_progress",
      pinned: true,
    },
    presentation: {
      title:
        SESSION_SUMMARY.presentation?.title ??
        "Plan a Starlette compatibility fix",
      subtitle:
        SESSION_SUMMARY.presentation?.subtitle ??
        "Coding session · OpenAI Responses",
      meta: "Status: In progress",
    },
  },
  {
    session_id: "customer-signals",
    modified: FIXTURE_NOW_SECONDS - 120,
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
    modified: FIXTURE_NOW_SECONDS - 360,
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

const WORKSPACE_REQUEST_STATUSES: Record<string, SessionRequestStatus> = {
  [WORKSPACE_PRIMARY_SESSION_ID]: {
    session_id: WORKSPACE_PRIMARY_SESSION_ID,
    request_id: "request-starlette-compatibility",
    state: "running",
    basis: "active_request",
    session_modified: 30,
  },
  "customer-signals": {
    session_id: "customer-signals",
    request_id: null,
    state: "not_started",
    basis: "session_tail",
    session_modified: 20,
  },
  "release-brief": {
    session_id: "release-brief",
    request_id: "request-release-brief",
    state: "succeeded",
    basis: "session_tail",
    session_modified: 10,
  },
};

const HOME_CONNECTIONS: ConnectionRecord[] = [
  {
    id: "local-workspace",
    kind: "manual",
    name: "Local workspace",
    host: "127.0.0.1",
    port: 9000,
    lastUsedAt: 2,
  },
  {
    id: "remote-workspace",
    kind: "bridge",
    name: "Remote workspace",
    bridgeUrl: "wss://bridge.example/ws/websocket",
    serverId: "review-runtime",
    serverName: "Review runtime",
    pairingToken: "website-review-token",
    lastUsedAt: 1,
  },
];

const HOME_SESSIONS_CACHE: SessionsCache = {
  "local-workspace": {
    connectionId: "local-workspace",
    lastLoadedAt: Date.now(),
    sessions: WORKSPACE_SESSIONS.slice(0, 2),
  },
  "remote-workspace": {
    connectionId: "remote-workspace",
    lastLoadedAt: Date.now(),
    sessions: [WORKSPACE_SESSIONS[2]],
  },
};

const HOME_STATUSES: Record<string, Record<string, SessionRequestStatus>> = {
  "local-workspace": {
    [WORKSPACE_PRIMARY_SESSION_ID]:
      WORKSPACE_REQUEST_STATUSES[WORKSPACE_PRIMARY_SESSION_ID],
    "customer-signals": WORKSPACE_REQUEST_STATUSES["customer-signals"],
  },
  "remote-workspace": {
    "release-brief": WORKSPACE_REQUEST_STATUSES["release-brief"],
  },
};

const HOME_VISUAL_STORE: KeyValueStore = {
  get: async (key: string) => {
    if (key === HOME_WATCHLIST_STORAGE_KEY) {
      return JSON.stringify([
        {
          connectionId: "local-workspace",
          sessionId: WORKSPACE_PRIMARY_SESSION_ID,
        },
        { connectionId: "local-workspace", sessionId: "customer-signals" },
        { connectionId: "remote-workspace", sessionId: "release-brief" },
      ]);
    }
    if (key === SESSION_NOTES_STORAGE_KEY) {
      return JSON.stringify({
        [WORKSPACE_PRIMARY_SESSION_ID]:
          "Compare the evidence before recommending a launch.",
      });
    }
    if (key === MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY) {
      return JSON.stringify({
        recentSessionsWindow: "1w",
        timeTrackingEnabled: false,
        timeTrackingPluginId: "human_time",
      });
    }
    return null;
  },
  set: async () => {},
  delete: async () => {},
};

function createHarnessBackend(kind: string): AgentBackend {
  const displayedMessages =
    kind === "usage" || kind === "cost"
      ? [PROVIDER_USAGE_MESSAGE]
      : kind === "system-template"
      ? SYSTEM_TEMPLATE_MESSAGES
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
    listAgents: async () => (kind === "vibe" ? ["zai"] : ["codex-openai"]),
    listAgentDescriptors: async () =>
      kind === "vibe"
        ? [
            {
              id: "zai",
              title: "GLM-5.3 Flash · Z.ai",
              description:
                "Claude-compatible tools through the configured Z.ai route.",
              order: 10,
            },
          ]
        : [
            {
              id: "codex-openai",
              title: "Codex · OpenAI",
              description: "Codex-oriented tools through OpenAI.",
              order: 10,
            },
          ],
    listSessions: async () => [
      kind === "composer-active" ? COMPOSER_SESSION_SUMMARY : SESSION_SUMMARY,
    ],
    getSessionSummary: async () =>
      kind === "vibe"
        ? VIBE_SESSION_SUMMARY
        : kind === "system-template"
        ? SYSTEM_TEMPLATE_SUMMARY
        : kind === "composer-active"
        ? COMPOSER_SESSION_SUMMARY
        : SESSION_SUMMARY,
    getSessionAgent: async () => (kind === "vibe" ? "zai" : "codex-openai"),
    switchSessionAgent: async () => {},
    listApplicationActions: async () =>
      kind === "cost" ? [COST_ACTION_FIXTURE.action_definition] : [],
    listApplicationUiSchema: async () => [],
    listMessages: async () => ({
      messages: displayedMessages,
      cursorEventId: "0",
      activeRequestId:
        kind === "composer-active" ? "website-active-request" : null,
    }),
    getLatestEventId: async () => "0",
    listEvents: async () => ({
      events: [],
      latestEventId: "0",
      cursorExpired: false,
    }),
    getSessionUiSchema: async () =>
      kind === "vibe"
        ? []
        : kind === "compiled"
        ? [COMPILED_ACTION_FIXTURE.ui_element]
        : kind === "usage" || kind === "cost"
        ? MESSAGE_FOOTER_ELEMENTS
        : kind === "provider-settings"
        ? PROVIDER_SETTINGS_SCHEMA
        : kind === "hero"
        ? MOBILE_HERO_UI_SCHEMA
        : SESSION_UI_SCHEMA,
    getSessionApplicationUiSchema: async () =>
      kind === "hero"
        ? []
        : kind === "cost"
        ? [COST_ACTION_FIXTURE.ui_element]
        : SESSION_APPLICATION_UI_SCHEMA,
    getSessionOverrides: async () =>
      kind === "provider-settings" ? {} : SESSION_OVERRIDES,
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
    executeAction: async (
      params: Parameters<AgentBackend["executeAction"]>[0]
    ) => {
      if (params.actionId === "show_cost_report") {
        return COST_ACTION_FIXTURE.response as any;
      }
      throw new Error(`Unexpected website fixture action: ${params.actionId}`);
    },
    executeSessionAction: async (
      params: Parameters<NonNullable<AgentBackend["executeSessionAction"]>>[0]
    ) => {
      if (params.actionId === "show_compiled_system_message") {
        return COMPILED_ACTION_FIXTURE.response as any;
      }
      if (params.actionId === "show_cost_report") {
        return COST_ACTION_FIXTURE.response as any;
      }
      throw new Error(`Unexpected website fixture action: ${params.actionId}`);
    },
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
    {
      value: "blocked",
      label: "Blocked",
      icon: "alert-circle",
      tone: "danger",
    },
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
      WORKSPACE_SESSIONS.find((session) => session.session_id === sessionId) ??
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
          default_pinned: false,
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
          default_pinned: true,
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

function MobileWorkspaceVisual({ theme }: { theme: Theme }): React.JSX.Element {
  const backend = useMemo(() => createWorkspaceBackend(), []);
  return (
    <ThemeProvider theme={theme}>
      <PinnedActionsProvider>
        <HomeWorkspaceProvider>
          <ApplicationPluginsProvider
            backend={backend}
            connectionId="website-workspaces-defaults-v2"
          >
            <View
              style={[styles.root, { backgroundColor: theme.background }]}
              testID="website-workspaces-ready"
            >
              <SessionsScreen
                backend={backend}
                connectionId="website-workspaces-defaults-v2"
                connectionName="Research workspace"
                cachedSessions={WORKSPACE_SESSIONS}
                lastLoadedAt={1}
                isActive
                requestStatuses={WORKSPACE_REQUEST_STATUSES}
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

function MobileHomeVisual({ theme }: { theme: Theme }): React.JSX.Element {
  return (
    <ThemeProvider theme={theme}>
      <PinnedActionsProvider>
        <HomeWorkspaceProvider store={HOME_VISUAL_STORE}>
          <View
            style={[styles.root, { backgroundColor: theme.background }]}
            testID="website-home-ready"
          >
            <HomeScreen
              connections={HOME_CONNECTIONS}
              sessionsCache={HOME_SESSIONS_CACHE}
              statusesByConnection={HOME_STATUSES}
              onOpenGlobalSettings={() => {}}
              onOpenEmbeddedSettings={() => {}}
              onNewConnection={() => {}}
              onSelectSession={() => {}}
            />
          </View>
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
    clcWebsiteVisualKind ?? Settings.get("clcWebsiteVisualKind") ?? "settings";
  const backend = useMemo(
    () => createHarnessBackend(configuredKind),
    [configuredKind]
  );
  const theme: Theme = configuredTheme === "dark" ? darkTheme : lightTheme;

  if (configuredKind === "workspaces") {
    return <MobileWorkspaceVisual theme={theme} />;
  }
  if (configuredKind === "home") {
    return <MobileHomeVisual theme={theme} />;
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
              <GlobalDisplayLayer
                backend={backend}
                connectionId="website-visual"
              >
                <View style={styles.screen}>
                  <SessionChatScreen
                    backend={backend}
                    connectionId="website-visual"
                    isActive={
                      configuredKind === "actions" ||
                      configuredKind === "message-actions" ||
                      configuredKind === "usage" ||
                      configuredKind === "cost" ||
                      configuredKind === "hero" ||
                      configuredKind === "compiled" ||
                      configuredKind === "vibe" ||
                      configuredKind === "composer-active" ||
                      configuredKind === "system-template"
                    }
                    sessionId={
                      configuredKind === "composer-active"
                        ? COMPOSER_SESSION_ID
                        : SESSION_ID
                    }
                    sessionSummary={
                      configuredKind === "vibe"
                        ? VIBE_SESSION_SUMMARY
                        : configuredKind === "system-template"
                        ? SYSTEM_TEMPLATE_SUMMARY
                        : configuredKind === "composer-active"
                        ? COMPOSER_SESSION_SUMMARY
                        : SESSION_SUMMARY
                    }
                    cachedMessages={
                      configuredKind === "usage" || configuredKind === "cost"
                        ? [PROVIDER_USAGE_MESSAGE]
                        : configuredKind === "vibe"
                        ? VIBE_MESSAGES
                        : configuredKind === "system-template"
                        ? SYSTEM_TEMPLATE_MESSAGES
                        : configuredKind === "hero"
                        ? MOBILE_HERO_MESSAGES
                        : MESSAGES
                    }
                    lastLoadedAt={1}
                    cachedEventsCursorId="0"
                    cachedActiveRequestId={
                      configuredKind === "composer-active"
                        ? "website-active-request"
                        : null
                    }
                    onUpdateCache={() => {}}
                    onUpdateSessionSummaries={() => {}}
                    onBack={() => {}}
                    onNavigateToSession={() => {}}
                    initialComposeText={
                      configuredKind === "composer-active"
                        ? "Append a validation note while the current request finishes."
                        : ""
                    }
                    initialScrollAnchor={null}
                    initialRangeStartText={
                      configuredKind === "vibe" ||
                      configuredKind === "system-template"
                        ? "0"
                        : "-50"
                    }
                    initialRangeEndText=""
                    onSaveComposeText={() => {}}
                    onSaveScrollAnchor={() => {}}
                    onSaveHistoryRange={() => {}}
                    debugTimeline={[]}
                    onAppendDebugTimelineEntry={() => {}}
                  />
                  {configuredKind === "compiled" ||
                  configuredKind === "cost" ? (
                    <ActionResultModal
                      testID={`website-${configuredKind}-action-display`}
                      visible
                      presentationMode="overlay"
                      display={
                        (configuredKind === "compiled"
                          ? COMPILED_ACTION_FIXTURE.response.result.display
                          : COST_ACTION_FIXTURE.response.result.display) as any
                      }
                      onRequestClose={() => {}}
                    />
                  ) : null}
                  {configuredKind === "actions" ||
                  configuredKind === "message-actions" ||
                  configuredKind === "usage" ||
                  configuredKind === "cost" ||
                  configuredKind === "hero" ||
                  configuredKind === "compiled" ||
                  configuredKind === "vibe" ||
                  configuredKind === "composer-active" ||
                  configuredKind ===
                    "system-template" ? null : configuredKind ===
                    "snapshots" ? (
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
