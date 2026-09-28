import { NativeModules, Platform } from "react-native";
import type { ActionDisplayPayload } from "@crystal-lattice/frontend-sdk";

export interface EmbeddedPythonRuntimeInfo {
  status: "ready";
  pythonVersion: string;
  pythonPlatform: string;
  answer?: number;
  agents?: string[];
  sessionId?: string;
  messageCount?: number;
  providerMode?: "smoke" | "openai-compatible" | "multi-provider";
  assistantContent?: string;
  toolMessageCount?: number;
  toolNames?: string[];
  providerImports?: string[];
  applicationForkSessionId?: string;
  applicationForkTitle?: string;
  applicationSnapshotCount?: number;
  applicationSnapshotReadonly?: boolean;
  outputExists?: boolean;
  outputContent?: string;
}

export interface EmbeddedRuntimeResponse<T = any> {
  status: number;
  data: T;
}

export type EmbeddedProviderProfileId =
  | "compatible"
  | "reviewer"
  | "openai"
  | "openrouter"
  | "anthropic";

export interface EmbeddedProviderProfileUpdate {
  enabled?: boolean;
  baseUrl?: string;
  model?: string;
  authMode?: "api" | "chatgpt";
  tlsCaBundle?: string;
  apiKey?: string;
  clearApiKey?: boolean;
}

export interface EmbeddedProviderProfile {
  id: EmbeddedProviderProfileId;
  label: string;
  agentId: string;
  toolFamily: "claude-like" | "codex-like";
  enabled: boolean;
  baseUrl: string;
  model: string;
  authMode?: "api" | "chatgpt";
  tlsCaBundle?: string;
  hasApiKey: boolean;
}

export interface EmbeddedRuntimeConfiguration {
  version?: 3;
  defaultAgent?: string;
  providers?: Partial<
    Record<EmbeddedProviderProfileId, EmbeddedProviderProfileUpdate>
  >;
  profileId?: EmbeddedProviderProfileId;
  // Legacy reviewer setup aliases.
  proxyUrl?: string;
  model?: string;
  apiKey?: string;
}

export interface EmbeddedRuntimePublicConfiguration {
  version: 3;
  defaultAgent: string;
  providers: Record<EmbeddedProviderProfileId, EmbeddedProviderProfile>;
  // Legacy reviewer setup aliases.
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
  validateConfiguration(
    configuration: EmbeddedRuntimeConfiguration
  ): Promise<{ status: "ok"; profile_id: string; model: string }>;
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

export async function validateEmbeddedPythonRuntimeConfiguration(
  configuration: EmbeddedRuntimeConfiguration
): Promise<{ status: "ok"; profile_id: string; model: string }> {
  return requireNativeRuntime().validateConfiguration(configuration);
}

export async function noteEmbeddedPythonRuntimeAppState(
  state: string
): Promise<EmbeddedRuntimeLifecycleStatus> {
  return requireNativeRuntime().noteAppState(state);
}

export async function getEmbeddedPythonRuntimeLifecycleStatus(): Promise<EmbeddedRuntimeLifecycleStatus> {
  return requireNativeRuntime().getLifecycleStatus();
}

export interface EmbeddedRuntimeApplicationActionResult {
  display?: ActionDisplayPayload;
  [key: string]: unknown;
}

export async function executeEmbeddedRuntimeApplicationAction(options: {
  pluginId: string;
  actionId: string;
  actionOwner?: string;
  inputs?: Record<string, unknown>;
}): Promise<EmbeddedRuntimeApplicationActionResult> {
  const response = await executeEmbeddedRuntimeCommand<{
    status: "ok" | "error";
    message?: string;
    result?: EmbeddedRuntimeApplicationActionResult;
  }>({
    method: "POST",
    path: "/actions",
    body: {
      plugin: options.pluginId,
      action_id: options.actionId,
      action_owner: options.actionOwner,
      inputs: options.inputs ?? {},
    },
  });
  if (response.status >= 300 || response.data.status !== "ok") {
    throw new Error(
      response.data.message ?? "Embedded application action failed."
    );
  }
  return response.data.result ?? {};
}
