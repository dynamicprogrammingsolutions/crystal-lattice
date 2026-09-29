/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;
const manualLoginEnabled =
  process.env.CRYSTAL_RUN_CHATGPT_LOGIN_E2E === "1";
const loginStartDescribe = manualLoginEnabled ? describe.skip : describe;
const gatedDescribe = manualLoginEnabled ? describe : describe.skip;

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

async function readText(testId: string): Promise<string> {
  const attributes = (await element(by.id(testId)).getAttributes()) as {
    text?: string;
    label?: string;
    value?: string;
  };
  return String(attributes.text ?? attributes.label ?? attributes.value ?? "");
}

async function readChatGPTLoginDetails(): Promise<{
  url: string;
  code: string;
}> {
  await waitFor(element(by.id("embedded-provider-openai-chatgpt-login-url")))
    .toExist()
    .withTimeout(30000);
  await waitFor(element(by.id("embedded-provider-openai-chatgpt-login-code")))
    .toExist()
    .withTimeout(30000);
  const url = await readText("embedded-provider-openai-chatgpt-login-url");
  const code = await readText("embedded-provider-openai-chatgpt-login-code");
  if (!url.startsWith("https://") || !code.trim()) {
    throw new Error("ChatGPT login returned an invalid URL or empty code.");
  }
  return { url, code };
}

async function waitForChatGPTLogin(timeoutMs: number): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  let lastStatus = "";
  while (Date.now() < deadline) {
    await tapById("action-display-action-check-chatgpt-login-status");
    const status = await readText(
      "embedded-provider-openai-chatgpt-auth-state"
    );
    lastStatus = status;
    if (status === "ChatGPT status: authenticated") return;
    if (
      status === "ChatGPT status: failed" ||
      status === "ChatGPT status: expired" ||
      status === "ChatGPT status: denied"
    ) {
      throw new Error(status);
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error(
    `ChatGPT device login was not completed; last status: ${lastStatus || "unavailable"}. Approve the code shown in the simulator's ChatGPT Login card before the device-code attempt expires.`
  );
}

async function openChatGPTSettings(deleteData: boolean): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: deleteData,
    launchArgs: { detoxEnableSynchronization: "0" },
  });
  await device.disableSynchronization();
  await waitFor(element(by.id("home-tab")))
    .toBeVisible()
    .withTimeout(30000);
  await tapById("home-tab");
  await tapById("home-embedded-settings");
  await waitFor(element(by.id("embedded-runtime-settings")))
    .toBeVisible()
    .withTimeout(30000);
  await settleAfterModalTransition();
  await waitFor(element(by.id("embedded-provider-openai-auth-chatgpt")))
    .toBeVisible()
    .withTimeout(30000);
  await tapById("embedded-provider-openai-auth-chatgpt");
  await waitFor(element(by.id("embedded-provider-openai-auth-selected")))
    .toHaveText("Selected authentication: chatgpt")
    .withTimeout(30000);
  await waitFor(
    element(by.id("embedded-provider-openai-chatgpt-login_start"))
  )
    .toBeVisible()
    .withTimeout(30000);
}

loginStartDescribe("embedded OpenAI Responses ChatGPT login start", () => {
  it("shows a real device-login URL and code and can cancel", async () => {
    await openChatGPTSettings(true);
    await tapById("embedded-provider-openai-chatgpt-login_start");
    await waitFor(
      element(by.id("action-display-action-open-chatgpt-login-link"))
    )
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(
      element(by.id("action-display-action-copy-chatgpt-login-code"))
    )
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.text("ChatGPT Login")))
      .toBeVisible()
      .withTimeout(30000);
    await readChatGPTLoginDetails();
    await tapById("embedded-provider-openai-chatgpt-cancel_login");
    await waitFor(element(by.text("The background ChatGPT login attempt was canceled.")))
      .toBeVisible()
      .withTimeout(30000);
  }, 120000);
});

gatedDescribe("embedded OpenAI Responses ChatGPT login", () => {
  it("logs in from settings and completes a real tool request", async () => {
    await openChatGPTSettings(true);
    const scroll = by.id("embedded-runtime-settings-scroll");
    await waitFor(
      element(by.id("embedded-provider-openai-chatgpt-login_start"))
    )
      .toBeVisible()
      .withTimeout(30000);
    await tapById("embedded-provider-openai-chatgpt-login_start");
    await waitFor(
      element(by.id("action-display-action-open-chatgpt-login-link"))
    )
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(
      element(by.id("action-display-action-copy-chatgpt-login-code"))
    )
      .toExist()
      .withTimeout(30000);

    const { url, code } = await readChatGPTLoginDetails();
    console.log(`ChatGPT login URL: ${url}`);
    console.log(`ChatGPT login code: ${code}`);
    console.log(
      "Open that URL in a browser, enter the code, approve login, and return to the simulator."
    );
    await waitForChatGPTLogin(900000);
    await waitFor(element(by.id("embedded-provider-openai-enabled")))
      .toBeVisible()
      .whileElement(scroll)
      .scroll(150, "down");
    await tapById("embedded-provider-openai-enabled");
    await waitFor(element(by.id("embedded-provider-openai-default")))
      .toBeVisible()
      .whileElement(scroll)
      .scroll(100, "down");
    await tapById("embedded-provider-openai-default");
    await new Promise<void>((resolve) => setTimeout(resolve, 900));
    await waitFor(element(by.text("Provider settings saved.")))
      .toBeVisible()
      .withTimeout(30000);
    await tapById("embedded-runtime-settings-close");
    await waitFor(element(by.id("embedded-runtime-settings")))
      .not.toExist()
      .withTimeout(30000);

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