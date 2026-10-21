/// <reference types="detox" />

import * as detox from "detox";
import { expect as jestExpect } from "@jest/globals";
import {
  FetchTransport,
  RestAgentBackend,
} from "@crystal-lattice/frontend-sdk";
import {
  getFreePort,
  startBackendServer,
  type StartedServer,
} from "../../../packages/frontend-sdk/src/integration/harness";

const detoxExpect = detox.expect;
let original: StartedServer;
let replacement: StartedServer;
let originalBackend: RestAgentBackend;

function configuration(agent: string) {
  return {
    default_agent: agent,
    globals: { plugins_env: { timeout: 30 } },
    agents: { [agent]: { provider: "deterministic_stream", model: "fixture" } },
    plugins: [
      "plugins.deterministic_stream_provider.DeterministicStreamProvider",
    ],
  };
}

async function settleModal() {
  await new Promise((resolve) => setTimeout(resolve, 500));
}

async function openSetup() {
  await element(by.id("home-tab")).tap();
  await waitFor(element(by.id("home-scroll")))
    .toBeVisible()
    .withTimeout(10000);
  await element(by.id("home-scroll")).scrollTo("top");
  await element(by.id("connections-new-connection")).tap();
  await waitFor(element(by.id("connection-wizard-modal")))
    .toBeVisible()
    .withTimeout(10000);
  await settleModal();
}

async function fillManual(port: number) {
  await element(by.id("connection-method-manual")).tap();
  await waitFor(element(by.id("manual-host-input")))
    .toBeVisible()
    .withTimeout(10000);
  await element(by.id("manual-host-input")).replaceText("127.0.0.1");
  await element(by.id("manual-port-input")).replaceText(String(port));
}

async function connect(port: number) {
  await openSetup();
  await fillManual(port);
  await element(by.id("manual-connect-button")).tap();
  await waitFor(element(by.id("connection-wizard-modal")))
    .not.toExist()
    .withTimeout(30000);
  await settleModal();
  await element(by.id("home-scroll")).scrollTo("top");
}

async function firstConnectionId(port: number): Promise<string> {
  const attributes = (await element(by.label(`127.0.0.1:${port}`))
    .atIndex(0)
    .getAttributes()) as {
    identifier?: string;
    testID?: string;
  };
  const identifier = attributes.identifier ?? attributes.testID;
  if (!identifier?.startsWith("connection-title-")) {
    throw new Error(
      `Missing connection card identifier: ${JSON.stringify(attributes)}`
    );
  }
  return identifier.slice("connection-title-".length);
}

