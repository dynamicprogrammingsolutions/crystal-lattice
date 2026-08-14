import React, { useMemo, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import type {
  AgentBackend,
  IndexedMessage,
  SessionSummary,
} from "@crystal-lattice/frontend-sdk";

import { ApplicationPluginsProvider } from "../ApplicationPluginsContext";
import { PinnedActionsProvider } from "../PinnedActionsContext";
import SessionChatScreen from "../SessionChatScreen";
import { ThemeProvider, lightTheme } from "../theme";

const CONNECTION_ID = "transcript-range-navigation";
const SESSION_ID = "transcript-range-navigation-session";
const MESSAGE_COUNT = 200;

const ALL_MESSAGES: IndexedMessage[] = Array.from(
  { length: MESSAGE_COUNT },
  (_, index) => ({
    index,
    message: {
      role: index % 4 === 0 ? "user" : "assistant",
      content: Array.from(
        { length: 2 + (index % 4) },
        (_unused, line) =>
          `Range navigation message ${index}, line ${line + 1}.`,
      ).join("\n"),
    },
  }),
);

const SESSION_SUMMARY: SessionSummary = {
  session_id: SESSION_ID,
  modified: 1,
  preview: "Transcript range navigation",
  metadata: {},
  presentation: {
    title: "Transcript range navigation",
    subtitle: "Production chat range harness",
    meta: `${MESSAGE_COUNT} messages`,
  },
};

function normalizeBound(value: number | undefined, fallback: number): number {
  if (value == null) {
    return fallback;
  }
  const relative = value < 0 ? MESSAGE_COUNT + value : value;
  return Math.max(0, Math.min(MESSAGE_COUNT, relative));
}

export function MobileTranscriptRangeNavigationHarness(): React.JSX.Element {
  const [loadedRange, setLoadedRange] = useState("100:199");
  const backend = useMemo(
    () =>
      ({
        kind: "inProcess",
        getCapabilities: () => ({
          featureCompletions: false,
          sessionUiSchema: false,
          sessionConfigOverrides: false,
          sessionPlugins: false,
          applicationActions: false,
          applicationConfig: false,
        }),
        listAgents: async () => ["default"],
        getSessionAgent: async () => "default",
        listMessages: async (
          _sessionId: string,
          params: { start?: number; end?: number } = {},
        ) => {
          const start = normalizeBound(params.start, 0);
          const end = normalizeBound(params.end, MESSAGE_COUNT);
          const messages = ALL_MESSAGES.slice(start, end);
          setLoadedRange(
            messages.length > 0
              ? `${messages[0].index}:${messages[messages.length - 1].index}`
              : "empty",
          );
          return {
            messages,
            cursorEventId: "range-navigation:1",
            activeRequestId: null,
            readonly: false,
            snapshotId: null,
          };
        },
        getSessionSummary: async () => SESSION_SUMMARY,
        getSelectedSessionSnapshot: async () => null,
        listSessionSnapshots: async () => [],
        listSessionPlugins: async () => [],
        getSessionUiSchema: async () => [],
        getSessionApplicationUiSchema: async () => [],
        getSessionOverrides: async () => ({}),
        getSessionConfigSchema: async () => [],
        getSessionBaseConfig: async () => ({}),
        listApplicationActions: async () => [],
        listApplicationUiSchema: async () => [],
        getLatestEventId: async () => "range-navigation:1",
        listEvents: async () => ({
          events: [],
          latestEventId: "range-navigation:1",
          cursorExpired: false,
        }),
      }) as unknown as AgentBackend,
    [],
  );

  return (
    <ThemeProvider theme={lightTheme}>
      <PinnedActionsProvider>
        <ApplicationPluginsProvider
          backend={backend}
          connectionId={CONNECTION_ID}
        >
          <View
            style={styles.root}
            testID="transcript-range-navigation-harness-ready"
          >
            <Text testID="transcript-range-navigation-loaded-range">
              {loadedRange}
            </Text>
            <SessionChatScreen
              backend={backend}
              connectionId={CONNECTION_ID}
              isActive={false}
              sessionId={SESSION_ID}
              sessionSummary={SESSION_SUMMARY}
              cachedMessages={ALL_MESSAGES.slice(100, 200)}
              lastLoadedAt={1}
              cachedEventsCursorId="range-navigation:1"
              cachedActiveRequestId={null}
              onUpdateCache={() => {}}
              onUpdateSessionSummaries={() => {}}
              onBack={() => {}}
              onNavigateToSession={() => {}}
              initialComposeText=""
              initialScrollAnchor={null}
              initialRangeStartText="100"
              initialRangeEndText="200"
              onSaveComposeText={() => {}}
              onSaveScrollAnchor={() => {}}
              onSaveHistoryRange={() => {}}
              debugTimeline={[]}
              onAppendDebugTimelineEntry={() => {}}
            />
          </View>
        </ApplicationPluginsProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#F2F2F7",
  },
});
