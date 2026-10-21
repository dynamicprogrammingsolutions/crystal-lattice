/// <reference types="detox" />

import * as detox from "detox";
import { expect as jestExpect } from "@jest/globals";

const detoxExpect = detox.expect;

type Frame = { x: number; y: number; width: number; height: number };
const longSessionId =
  "session-with-a-deliberately-long-identifier-for-native-truncation";

function frameFrom(attributes: any): Frame {
  const frame = attributes?.frame || attributes?.elementBounds;
  if (
    !frame ||
    typeof frame.x !== "number" ||
    typeof frame.y !== "number" ||
    typeof frame.width !== "number" ||
    typeof frame.height !== "number"
  ) {
    throw new Error(`Missing native frame: ${JSON.stringify(attributes)}`);
  }
  return frame;
}

function expectNoHorizontalOverlap(left: Frame, right: Frame): void {
  jestExpect(left.x + left.width).toBeLessThanOrEqual(right.x + 2);
}

async function dismissAndroidImmersiveModeConfirmation(): Promise<void> {
  if (device.getPlatform() !== "android") return;
  try {
    await system.element(by.system.label("Wait")).tap();
  } catch {
    // Some emulator images surface a transient system-process ANR dialog.
  }
  try {
    await system.element(by.system.label("Got it")).tap();
  } catch {
    // Fresh E2E images do not show this one-time Android system confirmation.
  }
}

async function launchHome(deleteData: boolean): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: deleteData,
    launchArgs: { clcHomeHarness: "1" },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id("home-harness-ready")))
    .toExist()
    .withTimeout(30000);
  await waitFor(element(by.id("home-screen-header")))
    .toBeVisible()
    .withTimeout(30000);
}

async function tapRecentWatch(connectionId: string, sessionId: string) {
  const watchAction = element(
    by.id(`home-recent-watch-${connectionId}-${sessionId}`)
  );
  await waitFor(watchAction)
    .toBeVisible()
    .whileElement(by.id("home-scroll"))
    .scroll(180, "down");
  await watchAction.tap();
}

