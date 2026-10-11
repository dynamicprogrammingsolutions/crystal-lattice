/// <reference types="detox" />
import { expect as jestExpect } from "@jest/globals";
import { expect as detoxExpect } from "detox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import {
  startAcknowledgementProxy,
  startChatOperationsBackend,
} from "../../../test/fixture/chat-operations/backend";

type Frame = { x: number; y: number; width: number; height: number };
function frame(attributes: any): Frame {
  const value = attributes.frame ?? attributes.elementBounds;
  if (!value || typeof value.height !== "number")
    throw new Error(`Missing frame: ${JSON.stringify(attributes)}`);
  return value;
}

let started: Awaited<ReturnType<typeof startChatOperationsBackend>>;
let proxy: Awaited<ReturnType<typeof startAcknowledgementProxy>>;
let nativeScale = 1;

async function waitForStableFrame(identifier: string) {
  let previous: Frame | null = null;
  let stableReads = 0;
  const readings: Frame[] = [];
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    const current = frame(await element(by.id(identifier)).getAttributes());
    readings.push(current);
    stableReads =
      previous &&
      Math.abs(current.x - previous.x) < 0.5 &&
      Math.abs(current.y - previous.y) < 0.5 &&
      Math.abs(current.width - previous.width) < 0.5 &&
      Math.abs(current.height - previous.height) < 0.5
        ? stableReads + 1
        : 0;
    if (stableReads >= 2) return;
    previous = current;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(
    `Native layout did not settle for ${identifier}: ${JSON.stringify(
      readings.slice(-5)
    )}`
  );
}

async function openSession() {
  const host = device.getPlatform() === "android" ? "10.0.2.2" : "127.0.0.1";
  const sessions = await started.backend.listSessions();
  await device.launchApp({
    newInstance: true,
    launchArgs: {
      detoxEnableSynchronization: 0,
      clcChatOperationsBaseUrl: `http://${host}:${proxy.port}`,
      clcChatOperationsSessions: JSON.stringify(sessions),
      clcDisplayPreset: "largest",
    },
  });
  if (device.getPlatform() === "android") {
    const adb = promisify(execFile);
    const density = await adb("adb", [
      "-s",
      device.id,
      "shell",
      "wm",
      "density",
    ]);
    const densities = [...density.stdout.matchAll(/density:\s*(\d+)/g)];
    nativeScale = Number(densities[densities.length - 1][1]) / 160;
    for (let attempt = 0; attempt < 20; attempt += 1) {
      const result = await adb("adb", [
        "-s",
        device.id,
        "shell",
        "dumpsys",
        "window",
      ]);
      const systemAnr = result.stdout.includes(
        "Application Not Responding: com.android.systemui"
      );
      if (systemAnr || result.stdout.includes("ImmersiveModeConfirmation")) {
        await adb("adb", [
          "-s",
          device.id,
          "shell",
          "uiautomator",
          "dump",
          "/data/local/tmp/clc-chat-operations-ui.xml",
        ]);
        const tree = await adb("adb", [
          "-s",
          device.id,
          "shell",
          "cat",
          "/data/local/tmp/clc-chat-operations-ui.xml",
        ]);
        const text = systemAnr ? "Close app" : "Got it";
        const bounds = tree.stdout.match(
          new RegExp(
            `<node[^>]*text="${text}"[^>]*bounds="\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]"`
          )
        );
        if (!bounds)
          throw new Error(
            `Android setup overlay has no reachable ${text} control.`
          );
        await adb("adb", [
          "-s",
          device.id,
          "shell",
          "input",
          "tap",
          String((Number(bounds[1]) + Number(bounds[3])) / 2),
          String((Number(bounds[2]) + Number(bounds[4])) / 2),
        ]);
        if (!systemAnr) break;
      }
      await new Promise((resolve) => setTimeout(resolve, 150));
    }
  }
  await device.disableSynchronization();
  try {
    await waitFor(element(by.id("sessions-tab")))
      .toBeVisible()
      .withTimeout(30_000);
  } catch (error) {
    if (device.getPlatform() === "android") {
      const adb = promisify(execFile);
      const focus = await adb("adb", [
        "-s",
        device.id,
        "shell",
        "dumpsys",
        "window",
      ]);
      await adb("adb", [
        "-s",
        device.id,
        "shell",
        "uiautomator",
        "dump",
        "/data/local/tmp/clc-chat-operations-ui.xml",
      ]);
      const tree = await adb("adb", [
        "-s",
        device.id,
        "shell",
        "cat",
        "/data/local/tmp/clc-chat-operations-ui.xml",
      ]);
      console.log(
        focus.stdout
          .split("\n")
          .filter((line) => /mCurrentFocus|mFocusedApp/.test(line))
          .join("\n")
      );
      console.log(tree.stdout);
    }
    throw error;
  }
  await element(by.id("sessions-tab")).tap();
  await waitFor(element(by.id(`session-row-${started.sessions[0]}`)))
    .toBeVisible()
    .withTimeout(15_000);
  await element(by.id(`session-row-${started.sessions[0]}`)).tap();
  await waitFor(element(by.id("message-composer-input")))
    .toBeVisible()
    .withTimeout(15_000);
}

