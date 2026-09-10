/// <reference types="detox" />

import assert from "node:assert/strict";
import * as detox from "detox";

const detoxExpect = detox.expect;

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
    const statusAttributes = (await element(
      by.id("embedded-python-runtime-status")
    ).getAttributes()) as { text?: string; label?: string; value?: string };
    const statusText = String(
      statusAttributes.text ??
        statusAttributes.label ??
        statusAttributes.value ??
        ""
    );
    if (statusText === "Failed") {
      const errorAttributes = (await element(
        by.id("embedded-python-runtime-error")
      ).getAttributes()) as { text?: string; label?: string; value?: string };
      throw new Error(
        String(
          errorAttributes.text ??
            errorAttributes.label ??
            errorAttributes.value ??
            "Embedded Python runtime failed without an error message."
        )
      );
    }
    assert.equal(statusText, "Ready");
    const versionAttributes = (await element(
      by.id("embedded-python-runtime-version")
    ).getAttributes()) as { text?: string; label?: string; value?: string };
    const versionText = String(
      versionAttributes.text ??
        versionAttributes.label ??
        versionAttributes.value ??
        ""
    );
    assert.match(versionText, /3\.12/);
    await detoxExpect(
      element(by.id("embedded-python-runtime-answer"))
    ).toHaveText("42");
  });
});