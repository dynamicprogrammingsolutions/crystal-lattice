/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;
const gatedDescribe =
  process.env.CRYSTAL_RUN_CHATGPT_LOGIN_E2E === "1"
    ? describe
    : describe.skip;

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

async function waitForMatrixReady(timeoutMs: number): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const attributes = (await element(
      by.id("embedded-provider-matrix-status")
    ).getAttributes()) as { text?: string; label?: string; value?: string };
    const status = String(
      attributes.text ?? attributes.label ?? attributes.value ?? ""
    );
    if (status === "Ready") return;
    if (status === "Failed") {
      const error = (await element(
        by.id("embedded-provider-matrix-error")
      ).getAttributes()) as { text?: string; label?: string; value?: string };
      throw new Error(
        String(error.text ?? error.label ?? error.value ?? "Unknown error")
      );
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("ChatGPT provider diagnostic did not complete.");
}

gatedDescribe("embedded OpenAI Responses ChatGPT login", () => {
  it("uses existing login actions and completes a real tool request", async () => {
    await device.launchApp({
      newInstance: true,
      delete: false,
      launchArgs: { detoxEnableSynchronization: "0" },
    });
    await device.disableSynchronization();
    await tapById("connections-tab");
    await waitFor(element(by.id("connection-card-embedded-ios-runtime")))
      .toBeVisible()
      .withTimeout(30000);
    await tapById("connection-card-embedded-ios-runtime");
    await waitFor(element(by.id("sessions-actions-menu")))
      .toBeVisible()
      .withTimeout(120000);
    await tapById("sessions-actions-menu");
    await tapById("actions-menu-action-newSession");
    await waitFor(element(by.id("new-session-agent-openai-codex")))
      .toBeVisible()
      .withTimeout(30000);
    await element(
      by.label("Create session with openai-codex")
    ).performAccessibilityAction("activate");
    await waitFor(element(by.id("session-actions-menu")))
      .toBeVisible()
      .withTimeout(120000);
    await tapById("session-actions-menu");
    await waitFor(
      element(by.id("actions-menu-action-chatgpt_auth_login_start"))
    )
      .toBeVisible()
      .withTimeout(30000);
    await tapById("actions-menu-action-chatgpt_auth_login_start");
    await waitFor(element(by.id("session-action-result-modal")))
      .toBeVisible()
      .withTimeout(30000);

    console.log(
      "Complete the ChatGPT device login shown in the simulator, return to the app, and tap Check status."
    );
    await waitFor(element(by.text("ChatGPT login is active.")))
      .toBeVisible()
      .withTimeout(900000);

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
    ).toHaveText("openai-codex");
    await detoxExpect(
      element(by.id("embedded-provider-matrix-tools"))
    ).toHaveText("apply_patch");
    await detoxExpect(
      element(by.id("embedded-provider-matrix-assistant"))
    ).toHaveText("MATRIX_OPENAI");
  }, 1_500_000);
});