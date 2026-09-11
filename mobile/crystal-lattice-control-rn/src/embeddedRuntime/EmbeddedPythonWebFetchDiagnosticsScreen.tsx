import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { createEmbeddedRuntimeBackend } from "./createEmbeddedRuntimeBackend";
import { startEmbeddedPythonRuntime } from "./embeddedPythonRuntime";

type State =
  | { status: "loading" }
  | { status: "ready"; title: string }
  | { status: "error"; message: string };

export function EmbeddedPythonWebFetchDiagnosticsScreen(): React.JSX.Element {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        await startEmbeddedPythonRuntime();
        const { transport } = createEmbeddedRuntimeBackend();
        const response = await transport.request<{
          status: "ok";
          title: string;
        }>({
          method: "GET",
          path: "/embedded/runtime/web-fetch-smoke",
        });
        if (active) {
          setState({ status: "ready", title: response.data.title });
        }
      } catch (error) {
        if (active) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Embedded WebFetch</Text>
        {state.status === "loading" ? (
          <>
            <ActivityIndicator size="large" />
            <Text testID="embedded-web-fetch-status">Loading</Text>
          </>
        ) : state.status === "error" ? (
          <>
            <Text testID="embedded-web-fetch-status" style={styles.error}>
              Failed
            </Text>
            <Text testID="embedded-web-fetch-error">{state.message}</Text>
          </>
        ) : (
          <>
            <Text testID="embedded-web-fetch-status" style={styles.ready}>
              Ready
            </Text>
            <Text testID="embedded-web-fetch-title">{state.title}</Text>
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
    fontSize: 24,
    fontWeight: "700",
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
});