async function hideKeyboard() {
  if (device.getPlatform() === "android") {
    await element(by.id("message-composer-input")).tap();
  }
  await waitFor(element(by.id("composer-dismiss-keyboard")))
    .toBeVisible()
    .withTimeout(10_000);
  await waitForStableFrame("composer-dismiss-keyboard");
  for (let attempt = 0; attempt < 2; attempt += 1) {
    await element(by.id("composer-dismiss-keyboard")).tap();
    try {
      await waitFor(element(by.id("composer-dismiss-keyboard")))
        .not.toExist()
        .withTimeout(3000);
      return;
    } catch (error) {
      if (attempt === 1) throw error;
    }
  }
}

async function replaceComposerText(text: string) {
  const input = element(by.id("message-composer-input"));
  if (device.getPlatform() === "android") {
    await input.replaceText(text);
    return;
  }
  await waitForStableFrame("message-composer-input");
  const existing: any = await input.getAttributes();
  if (existing.text || existing.value) await input.clearText();
  await input.tap({ x: 12, y: 20 });
  await waitFor(element(by.id("composer-dismiss-keyboard")))
    .toBeVisible()
    .withTimeout(10_000);
  await waitForStableFrame("composer-dismiss-keyboard");
  await input.typeText(text);
}

async function assertGeometry(withStatus = false) {
  await waitForStableFrame("chat-composer");
  await waitForStableFrame("transcript-scroll-list");
  const listAttributes = await element(
    by.id("transcript-scroll-list")
  ).getAttributes();
  const headerAttributes = await element(
    by.id("messages-screen-header")
  ).getAttributes();
  const composerAttributes = await element(
    by.id("chat-composer")
  ).getAttributes();
  const transcript = frame(listAttributes);
  if (device.getPlatform() === "android") {
    transcript.x -= transcript.width;
    transcript.y -= transcript.height;
  }
  const header = frame(headerAttributes);
  const composer = frame(composerAttributes);
  const usable = composer.y + composer.height - header.y;
  jestExpect(transcript.height).toBeGreaterThanOrEqual(usable * 0.3);
  jestExpect(transcript.y + transcript.height).toBeLessThanOrEqual(
    composer.y + 2
  );
  if (withStatus) {
    const status = element(by.id("chat-activity-row"));
    const row = frame(await status.getAttributes());
    jestExpect(row.y + row.height).toBeLessThanOrEqual(transcript.y + 2);
    jestExpect(row.height).toBeLessThanOrEqual(56 * nativeScale);
  }
}

async function assertScrollAndHideKeyboard(withStatus = false) {
  await element(by.id("message-composer-input")).tap();
  await waitFor(element(by.id("composer-dismiss-keyboard")))
    .toBeVisible()
    .withTimeout(10_000);
  await assertGeometry(withStatus);
  await hideKeyboard();
  await assertScroll(withStatus);
}

async function assertScroll(withStatus = false) {
  try {
    await detoxExpect(element(by.id("transcript-message-0"))).toBeVisible();
  } catch {
    await waitFor(element(by.id("transcript-scroll-to-top")))
      .toBeVisible()
      .withTimeout(10_000);
    await element(by.id("transcript-scroll-to-top")).tap();
  }
  await waitFor(element(by.id("transcript-message-0")))
    .toBeVisible()
    .withTimeout(20_000);
  const before = frame(
    await element(by.id("transcript-message-0")).getAttributes()
  );
  await element(
    by.id(
      device.getPlatform() === "android"
        ? "transcript-message-0"
        : "transcript-scroll-list"
    )
  ).swipe("up", "slow", device.getPlatform() === "android" ? 0.2 : 0.35);
  const after = frame(
    await element(by.id("transcript-message-0")).getAttributes()
  );
  jestExpect(Math.abs(after.y - before.y)).toBeGreaterThan(10);
  await assertGeometry(withStatus);
}

