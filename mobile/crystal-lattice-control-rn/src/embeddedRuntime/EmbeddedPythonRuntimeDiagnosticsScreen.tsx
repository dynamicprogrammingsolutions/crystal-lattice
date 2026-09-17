import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  AppState,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  EmbeddedPythonRuntimeInfo,
  EmbeddedRuntimeLifecycleStatus,
  getEmbeddedPythonRuntimeConfiguration,
  getEmbeddedPythonRuntimeLifecycleStatus,
  noteEmbeddedPythonRuntimeAppState,
  runEmbeddedPythonSmoke,
  startEmbeddedPythonRuntime,
} from "./embeddedPythonRuntime";
import { createEmbeddedRuntimeBackend } from "./createEmbeddedRuntimeBackend";

type RuntimeState =
  | { status: "starting" }
  | { status: "ready"; info: EmbeddedPythonRuntimeInfo }
  | { status: "error"; message: string };

async function runApplicationRouteSmoke(
  backend: ReturnType<typeof createEmbeddedRuntimeBackend>["backend"],
  transport: ReturnType<typeof createEmbeddedRuntimeBackend>["transport"],
  sourceSessionId: string,
  sourceMessageCount: number
): Promise<{
  forkSessionId: string;
  forkTitle: string;
  snapshotCount: number;
  snapshotReadonly: boolean;
}> {
  const forked = await backend.forkSession(sourceSessionId, {
    index: Math.max(0, sourceMessageCount - 1),
  });
  const forkSessionId = forked.session.session_id;
  if (!backend.executeSessionAction) {
    throw new Error("The embedded backend does not support session actions.");
  }
  await backend.executeSessionAction({
    sessionId: forkSessionId,
    pluginId: "session_title",
    actionId: "set_session_title",
    inputs: {
      session_id: forkSessionId,
      title: "Embedded application routes",
    },
  });
  const forkMessages = await backend.listMessages(forkSessionId);
  await backend.deleteMessages(forkSessionId, {
    indices: [Math.max(0, forkMessages.messages.length - 1)],
  });
  const snapshots = await backend.listSessionSnapshots(forkSessionId);
  if (snapshots.length === 0) {
    throw new Error("Message deletion did not create a session snapshot.");
  }
  await backend.selectSessionSnapshot(
    forkSessionId,
    snapshots[0].snapshot_id
  );
  const selected = await backend.listMessages(forkSessionId);
  await backend.clearSelectedSessionSnapshot(forkSessionId);
  await backend.restoreSessionSnapshot(
    forkSessionId,
    snapshots[0].snapshot_id
  );
  const summaries = await backend.listSessions();
  const forkSummary = summaries.find(
    (session) => session.session_id === forkSessionId
  );
  const result = {
    forkSessionId,
    forkTitle: String(forkSummary?.presentation?.title ?? ""),
    snapshotCount: snapshots.length,
    snapshotReadonly: selected.readonly === true,
  };
  await transport.request({
    method: "DELETE",
    path: `/sessions/${encodeURIComponent(forkSessionId)}`,
  });
  return result;
}

