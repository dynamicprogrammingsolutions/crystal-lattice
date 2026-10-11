import React, { useMemo, useState } from "react";
import { StyleSheet, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import {
  FetchTransport,
  RestAgentBackend,
  type SessionSummary,
} from "@crystal-lattice/frontend-sdk";
import {
  applyDisplayTypographyPreset,
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MARKDOWN_BASE_FONT_SIZES,
  MarkdownDisplayPreferencesProvider,
} from "@crystal-lattice/frontend-rn-components";
import ConnectedRoot from "../ConnectedRoot";
import { PinnedActionsProvider } from "../PinnedActionsContext";
import { HomeWorkspaceProvider } from "../HomeWorkspaceContext";
import { ThemeProvider, lightTheme } from "../theme";
import type { MessagesCache } from "../cache/types";
import type { SessionsCache } from "../../App";

const CONNECTION_ID = "chat-operations";
const noop = () => {};

export function MobileChatOperationsHarness(props: {
  clcChatOperationsBaseUrl: string;
  clcChatOperationsSessions: string;
  clcDisplayPreset?: string;
}) {
  const transport = useMemo(
    () => new FetchTransport({ baseUrl: props.clcChatOperationsBaseUrl }),
    [props.clcChatOperationsBaseUrl]
  );
  const backend = useMemo(
    () => new RestAgentBackend({ transport }),
    [transport]
  );
  const sessions = useMemo(
    () => JSON.parse(props.clcChatOperationsSessions) as SessionSummary[],
    [props.clcChatOperationsSessions]
  );
  const [sessionsCache, setSessionsCache] = useState<SessionsCache>({
    [CONNECTION_ID]: {
      connectionId: CONNECTION_ID,
      sessions,
      lastLoadedAt: Date.now(),
    },
  });
  const [messagesCache, setMessagesCache] = useState<MessagesCache>({});
  const preferences = {
    ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
    baseFontSize:
      props.clcDisplayPreset === "largest"
        ? MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1]
        : DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize,
  };
  const theme = applyDisplayTypographyPreset(
    lightTheme,
    preferences.baseFontSize
  );
  const url = new URL(props.clcChatOperationsBaseUrl);
  return (
    <SafeAreaProvider>
      <MarkdownDisplayPreferencesProvider value={preferences}>
        <ThemeProvider theme={theme}>
          <PinnedActionsProvider>
            <HomeWorkspaceProvider>
              <View testID="chat-operations-root" style={styles.root}>
                <ConnectedRoot
                  backend={backend}
                  transport={transport}
                  onDisconnect={noop}
                  connections={[
                    {
                      id: CONNECTION_ID,
                      kind: "manual",
                      name: "Chat operations",
                      host: url.hostname,
                      port: Number(url.port),
                      lastUsedAt: Date.now(),
                    },
                  ]}
                  connectionsLoading={false}
                  onSelectConnectionRecord={noop}
                  onNewConnectionRequested={noop}
                  onCloseConnectionWizard={noop}
                  renderConnectionWizard={() => null}
                  onDeleteConnectionRecord={noop}
                  activeConnectionId={CONNECTION_ID}
                  sessionsCache={sessionsCache}
                  messagesCache={messagesCache}
                  onUpdateSessionsCache={(connectionId, next) =>
                    setSessionsCache((current) => ({
                      ...current,
                      [connectionId]: {
                        connectionId,
                        sessions: next,
                        lastLoadedAt: Date.now(),
                      },
                    }))
                  }
                  onUpdateMessagesCache={(
                    connectionId,
                    sessionId,
                    messages,
                    eventsCursorId,
                    activeRequestId
                  ) =>
                    setMessagesCache((current) => ({
                      ...current,
                      [connectionId]: {
                        ...current[connectionId],
                        [sessionId]: {
                          ...current[connectionId]?.[sessionId],
                          connectionId,
                          sessionId,
                          messages,
                          eventsCursorId,
                          activeRequestId,
                          lastLoadedAt: Date.now(),
                        },
                      },
                    }))
                  }
                  onSaveMessagesComposeText={(
                    connectionId,
                    sessionId,
                    composeText
                  ) =>
                    setMessagesCache((current) => ({
                      ...current,
                      [connectionId]: {
                        ...current[connectionId],
                        [sessionId]: {
                          ...current[connectionId]?.[sessionId],
                          connectionId,
                          sessionId,
                          messages:
                            current[connectionId]?.[sessionId]?.messages ?? [],
                          lastLoadedAt:
                            current[connectionId]?.[sessionId]?.lastLoadedAt ??
                            null,
                          composeText,
                        },
                      },
                    }))
                  }
                  onSaveMessagesScrollAnchor={noop}
                  onSaveMessagesHistoryRange={noop}
                  debugTimeline={[]}
                  onAppendDebugTimelineEntry={noop}
                />
              </View>
            </HomeWorkspaceProvider>
          </PinnedActionsProvider>
        </ThemeProvider>
      </MarkdownDisplayPreferencesProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({ root: { flex: 1 } });
