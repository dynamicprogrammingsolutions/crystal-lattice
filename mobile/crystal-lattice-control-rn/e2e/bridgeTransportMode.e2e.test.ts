/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

async function settings() {
  await element(by.id("home-tab")).tap();
  await element(by.id("home-scroll")).scrollTo("top");
  await element(by.id("home-menu")).tap();
  await waitFor(element(by.id("home-menu-development-settings")))
    .toBeVisible().withTimeout(10000);
  await element(by.id("home-menu-development-settings")).tap();
  await waitFor(element(by.id("development-settings-modal")))
    .toBeVisible().withTimeout(10000);
}

describe("Home development bridge settings", () => {
  beforeAll(async () => {
    await device.launchApp({
      newInstance: true, delete: true,
    });
    await device.enableSynchronization();
    await waitFor(element(by.id("home-menu"))).toBeVisible().withTimeout(30000);
  });

  it("keeps the normal wizard HTTP-only and persists explicit legacy diagnostics separately", async () => {
    await settings();
    await detoxExpect(element(by.label("HTTP — Product default selected"))).toBeVisible();
    await element(by.id("development-bridge-mode-websocket")).tap();
    await waitFor(element(by.label("WebSocket — Legacy diagnostic selected")))
      .toBeVisible().withTimeout(10000);
    await element(by.id("development-bridge-mode-hybrid")).tap();
    await waitFor(element(by.label("Hybrid — Legacy diagnostic selected")))
      .toBeVisible().withTimeout(10000);
    await element(by.id("development-settings-modal-close")).tap();
    await device.launchApp({ newInstance: true });
    await device.enableSynchronization();
    await waitFor(element(by.id("home-menu"))).toBeVisible().withTimeout(30000);
    await settings();
    await detoxExpect(element(by.label("Hybrid — Legacy diagnostic selected"))).toBeVisible();
    await element(by.id("development-bridge-reset")).tap();
    await waitFor(element(by.label("HTTP — Product default selected")))
      .toBeVisible().withTimeout(10000);
    await element(by.id("development-settings-modal-close")).tap();
    await waitFor(element(by.id("development-settings-modal"))).not.toExist().withTimeout(10000);
    await new Promise((resolve) => setTimeout(resolve, 500));
    await element(by.id("connections-new-connection")).tap();
    await element(by.id("connection-method-bridge")).tap();
    await detoxExpect(element(by.id("bridge-transport-mode-websocket"))).not.toExist();
    await detoxExpect(element(by.id("bridge-transport-mode-hybrid"))).not.toExist();
    await detoxExpect(element(by.id("bridge-add-new"))).toBeVisible();
    await element(by.id("bridge-add-new")).tap();
    await detoxExpect(element(by.id("bridge-url-input"))).toBeVisible();
    await element(by.id("connection-wizard-modal-close")).tap();
  });
});