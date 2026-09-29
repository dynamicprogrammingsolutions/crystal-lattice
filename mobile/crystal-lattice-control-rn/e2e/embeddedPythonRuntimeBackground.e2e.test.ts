/// <reference types="detox" />

import assert from "node:assert/strict";
import * as detox from "detox";

async function readText(testId: string): Promise<string> {
  const attributes = (await element(by.id(testId)).getAttributes()) as {
    text?: string;
    label?: string;
    value?: string;
  };
  return String(attributes.text ?? attributes.label ?? attributes.value ?? "");
}

async function waitForText(
  testId: string,
  expected: string,
  timeoutMs: number
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if ((await readText(testId)) === expected) {
      return;
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(
    `Timed out waiting for ${testId}=${expected}; got ${await readText(testId)}`
  );
}

describe("embedded Python runtime background continuation", () => {
  it("completes a delayed real tool loop after background and foreground", async () => {
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
    await device.disableSynchronization();
    await waitFor(element(by.id("embedded-python-runtime-lifecycle-state")))
      .toExist()
      .withTimeout(30000);
    await waitForText(
      "embedded-python-runtime-lifecycle-state",
      "running",
      120000
    );

    await device.sendToHome();
    await new Promise<void>((resolve) => setTimeout(resolve, 5000));
    await device.launchApp({ newInstance: false });

    await waitForText("embedded-python-runtime-status", "Ready", 180000);
    await waitForText(
      "embedded-python-runtime-lifecycle-state",
      "completed",
      30000
    );
    const backgroundedAt = Number(
      await readText("embedded-python-runtime-lifecycle-backgrounded")
    );
    const completedAt = Number(
      await readText("embedded-python-runtime-lifecycle-completed")
    );
    assert.ok(backgroundedAt > 0);
    assert.ok(completedAt >= backgroundedAt);
    assert.equal(
      (await readText("embedded-python-runtime-output-content")).trim(),
      "UPPERCASE: ALPHA BETA GAMMA"
    );
  });
});