export function EmbeddedPythonRuntimeDiagnosticsScreen(): React.JSX.Element {
  const [runtimeState, setRuntimeState] = useState<RuntimeState>({
    status: "starting",
  });
  const [lifecycleStatus, setLifecycleStatus] =
    useState<EmbeddedRuntimeLifecycleStatus | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = async (): Promise<void> => {
      try {
        const status = await getEmbeddedPythonRuntimeLifecycleStatus();
        if (active) {
          setLifecycleStatus(status);
        }
      } catch {
        // Runtime startup reports the actionable error through the main flow.
      }
    };
    void refresh();
    const interval = setInterval(() => {
      void refresh();
    }, 250);
    const subscription = AppState.addEventListener("change", (state) => {
      void noteEmbeddedPythonRuntimeAppState(state).then((status) => {
        if (active) {
          setLifecycleStatus(status);
        }
      });
    });
    return () => {
      active = false;
      clearInterval(interval);
      subscription.remove();
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function start(): Promise<void> {
      try {
        const runtimeInfo = await startEmbeddedPythonRuntime();
        const smokeInfo = await runEmbeddedPythonSmoke();
        const { backend, transport } = createEmbeddedRuntimeBackend();
        const providerImports = await transport.request<{
          providers: string[];
        }>({
          method: "GET",
          path: "/embedded/runtime/provider-imports",
        });
        const ownerConfiguration =
          await getEmbeddedPythonRuntimeConfiguration();
        if (ownerConfiguration.inspectionOnly) {
          const agents = await backend.listAgents();
          const sessions = await backend.listSessions();
          if (sessions.length === 0) {
            throw new Error("No persisted embedded session was found.");
          }
          const sessionId = sessions[0].session_id;
          const messages = await backend.listMessages(sessionId);
          const assistant = [...messages.messages]
            .reverse()
            .find(
              (entry) =>
                entry.message.role === "assistant" &&
                String(entry.message.content ?? "").trim().length > 0
            );
          const output = await transport.request<{
            exists: boolean;
            content: string;
            provider_mode: "smoke" | "openai-compatible";
          }>({
            method: "GET",
            path: "/embedded/workspace/output",
          });
          const info: EmbeddedPythonRuntimeInfo = {
            ...runtimeInfo,
            answer: smokeInfo.answer,
            agents,
            sessionId,
            messageCount: messages.messages.length,
            providerMode: output.data.provider_mode,
            assistantContent: String(assistant?.message.content ?? ""),
            toolMessageCount: messages.messages.filter(
              (entry) => entry.message.role === "tool"
            ).length,
            toolNames: messages.messages
              .filter((entry) => entry.message.role === "tool")
              .map((entry) => String(entry.message.metadata?.tool_name ?? ""))
              .filter(Boolean),
            providerImports: providerImports.data.providers,
            outputExists: output.data.exists,
            outputContent: output.data.content,
          };
          setLifecycleStatus(await getEmbeddedPythonRuntimeLifecycleStatus());
          if (active) {
            setRuntimeState({ status: "ready", info });
          }
          return;
        }
        await transport.request({
          method: "POST",
          path: "/embedded/workspace/reset",
          body: {
            input: "alpha beta gamma\n",
          },
        });
        const agents = await backend.listAgents();
        const created = await backend.createSession({
          agentId: agents[0],
          systemMessage:
            "Use the Read and Write tools for workspace file operations. Every file_path must be a bare workspace-relative path. Use exactly `input.txt` and `output.txt`; never start a path with `/` and never prefix it with `workspace/`.",
        });
        const sessionId = created.session.session_id;
        const sendAndWait = async (content: string): Promise<void> => {
          const started = await backend.sendMessage(sessionId, {
            message: {
              role: "user",
              content,
            },
          });
          const deadline = Date.now() + 180000;
          while (Date.now() < deadline) {
            const events = await backend.listEvents({
              sessionId,
              requestId: started.request_id,
            });
            if (
              events.events.some((event) => event.type === "request_completed")
            ) {
              return;
            }
            await new Promise<void>((resolve) => setTimeout(resolve, 50));
          }
          throw new Error("Embedded backend request did not complete.");
        };
        await sendAndWait(
          "Call Read with file_path exactly `input.txt` (no slash or directory prefix), then reply with the text you found."
        );
        await sendAndWait(
          "Call Write exactly once with file_path exactly `output.txt` and content exactly `UPPERCASE: ALPHA BETA GAMMA`. Do not copy the previous Read result and do not call any other tool. Never add a leading slash."
        );
        await sendAndWait(
          "Call Read with file_path exactly `output.txt` and briefly confirm that its content is `UPPERCASE: ALPHA BETA GAMMA`. Never add a leading slash."
        );
        const messages = await backend.listMessages(sessionId);
        const assistant = [...messages.messages]
          .reverse()
          .find(
            (entry) =>
              entry.message.role === "assistant" &&
              String(entry.message.content ?? "").trim().length > 0
          );
        const output = await transport.request<{
          exists: boolean;
          content: string;
          provider_mode: "smoke" | "openai-compatible";
        }>({
          method: "GET",
          path: "/embedded/workspace/output",
        });
        const applicationSmoke = await runApplicationRouteSmoke(
          backend,
          transport,
          sessionId,
          messages.messages.length
        );
        const info: EmbeddedPythonRuntimeInfo = {
          ...runtimeInfo,
          answer: smokeInfo.answer,
          agents,
          sessionId,
          messageCount: messages.messages.length,
          providerMode: output.data.provider_mode,
          assistantContent: String(assistant?.message.content ?? ""),
          toolMessageCount: messages.messages.filter(
            (entry) => entry.message.role === "tool"
          ).length,
          toolNames: messages.messages
            .filter((entry) => entry.message.role === "tool")
            .map((entry) => String(entry.message.metadata?.tool_name ?? ""))
            .filter(Boolean),
          providerImports: providerImports.data.providers,
          applicationForkSessionId: applicationSmoke.forkSessionId,
          applicationForkTitle: applicationSmoke.forkTitle,
          applicationSnapshotCount: applicationSmoke.snapshotCount,
          applicationSnapshotReadonly: applicationSmoke.snapshotReadonly,
          outputExists: output.data.exists,
          outputContent: output.data.content,
        };
        setLifecycleStatus(await getEmbeddedPythonRuntimeLifecycleStatus());
        if (active) {
          setRuntimeState({ status: "ready", info });
        }
      } catch (error) {
        if (active) {
          setRuntimeState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          });
        }
      }
    }

    void start();
    return () => {
      active = false;
    };
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Embedded Python Runtime</Text>
        {runtimeState.status === "starting" ? (
          <>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text testID="embedded-python-runtime-status" style={styles.status}>
              Starting
            </Text>
            <Text
              testID="embedded-python-runtime-lifecycle-state"
              style={styles.detail}
            >
              {lifecycleStatus?.state ?? "idle"}
            </Text>
          </>
        ) : runtimeState.status === "error" ? (
          <>
            <Text testID="embedded-python-runtime-status" style={styles.error}>
              Failed
            </Text>
            <Text testID="embedded-python-runtime-error" style={styles.detail}>
              {runtimeState.message}
            </Text>
          </>
        ) : (
          <>
            <Text testID="embedded-python-runtime-status" style={styles.ready}>
              Ready
            </Text>
            <Text
              testID="embedded-python-runtime-lifecycle-state"
              style={styles.detail}
            >
              {lifecycleStatus?.state ?? "idle"}
            </Text>
            <Text
              testID="embedded-python-runtime-lifecycle-backgrounded"
              style={styles.detail}
            >
              {String(
                lifecycleStatus?.lastBackgroundedAtMs ??
                  lifecycleStatus?.backgroundedAtMs ??
                  ""
              )}
            </Text>
            <Text
              testID="embedded-python-runtime-lifecycle-completed"
              style={styles.detail}
            >
              {String(lifecycleStatus?.completedAtMs ?? "")}
            </Text>
            <Text
              testID="embedded-python-runtime-version"
              style={styles.detail}
            >
              {runtimeState.info.pythonVersion}
            </Text>
            <Text
              testID="embedded-python-runtime-platform"
              style={styles.detail}
            >
              {runtimeState.info.pythonPlatform}
            </Text>
            <Text testID="embedded-python-runtime-answer" style={styles.detail}>
              {String(runtimeState.info.answer)}
            </Text>
            <Text testID="embedded-python-runtime-agents" style={styles.detail}>
              {(runtimeState.info.agents ?? []).join(",")}
            </Text>
            <Text
              testID="embedded-python-runtime-message-count"
              style={styles.detail}
            >
              {String(runtimeState.info.messageCount)}
            </Text>
            <Text
              testID="embedded-python-runtime-session-id"
              style={styles.detail}
            >
              {runtimeState.info.sessionId}
            </Text>
            <Text
              testID="embedded-python-runtime-provider-mode"
              style={styles.detail}
            >
              {runtimeState.info.providerMode}
            </Text>
            <Text
              testID="embedded-python-runtime-assistant"
              style={styles.detail}
            >
              {runtimeState.info.assistantContent}
            </Text>
            <Text
              testID="embedded-python-runtime-tool-message-count"
              style={styles.detail}
            >
              {String(runtimeState.info.toolMessageCount)}
            </Text>
            <Text
              testID="embedded-python-runtime-tool-names"
              style={styles.detail}
            >
              {(runtimeState.info.toolNames ?? []).join(",")}
            </Text>
            <Text
              testID="embedded-python-runtime-provider-imports"
              style={styles.detail}
            >
              {(runtimeState.info.providerImports ?? []).join(",")}
            </Text>
            <Text
              testID="embedded-python-runtime-application-fork"
              style={styles.detail}
            >
              {runtimeState.info.applicationForkSessionId ?? ""}
            </Text>
            <Text
              testID="embedded-python-runtime-application-title"
              style={styles.detail}
            >
              {runtimeState.info.applicationForkTitle ?? ""}
            </Text>
            <Text
              testID="embedded-python-runtime-application-snapshots"
              style={styles.detail}
            >
              {String(runtimeState.info.applicationSnapshotCount ?? "")}
            </Text>
            <Text
              testID="embedded-python-runtime-application-readonly"
              style={styles.detail}
            >
              {String(runtimeState.info.applicationSnapshotReadonly ?? "")}
            </Text>
            <Text
              testID="embedded-python-runtime-output-exists"
              style={styles.detail}
            >
              {String(runtimeState.info.outputExists)}
            </Text>
            <Text
              testID="embedded-python-runtime-output-content"
              style={styles.detail}
            >
              {runtimeState.info.outputContent}
            </Text>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F2F2F7",
  },
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
    padding: 24,
  },
  title: {
    color: "#111111",
    fontSize: 24,
    fontWeight: "700",
  },
  status: {
    color: "#666666",
    fontSize: 17,
  },
  ready: {
    color: "#248A3D",
    fontSize: 20,
    fontWeight: "700",
  },
  error: {
    color: "#D70015",
    fontSize: 20,
    fontWeight: "700",
  },
  detail: {
    color: "#333333",
    fontFamily: "Courier",
    fontSize: 14,
    textAlign: "center",
  },
});
