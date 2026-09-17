import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { createEmbeddedRuntimeBackend } from "./createEmbeddedRuntimeBackend";
import {
  getEmbeddedPythonRuntimeConfiguration,
  startEmbeddedPythonRuntime,
} from "./embeddedPythonRuntime";

type ReadyState = {
  status: "ready";
  agentId: string;
  assistant: string;
  sessionId: string;
  toolNames: string[];
};

type MatrixState =
  | { status: "starting" }
  | ReadyState
  | { status: "error"; message: string };

export function EmbeddedProviderMatrixDiagnosticsScreen(): React.JSX.Element {
  const [state, setState] = useState<MatrixState>({ status: "starting" });

  useEffect(() => {
    let active = true;

    async function inspectPersisted(
      agentId: string
    ): Promise<ReadyState | null> {
      const { backend } = createEmbeddedRuntimeBackend();
      const sessions = await backend.listSessions();
      for (const summary of sessions) {
        const messages = await backend.listMessages(summary.session_id);
        const toolNames = messages.messages
          .filter((entry) => entry.message.role === "tool")
          .map((entry) => String(entry.message.metadata?.tool_name ?? ""))
          .filter(Boolean);
        const assistant = [...messages.messages]
          .reverse()
          .find(
            (entry) =>
              entry.message.role === "assistant" &&
              String(entry.message.content ?? "").trim().length > 0
          );
        if (toolNames.length > 0 && assistant) {
          return {
            status: "ready",
            agentId,
            assistant: String(assistant.message.content ?? ""),
            sessionId: summary.session_id,
            toolNames,
          };
        }
      }
      return null;
    }

    async function run(): Promise<void> {
      try {
        await startEmbeddedPythonRuntime();
        const configuration = await getEmbeddedPythonRuntimeConfiguration();
        const agentId = configuration.defaultAgent;
        if (configuration.inspectionOnly) {
          const persisted = await inspectPersisted(agentId);
          if (!persisted) {
            throw new Error("No persisted provider matrix session was found.");
          }
          if (active) setState(persisted);
          return;
        }

        const profile = Object.values(configuration.providers).find(
          (candidate) => candidate.agentId === agentId
        );
        if (!profile) {
          throw new Error(`No configured profile owns ${agentId}.`);
        }
        const marker = `MATRIX_${profile.id.toUpperCase()}`;
        const prompt =
          profile.toolFamily === "codex-like"
            ? `Call apply_patch exactly once to create matrix-result.txt containing ${marker}. After the tool succeeds, do not call another tool and reply exactly ${marker}.`
            : `Call Write exactly once with file_path matrix-result.txt and content ${marker}. After the tool succeeds, do not call another tool and reply exactly ${marker}.`;
        const { backend } = createEmbeddedRuntimeBackend();
        const created = await backend.createSession({ agentId });
        const sessionId = created.session.session_id;
        const started = await backend.sendMessage(sessionId, {
          message: { role: "user", content: prompt },
        });
        const deadline = Date.now() + 300000;
        let completed = false;
        while (Date.now() < deadline) {
          const events = await backend.listEvents({
            sessionId,
            requestId: started.request_id,
          });
          const terminalError = events.events.find(
            (event) =>
              event.type === "error" ||
              event.type === "request_failed" ||
              event.type === "request_cancelled"
          );
          if (terminalError) {
            throw new Error(
              String(
                (terminalError as any).detail ??
                  (terminalError as any).message ??
                  terminalError.type
              )
            );
          }
          if (
            events.events.some((event) => event.type === "request_completed")
          ) {
            completed = true;
            break;
          }
          await new Promise<void>((resolve) => setTimeout(resolve, 100));
        }
        if (!completed) {
          throw new Error("The provider matrix request did not complete.");
        }

        const messages = await backend.listMessages(sessionId);
        const toolNames = messages.messages
          .filter((entry) => entry.message.role === "tool")
          .map((entry) => String(entry.message.metadata?.tool_name ?? ""))
          .filter(Boolean);
        const assistant = [...messages.messages]
          .reverse()
          .find(
            (entry) =>
              entry.message.role === "assistant" &&
              String(entry.message.content ?? "").trim().length > 0
          );
        if (toolNames.length === 0) {
          throw new Error("The provider request completed without a tool result.");
        }
        const assistantText = String(assistant?.message.content ?? "");
        if (!assistantText.includes(marker)) {
          throw new Error(
            `The provider final response did not include ${marker}.`
          );
        }
        if (active) {
          setState({
            status: "ready",
            agentId,
            assistant: assistantText,
            sessionId,
            toolNames,
          });
        }
      } catch (error) {
        if (active) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          });
        }
      }
    }

    void run();
    return () => {
      active = false;
    };
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Embedded Provider Matrix</Text>
        {state.status === "starting" ? (
          <>
            <ActivityIndicator size="large" />
            <Text testID="embedded-provider-matrix-status">Starting</Text>
          </>
        ) : state.status === "error" ? (
          <>
            <Text testID="embedded-provider-matrix-status" style={styles.error}>
              Failed
            </Text>
            <Text testID="embedded-provider-matrix-error">{state.message}</Text>
          </>
        ) : (
          <>
            <Text testID="embedded-provider-matrix-status" style={styles.ready}>
              Ready
            </Text>
            <Text testID="embedded-provider-matrix-agent">{state.agentId}</Text>
            <Text testID="embedded-provider-matrix-session">
              {state.sessionId}
            </Text>
            <Text testID="embedded-provider-matrix-tools">
              {state.toolNames.join(",")}
            </Text>
            <Text testID="embedded-provider-matrix-assistant">
              {state.assistant}
            </Text>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F2F2F7" },
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
    padding: 24,
  },
  title: { fontSize: 24, fontWeight: "700" },
  ready: { color: "#248A3D", fontSize: 20, fontWeight: "700" },
  error: { color: "#D70015", fontSize: 20, fontWeight: "700" },
});