/// <reference types="detox" />

import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

import * as detox from "detox";

const detoxExpect = detox.expect;

type ProfileId =
  | "compatible"
  | "reviewer"
  | "openai"
  | "openrouter"
  | "anthropic";

const APP_BUNDLE_ID =
  "com.dynamicprogrammingsolutions.crystallatticecontrolrn";

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

async function launchApp(deleteData: boolean): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: deleteData,
    launchArgs: { detoxEnableSynchronization: "0" },
  });
  await device.disableSynchronization();
  await waitFor(element(by.id("home-tab")))
    .toBeVisible()
    .withTimeout(30000);
}

async function tapById(testId: string, timeoutMs = 15000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (true) {
    try {
      await element(by.id(testId)).tap();
      return;
    } catch (error) {
      if (Date.now() >= deadline) throw error;
      await new Promise<void>((resolve) => setTimeout(resolve, 250));
    }
  }
}

async function settleAfterModalTransition(): Promise<void> {
  await new Promise<void>((resolve) => setTimeout(resolve, 600));
}

async function scrollUntilVisible(
  scrollId: string,
  testId: string
): Promise<void> {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    try {
      await waitFor(element(by.id(testId))).toBeVisible().withTimeout(1500);
      return;
    } catch {
      await element(by.id(scrollId)).swipe("up", "fast", 0.45);
    }
  }
  throw new Error(`${testId} never became visible`);
}

function installSimulatorTlsCa(sourcePath: string): string {
  if (device.getPlatform() !== "ios") {
    throw new Error("The embedded reviewer TLS fixture is iOS-only.");
  }
  const container = execFileSync(
    "/usr/bin/xcrun",
    [
      "simctl",
      "get_app_container",
      device.id,
      APP_BUNDLE_ID,
      "data",
    ],
    { encoding: "utf-8" }
  ).trim();
  const destinationDirectory = path.join(
    container,
    "Library",
    "Application Support",
    "CrystalLatticeEmbeddedRuntime",
    "config",
    "test-certs"
  );
  fs.mkdirSync(destinationDirectory, { recursive: true });
  const destination = path.join(destinationDirectory, "reviewer-local-ca.pem");
  fs.copyFileSync(sourcePath, destination);
  return destination;
}

async function readText(testId: string): Promise<string> {
  const attributes = (await element(by.id(testId)).getAttributes()) as {
    text?: string;
    label?: string;
    value?: string;
  };
  return String(attributes.text ?? attributes.label ?? attributes.value ?? "");
}

async function waitForMatrixReady(timeoutMs: number): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const status = await readText("embedded-provider-matrix-status");
    if (status === "Ready") return;
    if (status === "Failed") {
      throw new Error(await readText("embedded-provider-matrix-error"));
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("Embedded provider matrix did not reach a terminal state.");
}

async function openEmbeddedConnection(): Promise<void> {
  await tapById("connections-tab");
  await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
    .toBeVisible()
    .withTimeout(30000);
  await tapById("connection-card-embedded-ios-runtime");
  await waitFor(element(by.id("sessions-screen-title")))
    .toHaveText("On-device Python agents")
    .withTimeout(120000);
  await new Promise<void>((resolve) => setTimeout(resolve, 3000));
}

async function waitForEnabled(testId: string): Promise<void> {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    const attributes = (await element(by.id(testId)).getAttributes()) as {
      enabled?: boolean;
    };
    if (attributes.enabled !== false) {
      return;
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`${testId} did not become enabled`);
}

async function createSession(agentId: string): Promise<void> {
  await waitFor(element(by.id("sessions-actions-menu")))
    .toBeVisible()
    .withTimeout(30000);
  await tapById("sessions-actions-menu");
  await waitFor(element(by.id("actions-menu-action-newSession")))
    .toBeVisible()
    .withTimeout(30000);
  await waitForEnabled("actions-menu-action-newSession");
  await tapById("actions-menu-action-newSession");
  await waitFor(element(by.id(`new-session-agent-${agentId}`)))
    .toBeVisible()
    .withTimeout(30000);
  await element(
    by.label(`Create session with ${agentId}`)
  ).performAccessibilityAction("activate");
  await waitFor(element(by.id("message-composer-input")))
    .toBeVisible()
    .withTimeout(60000);
}