async function createSession(agent: string, connectionId?: string) {
  if (connectionId) {
    await element(by.id("home-tab")).tap();
    await waitFor(element(by.id("home-scroll")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("home-scroll")).scrollTo("top");
    await element(by.id(`connection-new-session-${connectionId}`)).tap();
  } else {
    await element(by.id("sessions-tab")).tap();
    await waitFor(element(by.id("sessions-header-action-new-session")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("sessions-header-action-new-session")).tap();
  }
  await waitFor(element(by.id(`new-session-agent-${agent}`)))
    .toBeVisible()
    .withTimeout(30000);
  await settleModal();
  await element(by.id(`new-session-agent-${agent}`)).tap();
  await waitFor(element(by.id("message-composer-input")))
    .toBeVisible()
    .withTimeout(30000);
  await settleModal();
}

describe("Home connection public flow", () => {
  beforeAll(async () => {
    original = await startBackendServer({ config: configuration("default") });
    replacement = await startBackendServer({
      config: configuration("replacement"),
    });
    originalBackend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: original.baseUrl }),
    });
  });

  afterAll(async () => {
    await original?.stop();
    await replacement?.stop();
  });

  it("preserves cards, collapse, modal setup, retained connections, and saved sessions", async () => {
    await device.launchApp({
      newInstance: true,
      delete: true,
      launchArgs: { detoxEnableSynchronization: "0" },
    });
    await device.disableSynchronization();
    await waitFor(element(by.id("connections-new-connection")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(element(by.id("connections-tab"))).not.toExist();
    await detoxExpect(
      element(by.id("connection-title-embedded-ios-runtime"))
    ).toHaveText("Local agent");
    await detoxExpect(element(by.id("home-actions-menu"))).not.toExist();
    await detoxExpect(element(by.id("connections-actions-menu"))).not.toExist();
    await element(by.id("home-menu")).tap();
    await waitFor(element(by.id("home-menu-new-connection")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("home-menu-new-connection")).performAccessibilityAction(
      "activate"
    );
    await waitFor(element(by.id("connection-wizard-modal")))
      .toBeVisible()
      .withTimeout(10000);
    await settleModal();
    await element(by.id("connection-wizard-modal-close")).tap();
    await waitFor(element(by.id("connection-wizard-modal")))
      .not.toExist()
      .withTimeout(10000);
    await settleModal();

    await connect(original.port);
    const originalId = await firstConnectionId(original.port);
    await detoxExpect(
      element(by.id(`connection-status-${originalId}`))
    ).toHaveText("Open");
    await element(by.id(`connection-card-${originalId}`)).tap();
    await waitFor(element(by.id("sessions-screen-title")))
      .toHaveText(`127.0.0.1:${original.port}`)
      .withTimeout(30000);
    await createSession("default", originalId);
    const sessions = await originalBackend.listSessions();
    jestExpect(sessions).toHaveLength(1);
    const firstSessionId = sessions[0].session_id;

    await openSetup();
    await fillManual(replacement.port);
    await element(by.id("connection-wizard-modal-close")).tap();
    await waitFor(element(by.id("connection-wizard-modal")))
      .not.toExist()
      .withTimeout(10000);
    await settleModal();
    await detoxExpect(
      element(by.id(`connection-status-${originalId}`))
    ).toHaveText("Open");
    await createSession("default");
    jestExpect(await originalBackend.listSessions()).toHaveLength(2);

    await openSetup();
    await fillManual(await getFreePort());
    await element(by.id("manual-connect-button")).tap();
    await waitFor(element(by.text("Connection Error")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.text("OK")).tap();
    await settleModal();
    await element(by.id("connection-wizard-modal-close")).tap();
    await waitFor(element(by.id("connection-wizard-modal")))
      .not.toExist()
      .withTimeout(10000);
    await settleModal();
    await detoxExpect(
      element(by.id(`connection-status-${originalId}`))
    ).toHaveText("Open");
    await createSession("default");
    jestExpect(await originalBackend.listSessions()).toHaveLength(3);

    await connect(replacement.port);
    const replacementId = await firstConnectionId(replacement.port);
    await detoxExpect(
      element(by.id(`connection-status-${originalId}`))
    ).toHaveText("Closed");
    await detoxExpect(
      element(by.id(`connection-status-${replacementId}`))
    ).toHaveText("Open");
    await createSession("replacement");
    const replacementBackend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: replacement.baseUrl }),
    });
    jestExpect(await replacementBackend.listSessions()).toHaveLength(1);
    await createSession("default", originalId);
    jestExpect(await originalBackend.listSessions()).toHaveLength(4);

    await connect(original.port);
    const newestId = await firstConnectionId(original.port);
    await detoxExpect(element(by.id("home-connections-toggle"))).toHaveLabel(
      "Show all 4 connections"
    );
    await detoxExpect(
      element(by.id("connection-card-embedded-ios-runtime"))
    ).not.toExist();
    await element(by.id("home-connections-toggle")).tap();
    await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
      .toBeVisible()
      .whileElement(by.id("home-scroll"))
      .scroll(150, "down");
    await detoxExpect(element(by.id("home-connections-toggle"))).toHaveLabel(
      "Show fewer"
    );
    await waitFor(element(by.id("home-connections-toggle")))
      .toBeVisible()
      .whileElement(by.id("home-scroll"))
      .scroll(150, "down");
    await element(by.id("home-connections-toggle")).tap();
    await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
      .not.toExist()
      .withTimeout(10000);
    await detoxExpect(
      element(by.id(`connection-card-${newestId}`))
    ).toBeVisible();

    await device.launchApp({
      newInstance: true,
      delete: false,
      launchArgs: { detoxEnableSynchronization: "0" },
    });
    await device.disableSynchronization();
    await waitFor(element(by.id("home-connections-toggle")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(
      element(by.id("connection-card-embedded-ios-runtime"))
    ).not.toExist();
    await element(by.id("home-connections-toggle")).tap();
    await waitFor(element(by.id(`connection-card-${originalId}`)))
      .toBeVisible()
      .whileElement(by.id("home-scroll"))
      .scroll(150, "down");
    await element(by.id(`connection-card-${originalId}`)).tap();
    await waitFor(element(by.id(`session-row-${firstSessionId}`)))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id(`session-row-${firstSessionId}`)).tap();
    await waitFor(element(by.id("message-composer-input")))
      .toBeVisible()
      .withTimeout(30000);
    jestExpect(await originalBackend.listSessions()).toHaveLength(4);
  }, 240000);
});
