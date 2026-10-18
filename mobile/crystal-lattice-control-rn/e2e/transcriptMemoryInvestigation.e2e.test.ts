/// <reference types="detox" />

import fs from "node:fs";
import path from "node:path";

import { expect as jestExpect } from "@jest/globals";

import {
  startMemoryInvestigationBackend,
  type MemoryInvestigationSession,
  type StartedMemoryInvestigationBackend,
} from "./support/mobileMemoryInvestigationBackend";
import {
  startIOSMemoryProfiler,
  type IOSMemoryProfiler,
  type MemorySample,
} from "./support/iosMemoryProfiler";

jest.setTimeout(30 * 60 * 1000);

const SETTLE_MS = Number(process.env.CLC_MEMORY_SETTLE_MS ?? 8000);
const MAX_SWIPES_PER_WINDOW = Number(
  process.env.CLC_MEMORY_MAX_SWIPES_PER_WINDOW ?? 30
);
const A_EXPANSIONS = Number(process.env.CLC_MEMORY_A_EXPANSIONS ?? 5);
const C_EXPANSIONS = Number(process.env.CLC_MEMORY_C_EXPANSIONS ?? 2);

type RangeWindow = {
  start: number;
  end: number;
};

type ScenarioResults = Record<string, MemorySample>;

let started: StartedMemoryInvestigationBackend;
let artifactRoot: string;

function pause(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function createRunId(): string {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function defaultRange(session: MemoryInvestigationSession): RangeWindow {
  return {
    start: Math.max(0, session.messageCount - 50),
    end: session.messageCount,
  };
}

function expandOlder(range: RangeWindow): RangeWindow {
  const count = range.end - range.start;
  if (count < 100) {
    return {
      start: Math.max(0, range.start - 50),
      end: range.end,
    };
  }
  return {
    start: Math.max(0, range.start - 50),
    end: Math.max(100, range.end - 50),
  };
}

async function launchFreshApp(): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: true,
    launchArgs: { detoxEnableSynchronization: "0" },
  });
  await device.disableSynchronization();
  await waitFor(element(by.id("connections-new-connection")))
    .toBeVisible()
    .withTimeout(60_000);
}

async function connectToFixture(port: number): Promise<void> {
  await element(by.id("connections-new-connection")).tap();
  await waitFor(element(by.id("connection-wizard-modal")))
    .toBeVisible()
    .withTimeout(15_000);
  await pause(750);
  await waitFor(element(by.id("connection-method-manual")))
    .toBeVisible()
    .withTimeout(15_000);
  await element(by.id("connection-method-manual")).tap();
  await pause(750);
  await waitFor(element(by.id("manual-host-input")))
    .toBeVisible()
    .withTimeout(30_000);
  await element(by.id("manual-host-input")).replaceText("127.0.0.1");
  await element(by.id("manual-port-input")).replaceText(String(port));
  let connected = false;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await element(by.id("manual-connect-button")).tap();
    try {
      await waitFor(element(by.id("connection-wizard-modal")))
        .not.toExist()
        .withTimeout(20_000);
      connected = true;
      break;
    } catch {
      try {
        await element(by.text("OK")).tap();
      } catch {
        // A transient request may still be settling without an alert.
      }
      await pause(1000);
    }
  }
  if (!connected) {
    throw new Error("Unable to connect to the memory investigation backend.");
  }
  await pause(1000);
  await waitFor(element(by.id("sessions-tab")))
    .toBeVisible()
    .withTimeout(15_000);
  await element(by.id("sessions-tab")).tap();
  await waitFor(element(by.id("sessions-screen-title")))
    .toBeVisible()
    .withTimeout(60_000);
}

async function openSession(
  session: MemoryInvestigationSession,
  expectedVisibleIndex: number | null = session.messageCount - 1
): Promise<void> {
  await element(by.id("sessions-tab")).tap();
  await waitFor(element(by.id("sessions-list")))
    .toBeVisible()
    .withTimeout(30_000);
  await element(by.id("sessions-list")).scrollTo("top");
  const row = element(by.id(`session-row-${session.sessionId}`));
  await waitFor(row)
    .toBeVisible()
    .whileElement(by.id("sessions-list"))
    .scroll(300, "down");
  await row.tap();
  await waitFor(element(by.id("message-composer-input")))
    .toBeVisible()
    .withTimeout(120_000);
  if (expectedVisibleIndex != null) {
    await waitFor(element(by.id(`transcript-message-${expectedVisibleIndex}`)))
      .toExist()
      .withTimeout(120_000);
  }
}

async function backToSessions(): Promise<void> {
  await element(by.id("messages-back-to-sessions")).tap();
  await waitFor(element(by.id("sessions-screen-title")))
    .toBeVisible()
    .withTimeout(60_000);
}