describe("chat operations through production UI and HTTP", () => {
  beforeAll(async () => {
    started = await startChatOperationsBackend({
      messageCount: 24,
      streamChunkCount: device.getPlatform() === "android" ? 120 : 45,
    });
    proxy = await startAcknowledgementProxy(started.server, {
      editDelayMs: 15_000,
    });
  });
  afterEach(async () => {
    proxy.setRule("none");
    const status = await started.backend.getSessionRequestStatuses([
      started.sessions[0],
    ]);
    for (const request of status.statuses) {
      if (request.state === "running" && request.request_id) {
        await started.backend.cancelRequest(request.request_id);
      }
    }
  });
  afterAll(async () => {
    await proxy?.stop();
    await started?.server.stop();
  });

  it("shows request progress, permits scrolling, and clears progress after tab return", async () => {
    await openSession();
    await replaceComposerText("native mobile request");
    await hideKeyboard();
    await element(by.id("composer-send")).tap();
    await waitFor(element(by.id("chat-activity-progress")))
      .toBeVisible()
      .withTimeout(10_000);
    await assertScrollAndHideKeyboard(true);
    if (device.getPlatform() === "android") {
      await element(by.id("composer-cancel-request")).tap();
    }
    await element(by.id("sessions-tab")).tap();
    await element(by.id("messages-tab")).tap();
    await waitFor(element(by.id("composer-send-progress")))
      .not.toExist()
      .withTimeout(60_000);
    await device.takeScreenshot("chat-request-return");
  });

  it("edits in the composer, saves with progress, and restores the ordinary draft", async () => {
    proxy.setRule("delay-edit");
    await openSession();
    await replaceComposerText("native ordinary draft");
    await hideKeyboard();
    try {
      await detoxExpect(element(by.id("transcript-message-0"))).toBeVisible();
    } catch {
      await waitFor(element(by.id("transcript-scroll-to-top")))
        .toBeVisible()
        .withTimeout(15_000);
      await element(by.id("transcript-scroll-to-top")).tap();
    }
    await waitFor(element(by.id("transcript-message-0")))
      .toBeVisible()
      .withTimeout(60_000);
    await element(
      by.id("message-action-modify").withAncestor(by.id("transcript-message-0"))
    ).tap();
    await waitFor(element(by.id("composer-edit-label")))
      .toHaveText("Editing message [0]")
      .withTimeout(10_000);
    await replaceComposerText("native mobile edited message");
    await hideKeyboard();
    await element(by.id("sessions-tab")).tap();
    await element(by.id("messages-tab")).tap();
    await waitFor(element(by.id("composer-edit-label")))
      .toHaveText("Editing message [0]")
      .withTimeout(10_000);
    await detoxExpect(element(by.id("message-composer-input"))).toHaveText(
      "native mobile edited message"
    );
    await assertScrollAndHideKeyboard();
    await element(by.id("composer-send")).tap();
    await waitFor(element(by.id("composer-send-progress")))
      .toBeVisible()
      .withTimeout(10_000);
    await assertScroll(true);
    await waitFor(element(by.id("composer-edit-context")))
      .not.toExist()
      .withTimeout(30_000);
    await detoxExpect(element(by.id("message-composer-input"))).toHaveText(
      "native ordinary draft"
    );
    const result = await started.backend.listMessages(started.sessions[0], {});
    jestExpect(result.messages[0].message.content).toBe(
      "native mobile edited message"
    );
    await device.takeScreenshot("chat-edit-saved");
  });

  it("keeps failure compact, retries an accepted send, and cancels a later failure", async () => {
    await openSession();
    proxy.setRule(
      device.getPlatform() === "android"
        ? "reject-send-after"
        : "drop-send-after",
      1
    );
    await replaceComposerText("native uncertain mobile send");
    await hideKeyboard();
    await element(by.id("composer-send")).tap();
    await waitFor(element(by.id("chat-send-recovery")))
      .toBeVisible()
      .withTimeout(10_000);
    await assertScrollAndHideKeyboard(true);
    await element(by.id("chat-send-recovery-resend")).tap();
    await waitFor(element(by.id("chat-send-recovery")))
      .not.toExist()
      .withTimeout(15_000);
    if (device.getPlatform() === "android") {
      await element(by.id("composer-cancel-request")).tap();
    }
    await waitFor(element(by.id("composer-send-progress")))
      .not.toExist()
      .withTimeout(60_000);
    const result = await started.backend.listMessages(started.sessions[0], {});
    jestExpect(
      result.messages.filter(
        (entry) => entry.message.content === "native uncertain mobile send"
      )
    ).toHaveLength(1);
    proxy.setRule(
      device.getPlatform() === "android"
        ? "reject-send-before"
        : "drop-send-before",
      1
    );
    await replaceComposerText("native cancelled mobile draft");
    await hideKeyboard();
    await element(by.id("composer-send")).tap();
    await waitFor(element(by.id("chat-send-recovery")))
      .toBeVisible()
      .withTimeout(10_000);
    await assertGeometry(true);
    await element(by.id("chat-send-recovery-cancel")).tap();
    await detoxExpect(element(by.id("message-composer-input"))).toHaveText(
      "native cancelled mobile draft"
    );
    await detoxExpect(element(by.id("chat-send-recovery"))).not.toExist();
    await device.takeScreenshot("chat-recovery-cancelled");
  });
});