async function configureProfile(options: {
  profileId: ProfileId;
  agentId: string;
  baseUrl: string;
  model: string;
  apiKey: string;
  authMode: "api" | "chatgpt";
  tlsCaBundle?: string;
}): Promise<void> {
  await tapById("home-tab");
  await waitFor(element(by.id("home-embedded-settings")))
    .toBeVisible()
    .withTimeout(30000);
  await tapById("home-embedded-settings");
  await waitFor(element(by.id("embedded-runtime-settings")))
    .toBeVisible()
    .withTimeout(30000);
  await settleAfterModalTransition();
  const scrollId = "embedded-runtime-settings-scroll";
  const scroll = by.id(scrollId);
  const prefix = `embedded-provider-${options.profileId}`;
  if (options.profileId === "openai" && options.authMode === "chatgpt") {
    await scrollUntilVisible(
      scrollId,
      "embedded-provider-openai-auth-chatgpt"
    );
    await tapById("embedded-provider-openai-auth-chatgpt");
  }
  await scrollUntilVisible(scrollId, `${prefix}-base-url`);

  const replaceProfileField = async (
    fieldId: string,
    value: string
  ): Promise<void> => {
    await scrollUntilVisible(scrollId, fieldId);
    const deadline = Date.now() + 15000;
    while (true) {
      try {
        await element(by.id(fieldId)).replaceText(value);
        return;
      } catch (error) {
        if (Date.now() >= deadline) throw error;
        await new Promise<void>((resolve) => setTimeout(resolve, 250));
      }
    }
  };

  await replaceProfileField(`${prefix}-base-url`, options.baseUrl);
  await replaceProfileField(`${prefix}-model`, options.model);
  if (options.profileId === "reviewer" && options.tlsCaBundle) {
    await replaceProfileField(
      "embedded-provider-reviewer-tls-ca-bundle",
      options.tlsCaBundle
    );
  }
  await replaceProfileField(`${prefix}-api-key`, options.apiKey);
  await scrollUntilVisible(scrollId, `${prefix}-test`);
  await tapById(`${prefix}-test`);
  await waitFor(element(by.id(`${prefix}-validation`)))
    .toHaveText(`Connected to ${options.model}`)
    .withTimeout(120000);
  await element(scroll).scrollTo("bottom");
  await waitFor(element(by.id("embedded-runtime-settings-save")))
    .toBeVisible()
    .withTimeout(30000);
  await tapById("embedded-runtime-settings-save");
  await waitFor(element(by.text("Provider settings saved.")))
    .toBeVisible()
    .withTimeout(30000);
  await detoxExpect(element(by.text(options.apiKey))).not.toExist();
  await tapById("embedded-runtime-settings-close");
}

describe("embedded provider real API matrix", () => {
  it("preserves local sessions and completes the configured provider tool path", async () => {
    const profileId = requiredEnvironment(
      "CRYSTAL_EMBEDDED_MATRIX_PROFILE"
    ) as ProfileId;
    const agentId = requiredEnvironment("CRYSTAL_EMBEDDED_MATRIX_AGENT");
    const baseUrl = requiredEnvironment("CRYSTAL_EMBEDDED_MATRIX_BASE_URL");
    const apiKey = requiredEnvironment("CRYSTAL_EMBEDDED_MATRIX_API_KEY");
    const model = requiredEnvironment("CRYSTAL_EMBEDDED_MATRIX_MODEL");
    const authMode = (process.env.CRYSTAL_EMBEDDED_MATRIX_AUTH_MODE ??
      "api") as "api" | "chatgpt";
    const tlsCaSource =
      process.env.CRYSTAL_EMBEDDED_MATRIX_TLS_CA_SOURCE ?? null;
    const marker = `MATRIX_${profileId.toUpperCase()}`;

    await launchApp(true);
    const tlsCaBundle = tlsCaSource
      ? installSimulatorTlsCa(tlsCaSource)
      : undefined;
    await openEmbeddedConnection();
    await createSession("local");
    await detoxExpect(element(by.id("session-chat-error"))).not.toExist();

    await configureProfile({
      profileId,
      agentId,
      baseUrl,
      model,
      apiKey,
      authMode,
      tlsCaBundle,
    });

    await tapById("messages-tab");
    await waitFor(element(by.id("message-composer-input")))
      .toBeVisible()
      .withTimeout(120000);
    await detoxExpect(element(by.id("session-chat-error"))).not.toExist();
    if (process.env.CRYSTAL_EMBEDDED_MATRIX_SKIP_PROVIDER_REQUEST === "1") {
      return;
    }

    await device.terminateApp();
    await device.launchApp({
      newInstance: true,
      delete: false,
      launchArgs: {
        clcEmbeddedProviderMatrixHarness: "1",
        detoxEnableSynchronization: "0",
      },
    });
    await waitFor(element(by.id("embedded-provider-matrix-status")))
      .toExist()
      .withTimeout(30000);
    await waitForMatrixReady(360000);
    await detoxExpect(
      element(by.id("embedded-provider-matrix-agent"))
    ).toHaveText(agentId);
    await detoxExpect(
      element(by.id("embedded-provider-matrix-tools"))
    ).toHaveText(
      profileId === "reviewer" || profileId === "openai"
        ? "apply_patch"
        : "Write"
    );
    const sessionId = await readText("embedded-provider-matrix-session");
    await detoxExpect(
      element(by.id("embedded-provider-matrix-assistant"))
    ).toHaveText(marker);

    await device.terminateApp();
    await device.launchApp({
      newInstance: true,
      delete: false,
      launchArgs: {
        clcEmbeddedProviderMatrixHarness: "1",
        clcEmbeddedInspectionOnly: "1",
        detoxEnableSynchronization: "0",
      },
    });
    await waitFor(element(by.id("embedded-provider-matrix-status")))
      .toExist()
      .withTimeout(30000);
    await waitForMatrixReady(120000);
    await detoxExpect(
      element(by.id("embedded-provider-matrix-session"))
    ).toHaveText(sessionId);
  }, 600000);
});