async function isVisible(testId: string): Promise<boolean> {
  try {
    const attributes = (await element(by.id(testId)).getAttributes()) as {
      visible?: boolean;
      hittable?: boolean;
    };
    return attributes.visible !== false && attributes.hittable !== false;
  } catch {
    return false;
  }
}

async function traverseCurrentWindowToTop(): Promise<void> {
  const list = element(by.id("transcript-scroll-list"));
  for (let swipe = 0; swipe < MAX_SWIPES_PER_WINDOW; swipe += 1) {
    if (await isVisible("transcript-range-top-expandAbove")) {
      break;
    }
    await list.swipe("down", "slow", 0.75);
  }

  if (!(await isVisible("transcript-range-top-expandAbove"))) {
    try {
      await waitFor(element(by.id("transcript-scroll-to-top")))
        .toBeVisible()
        .withTimeout(30_000);
    } catch {
      // Momentum may have reached the range controls while the helper changed.
    }
    if (
      !(await isVisible("transcript-range-top-expandAbove")) &&
      (await isVisible("transcript-scroll-to-top"))
    ) {
      await element(by.id("transcript-scroll-to-top")).tap();
    }
  }
  await waitFor(element(by.id("transcript-range-top-expandAbove")))
    .toBeVisible()
    .withTimeout(30_000);
}

async function tapExpandAbove(): Promise<void> {
  const button = element(by.id("transcript-range-top-expandAbove"));
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await traverseCurrentWindowToTop();
    await pause(750);
    try {
      await waitFor(button).toBeVisible().withTimeout(5000);
      await button.tap();
      return;
    } catch {
      // Range loading and anchor restoration can briefly move the footer cell.
    }
  }
  throw new Error("Unable to activate the older-history range control.");
}

async function traverseOlderHistory(options: {
  session: MemoryInvestigationSession;
  expansions: number;
  profiler: IOSMemoryProfiler;
  phasePrefix: string;
  results: ScenarioResults;
}): Promise<RangeWindow> {
  let range = defaultRange(options.session);
  for (let step = 0; step <= options.expansions; step += 1) {
    try {
      await traverseCurrentWindowToTop();
    } catch (error) {
      options.results[`${options.phasePrefix}-navigation-stalled`] =
        await options.profiler.mark(
          `${options.phasePrefix}-navigation-stalled`,
          {
            sessionLabel: options.session.label,
            sessionId: options.session.sessionId,
            loadedStart: range.start,
            loadedEnd: range.end,
            loadedCount: range.end - range.start,
            error: error instanceof Error ? error.message : String(error),
          }
        );
      break;
    }
    options.results[`${options.phasePrefix}-window-${step}-top`] =
      await options.profiler.mark(`${options.phasePrefix}-window-${step}-top`, {
        sessionLabel: options.session.label,
        sessionId: options.session.sessionId,
        loadedStart: range.start,
        loadedEnd: range.end,
        loadedCount: range.end - range.start,
        sourceMessageCount: options.session.messageCount,
      });
    if (step === options.expansions) {
      break;
    }

    const priorStart = range.start;
    try {
      await tapExpandAbove();
    } catch (error) {
      options.results[`${options.phasePrefix}-navigation-stalled`] =
        await options.profiler.mark(
          `${options.phasePrefix}-navigation-stalled`,
          {
            sessionLabel: options.session.label,
            sessionId: options.session.sessionId,
            loadedStart: range.start,
            loadedEnd: range.end,
            loadedCount: range.end - range.start,
            error: error instanceof Error ? error.message : String(error),
          }
        );
      break;
    }
    range = expandOlder(range);
    await waitFor(element(by.id(`transcript-message-${priorStart}`)))
      .toExist()
      .withTimeout(120_000);
    await pause(1500);
  }
  return range;
}

async function markSettled(options: {
  profiler: IOSMemoryProfiler;
  results: ScenarioResults;
  phase: string;
  details: Record<string, unknown>;
}): Promise<void> {
  await options.profiler.mark(`${options.phase}-settling`, options.details);
  await pause(SETTLE_MS);
  options.results[options.phase] = await options.profiler.mark(
    options.phase,
    options.details
  );
}

async function runProfiledScenario(
  scenario: string,
  run: (profiler: IOSMemoryProfiler, results: ScenarioResults) => Promise<void>
): Promise<ScenarioResults> {
  await launchFreshApp();
  const profiler = await startIOSMemoryProfiler({
    simulatorId: device.id,
    scenario,
    artifactRoot,
  });
  const results: ScenarioResults = {};
  try {
    await profiler.mark(`${scenario}-launched`);
    const health = await fetch(`${started.server.baseUrl}/api/hello`);
    if (!health.ok) {
      throw new Error(`Fixture backend health check failed: ${health.status}`);
    }
    await connectToFixture(started.server.port);
    await profiler.mark(`${scenario}-connected`);
    await run(profiler, results);
    return results;
  } finally {
    await profiler.stop();
    await device.terminateApp();
  }
}

