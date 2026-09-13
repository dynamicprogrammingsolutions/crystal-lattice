/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

function verticalPosition(attributes: any): number {
  const bounds = attributes?.frame || attributes?.elementBounds;
  const value = bounds?.y ?? bounds?.top;
  if (typeof value !== "number") {
    throw new Error(
      `Element attributes do not contain vertical bounds: ${JSON.stringify(
        attributes
      )}`
    );
  }
  return value;
}

function verticalBounds(attributes: any): {
  top: number;
  bottom: number;
  height: number;
} {
  const bounds = attributes?.frame || attributes?.elementBounds;
  const top = bounds?.y ?? bounds?.top;
  const height = bounds?.height;
  if (typeof top !== "number" || typeof height !== "number") {
    throw new Error(
      `Element attributes do not contain vertical bounds: ${JSON.stringify(
        attributes
      )}`
    );
  }
  return { top, bottom: top + height, height };
}

function frameFrom(attributes: any): {
  x: number;
  y: number;
  width: number;
  height: number;
} {
  const frame = attributes?.frame || attributes?.elementBounds;
  if (
    !frame ||
    typeof frame.x !== "number" ||
    typeof frame.y !== "number" ||
    typeof frame.width !== "number" ||
    typeof frame.height !== "number"
  ) {
    throw new Error(
      `Element attributes do not contain a frame: ${JSON.stringify(attributes)}`
    );
  }
  return frame;
}

async function dismissAndroidImmersiveModeConfirmation(): Promise<void> {
  if (device.getPlatform() !== "android") {
    return;
  }
  try {
    await system.element(by.system.label("Got it")).tap();
  } catch {
    // Fresh E2E images do not show this one-time Android system confirmation.
  }
}

async function launchHarness(
  displayPreset: "default" | "largest" = "default"
): Promise<void> {
  await device.launchApp({
    newInstance: true,
    resetAppState: true,
    launchArgs: {
      clcSessionListHarness: "1",
      clcDisplayPreset: displayPreset,
    },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id("session-list-harness-ready")))
    .toExist()
    .withTimeout(30000);
  await waitFor(element(by.id("session-list-harness-watchlist-state")))
    .toHaveText("not-watched")
    .withTimeout(10000);
}

