/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

describe("bridge transport mode selection", () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true, delete: true });
  });

  it("defaults to WebSocket and allows explicit HTTP, hybrid, and rollback selection", async () => {
    await waitFor(element(by.id("connections-new-connection"))).toBeVisible().withTimeout(30000);
    await element(by.id("connections-new-connection")).tap();
    await element(by.id("connection-method-bridge")).tap();

    await detoxExpect(
      element(by.label("WebSocket bridge transport selected")),
    ).toBeVisible();

    await element(by.id("bridge-transport-mode-http")).tap();
    await detoxExpect(
      element(by.label("HTTP bridge transport selected")),
    ).toBeVisible();

    await element(by.id("bridge-transport-mode-hybrid")).tap();
    await detoxExpect(
      element(by.label("Hybrid bridge transport selected")),
    ).toBeVisible();

    await element(by.id("bridge-transport-mode-websocket")).tap();
    await detoxExpect(
      element(by.label("WebSocket bridge transport selected")),
    ).toBeVisible();
  });
});