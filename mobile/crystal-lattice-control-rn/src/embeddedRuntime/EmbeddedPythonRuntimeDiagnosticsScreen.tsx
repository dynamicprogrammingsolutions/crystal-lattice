import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  EmbeddedPythonRuntimeInfo,
  runEmbeddedPythonSmoke,
  startEmbeddedPythonRuntime,
} from "./embeddedPythonRuntime";

type RuntimeState =
  | { status: "starting" }
  | { status: "ready"; info: EmbeddedPythonRuntimeInfo }
  | { status: "error"; message: string };

export function EmbeddedPythonRuntimeDiagnosticsScreen(): React.JSX.Element {
  const [runtimeState, setRuntimeState] = useState<RuntimeState>({
    status: "starting",
  });

  useEffect(() => {
    let active = true;

    async function start(): Promise<void> {
      try {
        await startEmbeddedPythonRuntime();
        const info = await runEmbeddedPythonSmoke();
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
            <Text testID="embedded-python-runtime-version" style={styles.detail}>
              {runtimeState.info.pythonVersion}
            </Text>
            <Text testID="embedded-python-runtime-platform" style={styles.detail}>
              {runtimeState.info.pythonPlatform}
            </Text>
            <Text testID="embedded-python-runtime-answer" style={styles.detail}>
              {String(runtimeState.info.answer)}
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