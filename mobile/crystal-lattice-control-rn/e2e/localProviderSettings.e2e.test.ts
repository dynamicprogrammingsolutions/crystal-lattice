/// <reference types="detox" />

import * as detox from "detox";
const detoxExpect = detox.expect;

async function openProviders() {
  await element(by.id("home-embedded-settings")).tap();
  await waitFor(element(by.id("embedded-runtime-settings"))).toBeVisible().withTimeout(30000);
  await new Promise<void>((resolve) => setTimeout(resolve, 600));
}

async function showInProviders(testId: string, direction: "up" | "down" = "down") {
  await waitFor(element(by.id(testId))).toBeVisible()
    .whileElement(by.id("embedded-runtime-settings-scroll")).scroll(140, direction);
}

async function changeReviewerExposure() {
  await new Promise<void>((resolve) => setTimeout(resolve, 600));
  await waitFor(element(by.id("home-menu"))).toBeVisible().withTimeout(30000);
  await element(by.id("home-menu")).tap();
  await waitFor(element(by.id("home-menu-global-settings"))).toBeVisible().withTimeout(30000);
  await element(by.id("home-menu-global-settings")).performAccessibilityAction("activate");
  await waitFor(element(by.id("global-settings-modal"))).toBeVisible().withTimeout(30000);
  await new Promise<void>((resolve) => setTimeout(resolve, 600));
  await element(by.id("global-settings-reviewer-visible")).performAccessibilityAction("activate");
  await new Promise<void>((resolve) => setTimeout(resolve, 900));
  await element(by.id("global-settings-modal-close")).tap();
  await new Promise<void>((resolve) => setTimeout(resolve, 600));
}

async function launch(deleteData: boolean) {
  await device.launchApp({
    newInstance: true, delete: deleteData,
    launchArgs: { detoxEnableSynchronization: "0" },
  });
  await device.disableSynchronization();
  await waitFor(element(by.id("home-tab"))).toBeVisible().withTimeout(30000);
}

describe("Local provider settings", () => {
  it("retains both OpenAI credential paths and requires explicit reviewer opt-in", async () => {
    await launch(true);
    await openProviders();
    await detoxExpect(element(by.text("Local provider settings"))).toBeVisible();
    await detoxExpect(element(by.id("embedded-provider-reviewer"))).not.toExist();
    await detoxExpect(element(by.id("embedded-reviewer-visible"))).not.toExist();
    await detoxExpect(element(by.id("embedded-provider-openai-default"))).not.toExist();
    await showInProviders("embedded-provider-openai-api-key");
    await showInProviders("embedded-provider-openai-auth-chatgpt", "up");
    await element(by.id("embedded-provider-openai-auth-chatgpt")).performAccessibilityAction("activate");
    await waitFor(element(by.id("embedded-provider-openai-auth-selected")))
      .toHaveText("Default authentication: ChatGPT").withTimeout(30000);
    await showInProviders("embedded-provider-openai-api-key");
    await detoxExpect(element(by.id("embedded-provider-openai-api-key"))).toBeVisible();
    await showInProviders("embedded-provider-openai-chatgpt-login_start");
    await detoxExpect(element(by.id("embedded-provider-openai-chatgpt-login_start"))).toBeVisible();
    await element(by.id("embedded-runtime-settings-close")).tap();
    await waitFor(element(by.id("embedded-runtime-settings"))).not.toExist().withTimeout(30000);

    await changeReviewerExposure();
    await openProviders();
    await showInProviders("embedded-provider-reviewer-enabled");
    await detoxExpect(element(by.id("embedded-provider-reviewer"))).toExist();
    await detoxExpect(element(by.id("embedded-provider-reviewer-enabled-control"))).toHaveToggleValue(true);
    await detoxExpect(element(by.id("embedded-provider-reviewer-base-url"))).not.toExist();
    await detoxExpect(element(by.id("embedded-provider-reviewer-model"))).not.toExist();
    await detoxExpect(element(by.id("embedded-provider-reviewer-tls-ca-bundle"))).not.toExist();
    await showInProviders("embedded-provider-reviewer-api-key");
    await element(by.id("embedded-provider-reviewer-api-key")).replaceText("settings-test-key");
    await element(by.id("embedded-provider-reviewer-api-key")).tapReturnKey();
    await element(by.id("embedded-runtime-settings-close")).tap();
    await waitFor(element(by.id("embedded-runtime-settings"))).not.toExist().withTimeout(30000);

    await launch(false);
    await openProviders();
    await showInProviders("embedded-provider-openai-auth-selected");
    await detoxExpect(element(by.id("embedded-provider-openai-auth-selected")))
      .toHaveText("Default authentication: ChatGPT");
    await showInProviders("embedded-provider-reviewer-clear-key");
    await showInProviders("embedded-provider-reviewer-enabled", "up");
    await detoxExpect(element(by.id("embedded-provider-reviewer-enabled-control"))).toHaveToggleValue(true);
    await element(by.id("embedded-provider-reviewer-enabled")).performAccessibilityAction("activate");
    await waitFor(element(by.text("Provider settings saved."))).toBeVisible().withTimeout(30000);
    await element(by.id("embedded-runtime-settings-close")).tap();
    await waitFor(element(by.id("embedded-runtime-settings"))).not.toExist().withTimeout(30000);
    await changeReviewerExposure();
    await changeReviewerExposure();
    await openProviders();
    await showInProviders("embedded-provider-reviewer-enabled");
    await detoxExpect(element(by.id("embedded-provider-reviewer-enabled-control"))).toHaveToggleValue(false);
    await showInProviders("embedded-provider-reviewer-clear-key");
    await detoxExpect(element(by.id("embedded-provider-reviewer-clear-key"))).toBeVisible();
  }, 240000);
});