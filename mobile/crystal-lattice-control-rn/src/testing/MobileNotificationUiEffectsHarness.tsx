import React, { useMemo, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type {
  AgentBackend,
  IndexedMessage,
  SessionNotification,
  SessionSummary,
} from "@crystal-lattice/frontend-sdk";

import { ApplicationPluginsProvider } from "../ApplicationPluginsContext";
import { PinnedActionsProvider } from "../PinnedActionsContext";
import SessionChatScreen from "../SessionChatScreen";
import { ThemeProvider, lightTheme } from "../theme";

const CONNECTION_ID = "notification-ui-effects";
const SESSION_ID = "notification-ui-effects-session";
const BEFORE_MESSAGES: IndexedMessage[] = [
  {
    index: 0,
    message: { role: "assistant", content: "Transcript before effect" },
  },
];
const AFTER_MESSAGES: IndexedMessage[] = [
  {
    index: 1,
    message: { role: "assistant", content: "Transcript after effect" },
  },
];

function notification(
  revision: number,
  completed: boolean
): SessionNotification {
  return {
    id: "notification-ui-effects-compaction",
    key: "notification-ui-effects:compaction",
    kind: "notification",
    status: "pending",
    revision,
    severity: completed ? "success" : "warning",
    title: completed ? "Compaction complete" : "Compaction running",
    body: completed ? "The transcript should reload." : "Waiting.",
    created_at: "2026-08-04T00:00:00Z",
    updated_at: `2026-08-04T00:00:0${revision}Z`,
    source: { plugin: "notification_ui_effects_harness" },
    display: {
      format: "text",
      title: completed ? "Compaction complete" : "Compaction running",
      body: completed ? "The transcript should reload." : "Waiting.",
      variant: completed ? "success" : "warning",
      presentation: "banner",
      dismissible: completed,
    },
    ...(completed ? { ui_effects: { reload_session_ids: [SESSION_ID] } } : {}),
    model_visibility: "hidden",
  };
}

function dismissedNotification(): SessionNotification {
  return {
    ...notification(3, true),
    status: "dismissed",
    updated_at: "2026-08-04T00:00:03Z",
    dismissal: {
      dismissed_at: "2026-08-04T00:00:03Z",
      reason: "user",
    },
  };
}

function summary(revision: number, completed: boolean): SessionSummary {
  return {
    session_id: SESSION_ID,
    modified: revision,
    preview: "Notification UI effects",
    metadata: {
      notifications: {
        items: [notification(revision, completed)],
      },
    },
  };
}

export function MobileNotificationUiEffectsHarness(): React.JSX.Element {
  const completedRef = useRef(false);
  const summaryRef = useRef(summary(1, false));
  const [sessionSummary, setSessionSummary] = useState(summaryRef.current);
  const [reloadCount, setReloadCount] = useState(0);
  const backend = useMemo(
    () =>
      ({
        kind: "inProcess",
        getCapabilities: () => ({
          featureCompletions: false,
          sessionUiSchema: false,
          sessionConfigOverrides: false,
          sessionPlugins: false,
          applicationActions: true,
          applicationConfig: false,
        }),
        listAgents: async () => ["default"],
        listSessions: async () => [summaryRef.current],
        getSessionSummary: async () => summaryRef.current,
        listMessages: async () => {
          setReloadCount((current) => current + 1);
          return {
            messages: completedRef.current ? AFTER_MESSAGES : BEFORE_MESSAGES,
            cursorEventId: "0",
            activeRequestId: null,
          };
        },
        listApplicationActions: async () => [],
        listApplicationUiSchema: async () => [],
        getLatestEventId: async () => "0",
        listEvents: async () => ({
          events: [],
          latestEventId: "0",
          cursorExpired: false,
        }),
      } as unknown as AgentBackend),
    []
  );

  const complete = () => {
    completedRef.current = true;
    summaryRef.current = summary(2, true);
    setSessionSummary(summaryRef.current);
  };

  const dismiss = () => {
    summaryRef.current = {
      ...summary(3, true),
      metadata: {
        notifications: {
          items: [dismissedNotification()],
        },
      },
    };
    setSessionSummary(summaryRef.current);
  };

  return (
    <ThemeProvider theme={lightTheme}>
      <PinnedActionsProvider>
        <ApplicationPluginsProvider
          backend={backend}
          connectionId={CONNECTION_ID}
        >
          <View
            style={styles.root}
            testID="notification-ui-effects-harness-ready"
          >
            <Pressable
              testID="notification-ui-effects-complete"
              style={styles.button}
              onPress={complete}
            >
              <Text>Complete compaction</Text>
            </Pressable>
            <Pressable
              testID="notification-ui-effects-dismiss"
              style={styles.button}
              onPress={dismiss}
            >
              <Text>Dismiss completion</Text>
            </Pressable>
            <Text testID="notification-ui-effects-reload-count">
              {String(reloadCount)}
            </Text>
            <SessionChatScreen
              backend={backend}
              connectionId={CONNECTION_ID}
              isActive
              sessionId={SESSION_ID}
              sessionSummary={sessionSummary}
              cachedMessages={BEFORE_MESSAGES}
              lastLoadedAt={1}
              cachedEventsCursorId="0"
              cachedActiveRequestId={null}
              onUpdateCache={() => {}}
              onUpdateSessionSummaries={() => {}}
              onBack={() => {}}
              onNavigateToSession={() => {
                throw new Error("Notification UI effects must not navigate");
              }}
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
          </View>
        </ApplicationPluginsProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#F2F2F7" },
  button: { padding: 12, backgroundColor: "#FFFFFF" },
});
