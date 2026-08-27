import React, { useMemo, useState } from "react";
import { Pressable, Settings, StyleSheet, Text, View } from "react-native";

import {
  type AgentBackend,
  type IndexedMessage,
  type SessionSummary,
} from "@crystal-lattice/frontend-sdk";

import { ApplicationPluginsProvider } from "../ApplicationPluginsContext";
import { PinnedActionsProvider } from "../PinnedActionsContext";
import SessionChatScreen from "../SessionChatScreen";
import GlobalDisplayLayer from "../components/GlobalDisplayLayer";
import SessionSettingsModal from "../components/SessionSettingsModal";
import { ThemeProvider, darkTheme, lightTheme, type Theme } from "../theme";

const SESSION_ID = "website-visual-session";
const SESSION_SUMMARY: SessionSummary = {
  session_id: SESSION_ID,
  modified: 1,
  preview: "Implement bounded retry handling for uploads",
  metadata: {},
  presentation: {
    title: "Implement upload retry handling",
    subtitle: "Coding session · OpenAI Responses",
    meta: "2 messages",
  },
};
const MESSAGES: IndexedMessage[] = [
  {
    index: 0,
    message: {
      role: "user",
      content:
        "Add bounded retries to the upload command and keep existing errors visible.",
    },
  },
  {
    index: 1,
    message: {
      role: "assistant",
      content:
        "Implemented retry backoff with explicit terminal errors and focused coverage.",
      metadata: {
        display: {
          type: "text",
          content:
            "Implemented retry backoff with explicit terminal errors and focused coverage.",
        },
      },
    },
  },
];

function createHarnessBackend(): AgentBackend {
  return {
    kind: "inProcess",
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: true,
      sessionConfigOverrides: true,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: async () => ["openai-responses"],
    listSessions: async () => [SESSION_SUMMARY],
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => [],
    getLatestEventId: async () => "0",
    listEvents: async () => ({
      events: [],
      latestEventId: "0",
      cursorExpired: false,
    }),
    getSessionUiSchema: async () => [
      {
        ui_type: "config",
        key: "model",
        type: "dropdown",
        label: "Model",
        description: "Model used for this coding session.",
        options: [
          { value: "openai/gpt-5", label: "GPT-5" },
          { value: "openai/gpt-5-mini", label: "GPT-5 mini" },
        ],
      },
      {
        ui_type: "config",
        key: "reasoning_effort",
        type: "select",
        label: "Reasoning effort",
        description: "Controls how much reasoning the model performs.",
        options: [
          { value: "low", label: "Low" },
          { value: "medium", label: "Medium" },
          { value: "high", label: "High" },
        ],
      },
      {
        ui_type: "config",
        key: "verbosity",
        type: "select",
        label: "Verbosity",
        description: "Controls response detail.",
        options: [
          { value: "low", label: "Low" },
          { value: "medium", label: "Medium" },
          { value: "high", label: "High" },
        ],
      },
      {
        ui_type: "config",
        key: "prompt_cache",
        type: "checkbox",
        label: "Prompt caching",
        description: "Reuse compatible cached prompt content.",
      },
      {
        ui_type: "config",
        key: "web_search",
        type: "checkbox",
        label: "Web search",
        description: "Allow provider-native web search when needed.",
      },
      {
        ui_type: "config",
        key: "response_format",
        type: "dropdown",
        label: "Response format",
        options: [
          { value: "text", label: "Text" },
          { value: "json", label: "JSON" },
        ],
      },
    ],
    getSessionApplicationUiSchema: async () => [],
    getSessionOverrides: async () => ({
      reasoning_effort: "medium",
      verbosity: "medium",
    }),
    getSessionConfigSchema: async () => [
      { key: "model", default: "openai/gpt-5" },
      { key: "reasoning_effort", default: "medium" },
      { key: "verbosity", default: "medium" },
      { key: "prompt_cache", default: true },
      { key: "web_search", default: false },
      { key: "response_format", default: "text" },
    ],
    getSessionBaseConfig: async () => ({
      model: "openai/gpt-5",
      reasoning_effort: "medium",
      verbosity: "medium",
      prompt_cache: true,
      web_search: false,
      response_format: "text",
    }),
    patchSessionOverrides: async () => {},
    deleteSessionOverride: async () => {},
  } as unknown as AgentBackend;
}

export interface MobileWebsiteVisualHarnessProps {
  clcWebsiteVisualTheme?: string;
}

export function MobileWebsiteVisualHarness({
  clcWebsiteVisualTheme,
}: MobileWebsiteVisualHarnessProps): React.JSX.Element {
  const backend = useMemo(() => createHarnessBackend(), []);
  const [visualOpen, setVisualOpen] = useState(false);
  const configuredTheme =
    clcWebsiteVisualTheme ?? Settings.get("clcWebsiteVisualTheme");
  const theme: Theme = configuredTheme === "dark" ? darkTheme : lightTheme;

  if (!visualOpen) {
    return (
      <ThemeProvider theme={theme}>
        <View
          style={[styles.root, { backgroundColor: theme.background }]}
          testID="website-visual-harness-ready"
        >
          <View style={styles.launchControl}>
            <Pressable
              testID="website-visual-open-session-settings"
              style={styles.launchButton}
              onPress={() => setVisualOpen(true)}
            >
              <Text style={styles.launchButtonText}>
                Open session settings visual
              </Text>
            </Pressable>
          </View>
        </View>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <PinnedActionsProvider>
        <ApplicationPluginsProvider
          backend={backend}
          connectionId="website-visual"
        >
          <View
            style={[styles.root, { backgroundColor: theme.background }]}
            testID="website-visual-harness-ready"
          >
            <GlobalDisplayLayer backend={backend} connectionId="website-visual">
              <View style={styles.screen}>
                <SessionChatScreen
                  backend={backend}
                  connectionId="website-visual"
                  isActive={false}
                  sessionId={SESSION_ID}
                  sessionSummary={SESSION_SUMMARY}
                  cachedMessages={MESSAGES}
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
                <SessionSettingsModal
                  backend={backend}
                  cacheKey={`website-visual-${
                    configuredTheme === "dark" ? "dark" : "light"
                  }`}
                  sessionId={SESSION_ID}
                  visible
                  onRequestClose={() => {}}
                />
              </View>
            </GlobalDisplayLayer>
          </View>
        </ApplicationPluginsProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
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
