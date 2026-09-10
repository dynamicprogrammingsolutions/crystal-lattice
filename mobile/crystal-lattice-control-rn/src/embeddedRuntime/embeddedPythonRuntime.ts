import { NativeModules, Platform } from "react-native";

export interface EmbeddedPythonRuntimeInfo {
  status: "ready";
  pythonVersion: string;
  pythonPlatform: string;
  answer?: number;
}

interface EmbeddedPythonRuntimeModule {
  start(): Promise<EmbeddedPythonRuntimeInfo>;
  runSmoke(): Promise<EmbeddedPythonRuntimeInfo>;
}

const nativeRuntime =
  Platform.OS === "ios"
    ? (NativeModules.CrystalLatticePythonRuntime as
        | EmbeddedPythonRuntimeModule
        | undefined)
    : undefined;

function requireNativeRuntime(): EmbeddedPythonRuntimeModule {
  if (!nativeRuntime) {
    throw new Error("The embedded Python runtime is only available on iOS.");
  }
  return nativeRuntime;
}

export async function startEmbeddedPythonRuntime(): Promise<EmbeddedPythonRuntimeInfo> {
  return requireNativeRuntime().start();
}

export async function runEmbeddedPythonSmoke(): Promise<EmbeddedPythonRuntimeInfo> {
  return requireNativeRuntime().runSmoke();
}