describe("mobile session-list contracts", () => {
  it("keeps session-card fields ordered and grows from the default to largest preset", async () => {
    await launchHarness();

    const defaultRow = verticalBounds(
      await element(by.id("session-row-server-first")).getAttributes()
    );
    const screenTitleAttributes = await element(
      by.id("sessions-screen-title")
    ).getAttributes();
    const cardTitleAttributes = await element(
      by.id("session-title-server-first")
    ).getAttributes();
    const screenTitleFrame =
      (screenTitleAttributes as any)?.frame ||
      (screenTitleAttributes as any)?.elementBounds;
    const cardTitleFrame =
      (cardTitleAttributes as any)?.frame ||
      (cardTitleAttributes as any)?.elementBounds;
    if (
      typeof screenTitleFrame?.x !== "number" ||
      typeof cardTitleFrame?.x !== "number" ||
      Math.abs(screenTitleFrame.x - cardTitleFrame.x) > 1
    ) {
      throw new Error(
        `Expected Sessions title and card title left edges to align: ${JSON.stringify(
          {
            screenTitleFrame,
            cardTitleFrame,
          }
        )}`
      );
    }
    const headerFrame = frameFrom(
      await element(by.id("sessions-screen-header")).getAttributes()
    );
    const overflowFrame = frameFrom(
      await element(by.id("sessions-actions-menu")).getAttributes()
    );
    if (
      overflowFrame.x < headerFrame.x ||
      overflowFrame.x + overflowFrame.width > headerFrame.x + headerFrame.width
    ) {
      throw new Error(
        `Expected the overflow trigger inside the Sessions header: ${JSON.stringify(
          {
            headerFrame,
            overflowFrame,
          }
        )}`
      );
    }
    if (screenTitleFrame.x + screenTitleFrame.width > overflowFrame.x) {
      throw new Error(
        `Expected the shrinking connection title not to overlap the overflow trigger: ${JSON.stringify(
          {
            screenTitleFrame,
            overflowFrame,
          }
        )}`
      );
    }

    await element(by.id("sessions-actions-menu")).tap();
    await detoxExpect(element(by.text("Toggle archive"))).toBeVisible();
    await element(by.id("actions-menu-close")).tap();
    const fieldIds = [
      "session-title-server-first",
      "session-id-server-first",
      "session-subtitle-server-first",
      "session-meta-server-first",
    ];
    const defaultFields = [];
    for (const fieldId of fieldIds) {
      defaultFields.push(
        verticalBounds(await element(by.id(fieldId)).getAttributes())
      );
    }
    for (let index = 1; index < defaultFields.length; index += 1) {
      if (defaultFields[index - 1].bottom > defaultFields[index].top) {
        throw new Error(
          `Expected ${fieldIds[index - 1]} above ${
            fieldIds[index]
          }: ${JSON.stringify(defaultFields)}`
        );
      }
    }
    await detoxExpect(
      element(by.id("session-preview-server-second"))
    ).toExist();

    await launchHarness("largest");
    const largestRow = verticalBounds(
      await element(by.id("session-row-server-first")).getAttributes()
    );
    if (largestRow.height <= defaultRow.height) {
      throw new Error(
        `Expected largest preset row to grow: ${largestRow.height} <= ${defaultRow.height}`
      );
    }
    const largestFields = [];
    for (const fieldId of fieldIds) {
      largestFields.push(
        verticalBounds(await element(by.id(fieldId)).getAttributes())
      );
    }
    for (let index = 1; index < largestFields.length; index += 1) {
      if (largestFields[index - 1].bottom > largestFields[index].top) {
        throw new Error(
          `Expected ${fieldIds[index - 1]} above ${
            fieldIds[index]
          } at largest preset: ${JSON.stringify(largestFields)}`
        );
      }
    }
  });

  it("renders the native list and runs a rich status action through its modal", async () => {
    await launchHarness();

    await waitFor(element(by.id("session-title-server-first")))
      .toBeVisible()
      .withTimeout(30000);

    const firstAttributes = await element(
      by.id("session-row-server-first")
    ).getAttributes();
    const secondAttributes = await element(
      by.id("session-row-server-second")
    ).getAttributes();
    const firstY = verticalPosition(firstAttributes);
    const secondY = verticalPosition(secondAttributes);
    if (firstY >= secondY) {
      throw new Error(
        `Expected server-first above server-second, got ${firstY} >= ${secondY}`
      );
    }

    await element(by.id("session-actions-menu-server-first")).tap();
    const watchlistAction = element(
      by.id("actions-menu-action-localWatchlist")
    );
    await waitFor(watchlistAction).toBeVisible().withTimeout(30000);
    await watchlistAction.tap();
    await waitFor(element(by.id("session-list-harness-watchlist-state")))
      .toHaveText("watched")
      .withTimeout(10000);

    await element(by.id("session-actions-menu-server-first")).tap();
    await detoxExpect(
      element(by.id("actions-menu-action-localWatchlist"))
    ).toHaveLabel("Remove from Watchlist");
    await waitFor(element(by.id("actions-menu-action-set_session_status")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("actions-menu-action-set_session_status")).tap();

    await waitFor(
      element(by.id("session-rich-list-server-first-set_session_status"))
    )
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(
      element(by.id("application-action-dialog-primary"))
    ).not.toExist();
    await element(
      by.id("session-rich-list-server-first-set_session_status-option-todo")
    ).tap();
    await waitFor(element(by.id("session-list-harness-submission")))
      .toHaveText("server-first:set_session_status:todo")
      .withTimeout(30000);
  });
});
