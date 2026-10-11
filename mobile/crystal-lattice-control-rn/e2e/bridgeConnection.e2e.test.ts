/// <reference types="detox" />

import * as detox from "detox";
import { expect as jestExpect } from "@jest/globals";
import { FetchTransport, RestAgentBackend } from "@crystal-lattice/frontend-sdk";
import {
  startBackendServer, startBridgeForE2E, waitForAsync, waitForStdoutMatch,
  type StartedServer, type StartedBridge,
} from "../../../packages/frontend-sdk/src/integration/harness";

const detoxExpect = detox.expect;
const serverId = `native-mobile-bridge-${Date.now()}`;
let bridge: StartedBridge;
let started: StartedServer;
let backend: RestAgentBackend;
let appUrl: string;

async function settle() {
  await new Promise((resolve) => setTimeout(resolve, 500));
}

async function enabled(testId: string) {
  await waitForAsync(async () => {
    const attributes = await element(by.id(testId)).getAttributes();
    return "enabled" in attributes && attributes.enabled;
  }, { timeoutMs: 10000, intervalMs: 100 });
}

async function openBridge() {
  await element(by.id("home-tab")).tap();
  await waitFor(element(by.id("home-scroll"))).toBeVisible().withTimeout(10000);
  await element(by.id("home-scroll")).scrollTo("top");
  await element(by.id("connections-new-connection")).tap();
  await waitFor(element(by.id("connection-wizard-modal"))).toBeVisible().withTimeout(10000);
  await settle();
  await element(by.id("connection-method-bridge")).tap();
}

async function launch(deleteState = false) {
  await device.launchApp({
    newInstance: true, delete: deleteState, launchArgs: { detoxEnableSynchronization: "0" },
  });
  await device.disableSynchronization();
  await waitFor(element(by.id("connections-new-connection"))).toBeVisible().withTimeout(30000);
}

describe("Home bridge public flow", () => {
  beforeAll(async () => {
    bridge = await startBridgeForE2E();
    started = await startBackendServer({
      config: {
        agents: { default: { provider: "deterministic_stream", model: "fixture" } },
        plugins: ["plugins.deterministic_stream_provider.DeterministicStreamProvider"],
      },
      bridge: { url: bridge.bridgeUrl, serverId, displayName: "Native bridge server" },
    });
    backend = new RestAgentBackend({ transport: new FetchTransport({ baseUrl: started.baseUrl }) });
    const httpBase = bridge.bridgeUrl.replace("ws://", "http://").replace("/ws/websocket", "");
    await waitForAsync(async () => {
      const data = await (await fetch(`${httpBase}/bridge/v1/servers`)).json();
      return data.servers.some((server: any) => server.server_id === serverId);
    }, { timeoutMs: 30000 });
    appUrl = device.getPlatform() === "android"
      ? bridge.bridgeUrl.replace("127.0.0.1", "10.0.2.2") : bridge.bridgeUrl;
  });

  afterAll(async () => {
    await started?.stop();
    await bridge?.stop();
  });

  it("saves discovery before pairing, reuses credentials, and removes only endpoint history", async () => {
    await launch(true);
    await openBridge();
    await detoxExpect(element(by.id("bridge-transport-mode-websocket"))).not.toExist();
    await element(by.id("bridge-add-new")).tap();
    await element(by.id("bridge-url-input")).replaceText(appUrl);
    await enabled("bridge-connect-button");
    await settle();
    await element(by.id("bridge-connect-button")).tap();
    await waitFor(element(by.id(`bridge-server-${serverId}`))).toBeVisible().withTimeout(30000);
    await element(by.id("connection-wizard-modal-close")).tap();
    await settle();

    await launch();
    await openBridge();
    await element(by.id(`saved-bridge-open-${appUrl}`)).tap();
    await waitFor(element(by.id(`bridge-server-${serverId}`))).toBeVisible().withTimeout(30000);
    await element(by.id(`bridge-server-${serverId}`)).tap();
    const code = await waitForStdoutMatch({
      stdout: started.stdout, pattern: /PAIRING CODE:\s*(\d{6})/, timeoutMs: 30000,
    });
    await waitFor(element(by.text("OK"))).toBeVisible().withTimeout(10000);
    await element(by.text("OK")).tap();
    await waitFor(element(by.text("OK"))).not.toExist().withTimeout(10000);
    await settle();
    await waitFor(element(by.id("bridge-pairing-code-input"))).toBeVisible().withTimeout(10000);
    await element(by.id("bridge-pairing-code-input")).replaceText(code[1]);
    await settle();
    await enabled("bridge-submit-pairing");
    await element(by.id("bridge-submit-pairing")).tap();
    await waitFor(element(by.id("connection-wizard-modal"))).not.toExist().withTimeout(30000);
    await settle();
    await element(by.id("home-scroll")).scrollTo("top");
    const attributes = await element(by.label("Native bridge server")).atIndex(0).getAttributes();
    const identifier = (attributes as any).identifier ?? (attributes as any).testID;
    jestExpect(identifier).toMatch(/^connection-title-/);
    const connectionId = identifier.slice("connection-title-".length);

    await element(by.id(`connection-new-session-${connectionId}`)).tap();
    await waitFor(element(by.id("new-session-agent-default"))).toBeVisible().withTimeout(30000);
    await settle();
    await element(by.id("new-session-agent-default")).tap();
    await waitFor(element(by.id("message-composer-input"))).toBeVisible().withTimeout(30000);
    await settle();
    await element(by.id("message-composer-input")).replaceText("Native bridge smoke");
    await settle();
    await enabled("composer-send");
    await element(by.id("composer-send")).tap();
    await waitForAsync(async () => {
      const sessions = await backend.listSessions();
      if (sessions.length !== 1) return false;
      const messages = await backend.listMessages(sessions[0].session_id);
      return messages.messages.some((entry) => entry.message.role === "assistant");
    }, { timeoutMs: 30000 });

    await launch();
    await openBridge();
    await element(by.id(`saved-bridge-remove-${appUrl}`)).tap();
    await waitFor(element(by.id(`saved-bridge-open-${appUrl}`))).not.toExist().withTimeout(10000);
    await element(by.id("connection-wizard-modal-close")).tap();
    await settle();
    await detoxExpect(element(by.id(`connection-card-${connectionId}`))).toBeVisible();
    await element(by.id(`connection-new-session-${connectionId}`)).tap();
    await waitFor(element(by.id("new-session-agent-default"))).toBeVisible().withTimeout(30000);
    await detoxExpect(element(by.id("bridge-pairing-code-input"))).not.toExist();
    await settle();
    await element(by.id("new-session-agent-default")).tap();
    await waitFor(element(by.id("message-composer-input"))).toBeVisible().withTimeout(30000);
    await settle();
    jestExpect(await backend.listSessions()).toHaveLength(2);
  }, 240000);
});