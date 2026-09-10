/// <reference types="detox" />

import assert from "node:assert/strict";
import * as detox from "detox";

const detoxExpect = detox.expect;

async function readText(testId: string): Promise<string> {
  const attributes = (await element(by.id(testId)).getAttributes()) as {
    text?: string;
    label?: string;
    value?: string;
  };
  return String(attributes.text ?? attributes.label ?? attributes.value ?? "");
}

async function waitForTerminalStatus(): Promise<string> {
  const deadline = Date.now() + 180000;
  while (Date.now() < deadline) {
    const status = await readText("embedded-python-runtime-status");
    if (status !== "Starting") {
      return status;
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 250));
  }
  return readText("embedded-python-runtime-status");
}

describe("embedded Python runtime with Ollama", () => {
  it("uses the authenticated OpenAI-compatible provider", async () => {
    const proxyUrl = process.env.CRYSTAL_EMBEDDED_PROXY_URL;
    const apiKey = process.env.CRYSTAL_EMBEDDED_PROXY_API_KEY;
    const model = process.env.CRYSTAL_EMBEDDED_MODEL;
    if (!proxyUrl || !apiKey || !model) {
      throw new Error(
        "CRYSTAL_EMBEDDED_PROXY_URL, CRYSTAL_EMBEDDED_PROXY_API_KEY, and CRYSTAL_EMBEDDED_MODEL are required"
      );
    }

    await device.launchApp({
      newInstance: true,
      delete: true,
      launchArgs: {
        clcEmbeddedPythonRuntimeHarness: "1",
        clcEmbeddedProxyURL: proxyUrl,
        clcEmbeddedProxyAPIKey: apiKey,
        clcEmbeddedModel: model,
        detoxEnableSynchronization: "0",
      },
    });

    await waitFor(element(by.id("embedded-python-runtime-status")))
      .toExist()
      .withTimeout(30000);
    const status = await waitForTerminalStatus();
    if (status === "Failed") {
      throw new Error(await readText("embedded-python-runtime-error"));
    }
    assert.equal(status, "Ready");
    await detoxExpect(
      element(by.id("embedded-python-runtime-provider-mode"))
    ).toHaveText("openai-compatible");
    await detoxExpect(
      element(by.id("embedded-python-runtime-message-count"))
    ).toHaveText("2");
    assert.ok(
      (await readText("embedded-python-runtime-assistant")).trim().length > 0
    );
  });
});
