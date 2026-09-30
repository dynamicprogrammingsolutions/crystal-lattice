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
  toolEvidence: string;
  providerCapabilities: string[];
  workspaceDirectoryLabel: string;
  workspaceBoundaryRejected: boolean;
  workspaceSessionIsolation: boolean;
};

type MatrixState =
  | { status: "starting" }
  | ReadyState
  | { status: "error"; message: string };

export function EmbeddedProviderMatrixDiagnosticsScreen(): React.JSX.Element {
  const [state, setState] = useState<MatrixState>({ status: "starting" });

  useEffect(() => {
    let active = true;

    function toolEvidenceMarker(
      messages: Array<{ message: { role: string; [key: string]: unknown } }>
    ): string | null {
      for (const entry of messages) {
        if (entry.message.role === "user") {
          continue;
        }
        const match = JSON.stringify(entry.message).match(/MATRIX_[A-Z]+/);
        if (match) {
          return match[0];
        }
      }
      return null;
    }

    async function inspectProviderCapabilities(
      backend: ReturnType<typeof createEmbeddedRuntimeBackend>["backend"],
      sessionId: string
    ): Promise<string[]> {
      const schema = await backend.getSessionUiSchema(sessionId);
      const capabilities: string[] = [];
      if (schema.some((element: any) => element?.key === "enable_web_search")) {
        capabilities.push("web_search");
      }
      if (
        schema.some(
          (element: any) =>
            element?.ui_type === "composer_attachment" &&
            element?.attachment_type === "image"
        )
      ) {
        capabilities.push("image");
      }
      if (
        schema.some(
          (element: any) => element?.key === "enable_flex_processing"
        )
      ) {
        capabilities.push("flex");
      }
      if (schema.some((element: any) => element?.key === "enable_fast_mode")) {
        capabilities.push("fast");
      }
      return capabilities;
    }

    async function inspectWorkspace(
      backend: ReturnType<typeof createEmbeddedRuntimeBackend>["backend"],
      sessionId: string,
      selection: { selectDirectory: boolean }
    ): Promise<{
      workspaceDirectoryLabel: string;
      workspaceBoundaryRejected: boolean;
    }> {
      const schema = await backend.getSessionUiSchema(sessionId);
      const directoryElement = schema.find(
        (candidate: any) =>
          candidate?.type === "directory" &&
          candidate?.key === "working_directory"
      ) as any;
      const directoryOptions = Array.isArray(directoryElement?.options)
        ? directoryElement.options
        : [];
      const nestedOption = directoryOptions.find(
        (candidate: any) => candidate?.label === "matrix-alpha"
      );
      const rootOption = directoryOptions.find(
        (candidate: any) => candidate?.label === "Workspace root"
      );
      if (
        !nestedOption ||
        typeof nestedOption.value !== "string" ||
        !rootOption ||
        typeof rootOption.value !== "string"
      ) {
        throw new Error(
          "The nested workspace directory was not exposed by session settings."
        );
      }
      if (selection.selectDirectory) {
        await backend.patchSessionOverrides(sessionId, {
          working_directory: nestedOption.value,
        });
      }
      const overrides = await backend.getSessionOverrides(sessionId);
      if (overrides.working_directory !== nestedOption.value) {
        throw new Error("The session working directory override was not persisted.");
      }

      let workspaceBoundaryRejected = false;
      try {
        await backend.patchSessionOverrides(sessionId, {
          working_directory: `${rootOption.value}/../outside`,
        });
      } catch {
        workspaceBoundaryRejected = true;
      }
      return {
        workspaceDirectoryLabel: String(nestedOption.label),
        workspaceBoundaryRejected,
      };
    }

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
        const toolEvidence = toolEvidenceMarker(messages.messages as any);
        if (toolNames.length > 0 && assistant && toolEvidence) {
          const workspace = await inspectWorkspace(
            backend,
            summary.session_id,
            { selectDirectory: false }
          );
          const providerCapabilities = await inspectProviderCapabilities(
            backend,
            summary.session_id
          );
          const comparisonSession = sessions.find(
            (candidate) => candidate.session_id !== summary.session_id
          );
          const comparisonOverrides = comparisonSession
            ? await backend.getSessionOverrides(comparisonSession.session_id)
            : null;
          return {
            status: "ready",
            agentId,
            assistant: String(assistant.message.content ?? ""),
            sessionId: summary.session_id,
            toolNames,
            toolEvidence,
            providerCapabilities,
            ...workspace,
            workspaceSessionIsolation:
              comparisonOverrides != null &&
              comparisonOverrides.working_directory == null,
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
            ? `Call apply_patch exactly once to create matrix-alpha/matrix-result.txt containing ${marker}. After the tool succeeds, do not call another tool and reply exactly ${marker}.`
            : `Call Write exactly once with file_path matrix-alpha/matrix-result.txt and content ${marker}. After the tool succeeds, do not call another tool and reply exactly ${marker}.`;
        const { backend } = createEmbeddedRuntimeBackend();
        const created = await backend.createSession({ agentId });
        const sessionId = created.session.session_id;
        const providerCapabilities = await inspectProviderCapabilities(
          backend,
          sessionId
        );
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
        const toolEvidence = toolEvidenceMarker(messages.messages as any);
        if (toolEvidence !== marker) {
          throw new Error(
            `The provider tool request did not retain ${marker}.`
          );
        }
        const workspace = await inspectWorkspace(backend, sessionId, {
          selectDirectory: true,
        });
        const comparison = await backend.createSession({ agentId });
        const comparisonOverrides = await backend.getSessionOverrides(
          comparison.session.session_id
        );
        if (active) {
          setState({
            status: "ready",
            agentId,
            assistant: assistantText,
            sessionId,
            toolNames,
            toolEvidence,
            providerCapabilities,
            ...workspace,
            workspaceSessionIsolation:
              comparison.session.session_id !== sessionId &&
              comparisonOverrides.working_directory == null,
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
            <Text testID="embedded-provider-matrix-tool-evidence">
              {state.toolEvidence}
            </Text>
            <Text testID="embedded-provider-matrix-provider-capabilities">
              {state.providerCapabilities.join(",")}
            </Text>
            <Text testID="embedded-provider-matrix-assistant">
              {state.assistant}
            </Text>
            <Text testID="embedded-provider-matrix-workspace">
              {state.workspaceDirectoryLabel}
            </Text>
            <Text testID="embedded-provider-matrix-workspace-boundary">
              {state.workspaceBoundaryRejected ? "rejected" : "accepted"}
            </Text>
            <Text testID="embedded-provider-matrix-workspace-isolation">
              {state.workspaceSessionIsolation ? "isolated" : "shared"}
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