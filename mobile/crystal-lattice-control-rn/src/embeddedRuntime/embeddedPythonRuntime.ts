import { NativeModules, Platform } from "react-native";

export interface EmbeddedPythonRuntimeInfo {
  status: "ready";
  pythonVersion: string;
  pythonPlatform: string;
  answer?: number;
  agents?: string[];
  sessionId?: string;
  messageCount?: number;
  providerMode?: "smoke" | "openai-compatible";
  assistantContent?: string;
  toolMessageCount?: number;
  toolNames?: string[];
  providerImports?: string[];
  outputExists?: boolean;
  outputContent?: string;
}

export interface EmbeddedRuntimeResponse<T = any> {
  status: number;
  data: T;
}

export interface EmbeddedRuntimeConfiguration {
  proxyUrl: string;
  model: string;
  apiKey?: string;
}

export interface EmbeddedRuntimePublicConfiguration {
  proxyUrl: string;
  model: string;
  hasApiKey: boolean;
  inspectionOnly?: boolean;
}

export interface EmbeddedRuntimeLifecycleStatus {
  state:
    | "idle"
    | "running"
    | "background"
    | "completed"
    | "failed"
    | "cancelled"
    | "expired"
    | "interrupted";
  requestId?: string;
  sessionId?: string;
  appState?: string;
  backgroundTaskActive?: boolean;
  backgroundTimeRemaining?: number;
  startedAtMs?: number;
  backgroundedAtMs?: number;
  lastBackgroundedAtMs?: number;
  foregroundedAtMs?: number;
  completedAtMs?: number;
  failedAtMs?: number;
  expiredAtMs?: number;
  interruptedAtMs?: number;
  recoverable?: boolean;
}

interface EmbeddedPythonRuntimeModule {
  start(): Promise<EmbeddedPythonRuntimeInfo>;
  runSmoke(): Promise<EmbeddedPythonRuntimeInfo>;
  runApplicationSmoke(): Promise<EmbeddedPythonRuntimeInfo>;
  execute(request: Record<string, unknown>): Promise<EmbeddedRuntimeResponse>;
  configure(
    configuration: EmbeddedRuntimeConfiguration
  ): Promise<EmbeddedRuntimePublicConfiguration>;
  getConfiguration(): Promise<EmbeddedRuntimePublicConfiguration>;
  noteAppState(state: string): Promise<EmbeddedRuntimeLifecycleStatus>;
  getLifecycleStatus(): Promise<EmbeddedRuntimeLifecycleStatus>;
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

export async function runEmbeddedApplicationSmoke(): Promise<EmbeddedPythonRuntimeInfo> {
  return requireNativeRuntime().runApplicationSmoke();
}

export async function executeEmbeddedRuntimeCommand<T = any>(
  request: Record<string, unknown>
): Promise<EmbeddedRuntimeResponse<T>> {
  return requireNativeRuntime().execute(request);
}

export async function configureEmbeddedPythonRuntime(
  configuration: EmbeddedRuntimeConfiguration
): Promise<EmbeddedRuntimePublicConfiguration> {
  return requireNativeRuntime().configure(configuration);
}

export async function getEmbeddedPythonRuntimeConfiguration(): Promise<EmbeddedRuntimePublicConfiguration> {
  return requireNativeRuntime().getConfiguration();
}

export async function noteEmbeddedPythonRuntimeAppState(
  state: string
): Promise<EmbeddedRuntimeLifecycleStatus> {
  return requireNativeRuntime().noteAppState(state);
}

export async function getEmbeddedPythonRuntimeLifecycleStatus(): Promise<EmbeddedRuntimeLifecycleStatus> {
  return requireNativeRuntime().getLifecycleStatus();
}
