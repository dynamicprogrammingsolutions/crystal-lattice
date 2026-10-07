/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

async function launchApp(deleteData: boolean): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: deleteData,
    launchArgs: {
      detoxEnableSynchronization: "0",
    },
  });
  await device.disableSynchronization();
  await waitFor(element(by.id("home-tab")))
    .toBeVisible()
    .withTimeout(30000);
}

async function scrollUntilVisible(testId: string): Promise<void> {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    try {
      await waitFor(element(by.id(testId))).toBeVisible().withTimeout(1500);
      return;
    } catch {
      await element(by.id("embedded-runtime-settings-scroll")).swipe(
        "up",
        "fast",
        0.35
      );
    }
  }
  throw new Error(`${testId} never became visible`);
}

describe("embedded Python runtime setup", () => {
  it("configures the built-in local connection from the Home settings window", async () => {
    const proxyUrl = process.env.CRYSTAL_EMBEDDED_PROXY_URL;
    const apiKey = process.env.CRYSTAL_EMBEDDED_PROXY_API_KEY;
    const model = process.env.CRYSTAL_EMBEDDED_MODEL;
    if (!proxyUrl || !apiKey || !model) {
      throw new Error(
        "CRYSTAL_EMBEDDED_PROXY_URL, CRYSTAL_EMBEDDED_PROXY_API_KEY, and CRYSTAL_EMBEDDED_MODEL are required"
      );
    }

    await launchApp(true);
    await element(by.id("home-tab")).tap();
    await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(
      element(by.id("connection-title-embedded-ios-runtime"))
    ).toHaveText("Local agent");

    await element(by.id("home-tab")).tap();
    await waitFor(element(by.id("home-menu")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("home-menu")).tap();
    await waitFor(element(by.id("home-menu-embedded-settings")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("home-menu-embedded-settings")).performAccessibilityAction("activate");
    await waitFor(element(by.id("embedded-runtime-settings")))
      .toBeVisible()
      .withTimeout(10000);
    await new Promise<void>((resolve) => setTimeout(resolve, 600));

    await scrollUntilVisible("embedded-provider-compatible-base-url");
    await detoxExpect(element(by.id("embedded-provider-reviewer"))).not.toExist();
    await detoxExpect(element(by.id("embedded-provider-openai"))).toExist();
    await detoxExpect(element(by.id("embedded-provider-openrouter"))).toExist();
    await detoxExpect(element(by.id("embedded-provider-anthropic"))).toExist();

    await element(by.id("embedded-provider-compatible-base-url")).replaceText(
      proxyUrl
    );
    await element(by.id("embedded-provider-compatible-model")).replaceText(
      model
    );
    const apiKeyInput = element(
      by.id("embedded-provider-compatible-api-key")
    );
    await apiKeyInput.replaceText("wrong-key");
    await element(by.id("embedded-provider-compatible-test")).tap();
    await waitFor(
      element(by.id("embedded-provider-compatible-validation"))
    )
      .toHaveText(
        "The proxy credentials were rejected or the configured model is unavailable"
      )
      .withTimeout(30000);

    await apiKeyInput.replaceText(apiKey);
    await element(by.id("embedded-provider-compatible-test")).tap();
    await waitFor(
      element(by.id("embedded-provider-compatible-validation"))
    )
      .toHaveText(`Connected to ${model}`)
      .withTimeout(30000);
    await scrollUntilVisible("embedded-provider-compatible-enabled");
    await element(by.id("embedded-provider-compatible-enabled")).tap();
    await new Promise<void>((resolve) => setTimeout(resolve, 900));
    await waitFor(element(by.text("Provider settings saved.")))
      .toBeVisible()
      .withTimeout(10000);
    await detoxExpect(element(by.text(apiKey))).not.toExist();
    await element(by.id("embedded-runtime-settings-close")).tap();
    await waitFor(element(by.id("home-tab")))
      .toBeVisible()
      .withTimeout(5000);
    await new Promise<void>((resolve) => setTimeout(resolve, 2000));
    await element(by.id("home-tab")).tap();
    await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("connection-card-embedded-ios-runtime")).tap();
    await waitFor(element(by.id("sessions-screen-title")))
      .toHaveText("Local agent")
      .withTimeout(120000);

    await launchApp(false);
    await element(by.id("home-menu")).tap();
    await waitFor(element(by.id("home-menu-embedded-settings")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("home-menu-embedded-settings")).performAccessibilityAction("activate");
    await waitFor(element(by.id("embedded-runtime-settings")))
      .toBeVisible()
      .withTimeout(10000);
    await new Promise<void>((resolve) => setTimeout(resolve, 600));
    await scrollUntilVisible("embedded-provider-compatible-clear-key");
    await detoxExpect(element(by.text(apiKey))).not.toExist();
  });
});
