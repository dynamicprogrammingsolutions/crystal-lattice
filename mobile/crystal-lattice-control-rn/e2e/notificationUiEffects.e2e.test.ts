/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

function attributeText(attributes: unknown): string {
  const value = attributes as any;
  return String(value?.text ?? value?.label ?? value?.value ?? "");
}

describe("mobile notification UI effects", () => {
  it("reloads the production transcript without navigating", async () => {
    await device.launchApp({
      newInstance: true,
      launchArgs: { clcNotificationUiEffectsHarness: "1" },
    });
    await waitFor(element(by.id("notification-ui-effects-harness-ready")))
      .toExist()
      .withTimeout(30000);
    await waitFor(element(by.id("transcript-message-0")))
      .toExist()
      .withTimeout(30000);

    const before = await element(
      by.id("notification-ui-effects-reload-count")
    ).getAttributes();
    await element(by.id("notification-ui-effects-complete")).tap();

    await waitFor(element(by.id("transcript-message-1")))
      .toExist()
      .withTimeout(30000);
    await detoxExpect(element(by.id("messages-screen-header"))).toExist();
    await detoxExpect(element(by.id("transcript-message-0"))).not.toExist();
    const after = await element(
      by.id("notification-ui-effects-reload-count")
    ).getAttributes();
    if (attributeText(before) === attributeText(after)) {
      throw new Error(
        `Expected a backend reload, count remained ${attributeText(after)}`
      );
    }

    await element(by.id("notification-ui-effects-dismiss")).tap();
    await new Promise<void>((resolve) => setTimeout(resolve, 500));
    const afterDismiss = await element(
      by.id("notification-ui-effects-reload-count")
    ).getAttributes();
    if (attributeText(afterDismiss) !== attributeText(after)) {
      throw new Error(
        `Dismissal repeated the reload: before=${attributeText(
          after
        )} after=${attributeText(afterDismiss)}`
      );
    }
  });
});