describe("multi-session transcript memory investigation", () => {
  beforeAll(async () => {
    if (device.getPlatform() !== "ios") {
      throw new Error(
        "This investigation currently targets the iOS Simulator."
      );
    }
    const runId = process.env.CLC_MEMORY_RUN_ID ?? createRunId();
    artifactRoot = path.resolve(
      process.cwd(),
      "artifacts",
      "detox",
      "memory-investigation",
      runId
    );
    fs.mkdirSync(artifactRoot, { recursive: true });
    fs.writeFileSync(
      path.join(path.dirname(artifactRoot), ".metadata_never_index"),
      "",
      "utf8"
    );
    started = await startMemoryInvestigationBackend(artifactRoot);
    console.log(`Memory investigation artifacts: ${artifactRoot}`);
  });

  afterAll(async () => {
    await started?.stop();
  });

  it("compares fresh B with B after heavy A and C histories", async () => {
    const [sessionA, sessionB, sessionC] = started.sessions;
    const control = await runProfiledScenario(
      "control-b",
      async (profiler, results) => {
        await openSession(sessionB);
        await markSettled({
          profiler,
          results,
          phase: "control-b-settled",
          details: {
            sessionLabel: sessionB.label,
            sessionId: sessionB.sessionId,
            loadedCount: 50,
            sourceMessageCount: sessionB.messageCount,
          },
        });
      }
    );

    const experimental = await runProfiledScenario(
      "multi-session",
      async (profiler, results) => {
        await openSession(sessionA);
        const aRange = await traverseOlderHistory({
          session: sessionA,
          expansions: A_EXPANSIONS,
          profiler,
          phasePrefix: "experimental-a",
          results,
        });
        await markSettled({
          profiler,
          results,
          phase: "experimental-a-heavy-settled",
          details: {
            sessionLabel: sessionA.label,
            sessionId: sessionA.sessionId,
            loadedStart: aRange.start,
            loadedEnd: aRange.end,
            loadedCount: aRange.end - aRange.start,
          },
        });

        await backToSessions();
        await openSession(sessionB);
        await markSettled({
          profiler,
          results,
          phase: "experimental-b-after-a-settled",
          details: {
            sessionLabel: sessionB.label,
            sessionId: sessionB.sessionId,
            loadedCount: 50,
            sourceMessageCount: sessionB.messageCount,
          },
        });

        await backToSessions();
        await openSession(sessionC);
        const cRange = await traverseOlderHistory({
          session: sessionC,
          expansions: C_EXPANSIONS,
          profiler,
          phasePrefix: "experimental-c",
          results,
        });
        await markSettled({
          profiler,
          results,
          phase: "experimental-c-heavy-settled",
          details: {
            sessionLabel: sessionC.label,
            sessionId: sessionC.sessionId,
            loadedStart: cRange.start,
            loadedEnd: cRange.end,
            loadedCount: cRange.end - cRange.start,
          },
        });

        await backToSessions();
        await openSession(sessionB);
        await markSettled({
          profiler,
          results,
          phase: "experimental-b-after-a-c-settled",
          details: {
            sessionLabel: sessionB.label,
            sessionId: sessionB.sessionId,
            loadedCount: 50,
            sourceMessageCount: sessionB.messageCount,
          },
        });

        await backToSessions();
        await openSession(sessionA, null);
        await markSettled({
          profiler,
          results,
          phase: "experimental-a-reopened-settled",
          details: {
            sessionLabel: sessionA.label,
            sessionId: sessionA.sessionId,
            loadedCount: aRange.end - aRange.start,
            sourceMessageCount: sessionA.messageCount,
          },
        });
      }
    );

    const controlB = control["control-b-settled"].rssKb;
    const bAfterA = experimental["experimental-b-after-a-settled"].rssKb;
    const bAfterAC = experimental["experimental-b-after-a-c-settled"].rssKb;
    const summary = {
      generatedAt: new Date().toISOString(),
      simulatorId: device.id,
      renderer: {
        markdown: "react-native-markdown-display",
        codeBlock: "selectable-native",
        source: "fresh-install defaults",
      },
      sessions: started.sessions,
      control,
      experimental,
      comparison: {
        controlBMb: controlB / 1024,
        bAfterAMb: bAfterA / 1024,
        bAfterACMb: bAfterAC / 1024,
        bAfterAMinusControlMb: (bAfterA - controlB) / 1024,
        bAfterACMinusControlMb: (bAfterAC - controlB) / 1024,
      },
    };
    fs.writeFileSync(
      path.join(artifactRoot, "summary.json"),
      JSON.stringify(summary, null, 2),
      "utf8"
    );
    console.log(
      `Memory investigation summary: ${JSON.stringify(summary.comparison)}`
    );

    jestExpect(Number.isFinite(summary.comparison.controlBMb)).toBe(true);
    jestExpect(Number.isFinite(summary.comparison.bAfterAMinusControlMb)).toBe(
      true
    );
  });
});