describe("mobile Home Watchlist and recent sessions", () => {
  it("uses vertically reorderable tiles, inclusive recents, permanent notes, settings, and closed navigation", async () => {
    await launchHome(true);

    await detoxExpect(element(by.id("home-tab"))).toBeVisible();
    const menuFrame = frameFrom(await element(by.id("home-menu")).getAttributes());
    const accountFrame = frameFrom(await element(by.id("home-account-slot")).getAttributes());
    jestExpect(menuFrame.x).toBeLessThan(accountFrame.x);
    await detoxExpect(element(by.id("connections-tab"))).not.toExist();
    await detoxExpect(element(by.id("connections-screen-title"))).toBeVisible();
    await detoxExpect(element(by.id("sessions-tab"))).toBeVisible();
    await detoxExpect(element(by.id("messages-tab"))).toBeVisible();
    await waitFor(element(by.text("Recent Sessions")))
      .toBeVisible().whileElement(by.id("home-scroll")).scroll(180, "down");
    await detoxExpect(element(by.id("home-recent-timeline"))).toExist();
    await detoxExpect(element(by.text("Last 3 days"))).toBeVisible();
    await detoxExpect(element(by.text("Older laptop session"))).toExist();
    await detoxExpect(
      element(by.id("home-recent-title-office-shared"))
    ).toHaveText("Office shared session");
    await detoxExpect(
      element(by.id("home-recent-subtitle-office-shared"))
    ).not.toExist();

    const longRecent = element(by.id(`home-recent-office-${longSessionId}`));
    await waitFor(longRecent)
      .toBeVisible()
      .whileElement(by.id("home-scroll"))
      .scroll(180, "down");
    await detoxExpect(
      element(by.id(`home-recent-title-office-${longSessionId}`))
    ).toHaveText("A complete native session title");
    await detoxExpect(
      element(by.id(`home-recent-subtitle-office-${longSessionId}`))
    ).toHaveText("A complete native session subtitle");
    await detoxExpect(
      element(by.id(`home-recent-session-id-office-${longSessionId}`))
    ).toBeVisible();
    const recentConnection = frameFrom(
      await element(
        by.id(`home-recent-connection-office-${longSessionId}`)
      ).getAttributes()
    );
    const recentTime = frameFrom(
      await element(
        by.id(`home-recent-time-office-${longSessionId}`)
      ).getAttributes()
    );
    const recentActions = frameFrom(
      await element(
        by.id(`home-recent-note-office-${longSessionId}`)
      ).getAttributes()
    );
    expectNoHorizontalOverlap(recentConnection, recentTime);
    expectNoHorizontalOverlap(recentTime, recentActions);

    await waitFor(element(by.id("home-recent-open-laptop-older")))
      .toBeVisible()
      .whileElement(by.id("home-scroll"))
      .scroll(180, "down");
    await element(by.id("home-recent-open-laptop-older")).tap();
    await waitFor(element(by.id("home-harness-last-action")))
      .toHaveText("opened:laptop")
      .withTimeout(10000);
    await detoxExpect(element(by.id("messages-tab-content"))).toBeVisible();
    await element(by.id("home-tab")).tap();

    await tapRecentWatch("office", "shared");
    await tapRecentWatch("laptop", "shared");
    await tapRecentWatch("office", "project");
    await element(by.id("home-scroll")).scrollTo("top");
    await waitFor(element(by.id("home-watchlist-tile-office-project")))
      .toBeVisible().whileElement(by.id("home-scroll")).scroll(180, "down");
    await waitFor(element(by.id("home-watchlist-tile-office-shared")))
      .toBeVisible()
      .withTimeout(10000);
    await detoxExpect(element(by.id("home-recent-office-shared"))).toExist();

    const firstBefore = frameFrom(
      await element(by.id("home-watchlist-tile-office-shared")).getAttributes()
    );
    const secondBefore = frameFrom(
      await element(by.id("home-watchlist-tile-laptop-shared")).getAttributes()
    );
    jestExpect(Math.abs(firstBefore.y - secondBefore.y)).toBeLessThanOrEqual(2);
    jestExpect(firstBefore.x).toBeLessThan(secondBefore.x);
    jestExpect(
      Math.abs(firstBefore.width - secondBefore.width)
    ).toBeLessThanOrEqual(2);

    await element(by.id("home-watchlist-note-office-shared")).tap();
    await element(by.id("session-note-input")).replaceText(
      "Permanent shared note"
    );
    await element(by.id("session-note-save")).tap();
    await detoxExpect(
      element(by.id("home-watchlist-note-preview-office-shared"))
    ).toHaveText("Permanent shared note");
    await detoxExpect(
      element(by.id("home-watchlist-note-preview-laptop-shared"))
    ).toHaveText("Permanent shared note");

    const officeDragHandle = element(
      by.id("home-watchlist-drag-office-shared")
    );
    if (device.getPlatform() === "ios") {
      await officeDragHandle.longPressAndDrag(
        1000,
        Number.NaN,
        Number.NaN,
        element(by.id("home-watchlist-drag-office-project")),
        Number.NaN,
        Number.NaN,
        "slow",
        0
      );
    } else {
      await officeDragHandle.swipe("down", "slow", 0.35, 0.5, 0.5);
    }
    const firstAfter = frameFrom(
      await element(by.id("home-watchlist-tile-office-shared")).getAttributes()
    );
    const secondAfter = frameFrom(
      await element(by.id("home-watchlist-tile-laptop-shared")).getAttributes()
    );
    jestExpect(firstAfter.y).toBeGreaterThan(secondAfter.y);
    await detoxExpect(element(by.id("home-recent-office-shared"))).toExist();

    await element(by.id("home-menu")).tap();
    await element(by.id("home-menu-global-settings")).tap();
    await waitFor(element(by.id("global-settings-modal")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("global-settings-recent-sessions")).tap();
    const recent24Hours = element(by.id("options-picker-declared-24h"));
    await waitFor(recent24Hours).toBeVisible().withTimeout(10000);
    await recent24Hours.tap();
    await detoxExpect(
      element(by.id("global-settings-recent-sessions-value"))
    ).toHaveText("Last 24 hours");
    await element(by.id("global-settings-modal-close")).tap();
    await detoxExpect(element(by.text("Older laptop session"))).not.toExist();

    await launchHome(false);
    await waitFor(element(by.id("home-watchlist-tile-office-shared")))
      .toBeVisible().whileElement(by.id("home-scroll")).scroll(180, "down");
    await detoxExpect(
      element(by.id("home-watchlist-note-preview-office-shared"))
    ).toHaveText("Permanent shared note");
    const persistedFirst = frameFrom(
      await element(by.id("home-watchlist-tile-laptop-shared")).getAttributes()
    );
    const persistedSecond = frameFrom(
      await element(by.id("home-watchlist-tile-office-project")).getAttributes()
    );
    const persistedThird = frameFrom(
      await element(by.id("home-watchlist-tile-office-shared")).getAttributes()
    );
    jestExpect(persistedFirst.x).toBeLessThan(persistedSecond.x);
    jestExpect(
      Math.abs(persistedFirst.y - persistedSecond.y)
    ).toBeLessThanOrEqual(2);
    jestExpect(persistedThird.y).toBeGreaterThan(persistedFirst.y);
    await waitFor(element(by.text("Last 24 hours")))
      .toBeVisible().whileElement(by.id("home-scroll")).scroll(150, "down");
    await detoxExpect(element(by.id("home-recent-office-shared"))).toExist();

    await waitFor(element(by.id("home-watchlist-remove-office-shared")))
      .toBeVisible().whileElement(by.id("home-scroll")).scroll(120, "up");
    await element(by.id("home-watchlist-remove-office-shared")).tap();
    await detoxExpect(
      element(by.id("home-watchlist-tile-office-shared"))
    ).not.toExist();
    await detoxExpect(element(by.id("home-recent-office-shared"))).toExist();

    await tapRecentWatch("office", longSessionId);
    await element(by.id("home-scroll")).scrollTo("top");
    await waitFor(element(by.id(`home-watchlist-tile-office-${longSessionId}`)))
      .toBeVisible()
      .whileElement(by.id("home-scroll"))
      .scroll(180, "down");
    await detoxExpect(
      element(by.id(`home-watchlist-title-office-${longSessionId}`))
    ).toHaveText("A complete native session title");
    await detoxExpect(
      element(by.id(`home-watchlist-subtitle-office-${longSessionId}`))
    ).toHaveText("A complete native session subtitle");
    await detoxExpect(
      element(by.id(`home-watchlist-session-id-office-${longSessionId}`))
    ).toBeVisible();
    const watchConnection = frameFrom(
      await element(
        by.id(`home-watchlist-connection-office-${longSessionId}`)
      ).getAttributes()
    );
    const watchTime = frameFrom(
      await element(
        by.id(`home-watchlist-time-office-${longSessionId}`)
      ).getAttributes()
    );
    expectNoHorizontalOverlap(watchConnection, watchTime);
    await detoxExpect(
      element(by.id(`home-watchlist-note-office-${longSessionId}`))
    ).toBeVisible();
    await detoxExpect(
      element(by.id(`home-watchlist-remove-office-${longSessionId}`))
    ).toBeVisible();
  });
});
