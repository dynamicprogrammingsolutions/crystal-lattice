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
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    const status = await readText("embedded-python-runtime-status");
    if (status !== "Starting") {
      return status;
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 250));
  }
  return readText("embedded-python-runtime-status");
}

describe("embedded Python runtime", () => {
  it("starts CPython and executes the production smoke program", async () => {
    await device.launchApp({
      newInstance: true,
      launchArgs: {
        clcEmbeddedPythonRuntimeHarness: "1",
        detoxEnableSynchronization: "0",
      },
    });

    await waitFor(element(by.id("embedded-python-runtime-status")))
      .toExist()
      .withTimeout(30000);
    const statusText = await waitForTerminalStatus();
    if (statusText === "Failed") {
      throw new Error(await readText("embedded-python-runtime-error"));
    }
    assert.equal(statusText, "Ready");
    const versionText = await readText("embedded-python-runtime-version");
    assert.match(versionText, /3\.12/);
    await detoxExpect(
      element(by.id("embedded-python-runtime-answer")),
    ).toHaveText("42");
    await detoxExpect(
      element(by.id("embedded-python-runtime-agents")),
    ).toHaveText("local");
    await detoxExpect(
      element(by.id("embedded-python-runtime-message-count")),
    ).toHaveText("2");
    const sessionId = await readText("embedded-python-runtime-session-id");
    assert.ok(sessionId.length > 10);
  });
});
