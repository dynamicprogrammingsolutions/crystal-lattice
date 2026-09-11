/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

describe("embedded Python WebFetch", () => {
  it("fetches and extracts a public page inside embedded CPython", async () => {
    await device.launchApp({
      newInstance: true,
      launchArgs: {
        clcEmbeddedPythonWebFetchHarness: "1",
        detoxEnableSynchronization: "0",
      },
    });

    await waitFor(element(by.id("embedded-web-fetch-status")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.id("embedded-web-fetch-status")))
      .toHaveText("Ready")
      .withTimeout(60000);
    await detoxExpect(element(by.id("embedded-web-fetch-title"))).toHaveText(
      "Welcome to Python.org"
    );
  });
});