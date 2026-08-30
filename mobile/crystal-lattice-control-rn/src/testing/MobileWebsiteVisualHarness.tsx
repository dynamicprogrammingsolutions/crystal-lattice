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
import GlobalDisplayLayer from "../components/GlobalDisplayLayer";
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

function createHarnessBackend(kind: string): AgentBackend {
  const displayedMessages =
    kind === "usage"
      ? [PROVIDER_USAGE_MESSAGE]
      : kind === "hero"
        ? MOBILE_HERO_MESSAGES
        : MESSAGES;
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
        : kind === "hero"
          ? MOBILE_HERO_UI_SCHEMA
          : SESSION_UI_SCHEMA,
    getSessionApplicationUiSchema: async () =>
      kind === "hero" ? [] : SESSION_APPLICATION_UI_SCHEMA,
    getSessionOverrides: async () => SESSION_OVERRIDES,
    getSessionConfigSchema: async () => SESSION_CONFIG_SCHEMA,
    getSessionBaseConfig: async () => SESSION_BASE_CONFIG,
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
                    configuredKind === "hero"
                  }
                  sessionId={SESSION_ID}
                  sessionSummary={SESSION_SUMMARY}
                  cachedMessages={
                    configuredKind === "usage"
                      ? [PROVIDER_USAGE_MESSAGE]
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
                  {configuredKind === "actions" || configuredKind === "usage" || configuredKind === "hero" ? null : configuredKind === "snapshots" ? (
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
