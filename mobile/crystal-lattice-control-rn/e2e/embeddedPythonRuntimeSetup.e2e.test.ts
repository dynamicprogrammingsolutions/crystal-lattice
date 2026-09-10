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

describe("embedded Python runtime setup", () => {
  it("validates a masked API key and reconnects from the saved owner configuration", async () => {
    const proxyUrl = process.env.CRYSTAL_EMBEDDED_PROXY_URL;
    const apiKey = process.env.CRYSTAL_EMBEDDED_PROXY_API_KEY;
    const model = process.env.CRYSTAL_EMBEDDED_MODEL;
    if (!proxyUrl || !apiKey || !model) {
      throw new Error(
        "CRYSTAL_EMBEDDED_PROXY_URL, CRYSTAL_EMBEDDED_PROXY_API_KEY, and CRYSTAL_EMBEDDED_MODEL are required"
      );
    }

    await launchApp(true);
    await element(by.id("connections-tab")).tap();
    await waitFor(element(by.id("connections-new-connection")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("connections-new-connection")).tap();
    await waitFor(element(by.id("connection-method-embedded")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("connection-method-embedded")).tap();

    await waitFor(element(by.id("embedded-proxy-url-input")))
      .toBeVisible()
      .withTimeout(10000);
    await waitFor(element(by.id("embedded-connect-button")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("embedded-proxy-url-input")).replaceText(proxyUrl);
    await element(by.id("embedded-model-input")).replaceText(model);
    const apiKeyInput = element(by.id("embedded-api-key-input"));
    await apiKeyInput.replaceText("wrong-key");
    await apiKeyInput.tapReturnKey();
    await element(by.id("embedded-connect-button")).tap();
    await waitFor(element(by.text("Embedded Runtime Error")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.text("OK")).tap();
    await new Promise<void>((resolve) => setTimeout(resolve, 750));

    await apiKeyInput.replaceText(apiKey);
    await apiKeyInput.tapReturnKey();
    await new Promise<void>((resolve) => setTimeout(resolve, 250));
    await element(by.id("embedded-connect-button")).tap();
    await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
      .toBeVisible()
      .withTimeout(120000);
    await detoxExpect(
      element(by.id("connection-status-embedded-ios-runtime"))
    ).toHaveText("Open");
    await detoxExpect(element(by.text(apiKey))).not.toExist();

    await new Promise<void>((resolve) => setTimeout(resolve, 1000));
    await launchApp(false);
    await element(by.id("connections-tab")).tap();
    await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("connection-card-embedded-ios-runtime")).tap();
    await waitFor(element(by.id("sessions-screen-title")))
      .toHaveText("On-device Python agent")
      .withTimeout(120000);
  });
});
