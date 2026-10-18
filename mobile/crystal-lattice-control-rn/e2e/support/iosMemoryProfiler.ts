import { execFile, spawn, type ChildProcess } from "node:child_process";
import { once } from "node:events";
import fs from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const APP_BUNDLE_ID = "com.dynamicprogrammingsolutions.crystallatticecontrolrn";

export type MemorySample = {
  timestampMs: number;
  rssKb: number;
  phase: string;
};

export type IOSMemoryProfiler = {
  artifactDirectory: string;
  pid: number;
  mark: (
    phase: string,
    details?: Record<string, unknown>
  ) => Promise<MemorySample>;
  stop: () => Promise<void>;
};

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function findSimulatorAppPid(
  simulatorId: string,
  timeoutMs = 30_000
): Promise<number> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const result = await execFileAsync("xcrun", [
        "simctl",
        "spawn",
        simulatorId,
        "launchctl",
        "list",
      ]);
      const line = result.stdout
        .split(/\r?\n/)
        .find((candidate) => candidate.includes(APP_BUNDLE_ID));
      const pid = line ? Number(line.trim().split(/\s+/)[0]) : Number.NaN;
      if (Number.isInteger(pid) && pid > 0) {
        return pid;
      }
    } catch {
      // The app may still be registering with the Simulator launch service.
    }
    await delay(250);
  }
  throw new Error(
    `Unable to find ${APP_BUNDLE_ID} on Simulator ${simulatorId}.`
  );
}

async function readRssKb(pid: number): Promise<number> {
  const result = await execFileAsync("ps", ["-o", "rss=", "-p", String(pid)]);
  const rssKb = Number(result.stdout.trim());
  if (!Number.isFinite(rssKb)) {
    throw new Error(`No RSS value for process ${pid}: ${result.stdout}`);
  }
  return rssKb;
}

async function waitForExit(
  child: ChildProcess,
  timeoutMs: number
): Promise<boolean> {
  if (child.exitCode != null || child.signalCode != null) {
    return true;
  }
  return Promise.race([
    once(child, "exit").then(() => true),
    delay(timeoutMs).then(() => false),
  ]);
}

function startXctrace(options: {
  simulatorId: string;
  pid: number;
  artifactDirectory: string;
}): ChildProcess | null {
  if (process.env.CLC_MEMORY_XCTRACE !== "1") {
    return null;
  }

  const requestedTimeLimitSeconds = Number(
    process.env.CLC_MEMORY_XCTRACE_TIME_LIMIT_SECONDS ?? 45
  );
  const timeLimitSeconds = Math.min(
    120,
    Math.max(
      15,
      Number.isFinite(requestedTimeLimitSeconds)
        ? Math.round(requestedTimeLimitSeconds)
        : 45
    )
  );
  const requestedWindowSeconds = Number(
    process.env.CLC_MEMORY_XCTRACE_WINDOW_SECONDS ?? 20
  );
  const windowSeconds = Math.min(
    timeLimitSeconds,
    Math.max(
      10,
      Number.isFinite(requestedWindowSeconds)
        ? Math.round(requestedWindowSeconds)
        : 20
    )
  );
  const outputPath = path.join(options.artifactDirectory, "allocations.trace");
  const child = spawn(
    "xcrun",
    [
      "xctrace",
      "record",
      "--template",
      "Allocations",
      "--device",
      options.simulatorId,
      "--attach",
      String(options.pid),
      "--time-limit",
      `${timeLimitSeconds}s`,
      "--window",
      `${windowSeconds}s`,
      "--output",
      outputPath,
      "--no-prompt",
    ],
    {
      stdio: ["ignore", "pipe", "pipe"],
    }
  );
  child.stdout?.pipe(
    fs.createWriteStream(
      path.join(options.artifactDirectory, "xctrace.stdout.log")
    )
  );
  child.stderr?.pipe(
    fs.createWriteStream(
      path.join(options.artifactDirectory, "xctrace.stderr.log")
    )
  );
  return child;
}

export async function startIOSMemoryProfiler(options: {
  simulatorId: string;
  scenario: string;
  artifactRoot: string;
}): Promise<IOSMemoryProfiler> {
  const artifactDirectory = path.join(options.artifactRoot, options.scenario);
  fs.mkdirSync(artifactDirectory, { recursive: true });
  const samplesPath = path.join(artifactDirectory, "process-memory.csv");
  const phasesPath = path.join(artifactDirectory, "phases.jsonl");
  fs.writeFileSync(samplesPath, "timestamp_ms,rss_kb,phase\n", "utf8");
  const pid = await findSimulatorAppPid(options.simulatorId);
  let phase = "launched";
  let stopped = false;
  let sampleInFlight = false;

  const sample = async (): Promise<MemorySample> => {
    const next = {
      timestampMs: Date.now(),
      rssKb: await readRssKb(pid),
      phase,
    };
    fs.appendFileSync(
      samplesPath,
      `${next.timestampMs},${next.rssKb},${JSON.stringify(next.phase)}\n`,
      "utf8"
    );
    return next;
  };

  const timer = setInterval(() => {
    if (stopped || sampleInFlight) {
      return;
    }
    sampleInFlight = true;
    void sample()
      .catch((error) => {
        fs.appendFileSync(
          path.join(artifactDirectory, "sampler-errors.log"),
          `${new Date().toISOString()} ${String(error)}\n`,
          "utf8"
        );
      })
      .finally(() => {
        sampleInFlight = false;
      });
  }, 1000);

  const xctrace = startXctrace({
    simulatorId: options.simulatorId,
    pid,
    artifactDirectory,
  });
  await delay(3000);
  fs.writeFileSync(
    path.join(artifactDirectory, "profiler-start.json"),
    JSON.stringify(
      {
        pid,
        simulatorId: options.simulatorId,
        xctraceEnabled: xctrace != null,
        xctraceTimeLimitSeconds:
          xctrace != null
            ? Math.min(
                120,
                Math.max(
                  15,
                  Number(
                    process.env.CLC_MEMORY_XCTRACE_TIME_LIMIT_SECONDS ?? 45
                  ) || 45
                )
              )
            : null,
        xctraceExitedDuringStartup:
          xctrace != null &&
          (xctrace.exitCode != null || xctrace.signalCode != null),
      },
      null,
      2
    ),
    "utf8"
  );

  return {
    artifactDirectory,
    pid,
    mark: async (nextPhase: string, details: Record<string, unknown> = {}) => {
      phase = nextPhase;
      const next = await sample();
      fs.appendFileSync(
        phasesPath,
        `${JSON.stringify({ ...next, ...details })}\n`,
        "utf8"
      );
      return next;
    },
    stop: async () => {
      if (stopped) {
        return;
      }
      stopped = true;
      clearInterval(timer);
      try {
        await sample();
      } catch {
        // A crash or termination is also evidence; sampler-errors.log records it.
      }
      if (xctrace && xctrace.exitCode == null && xctrace.signalCode == null) {
        xctrace.kill("SIGINT");
        if (!(await waitForExit(xctrace, 45_000))) {
          xctrace.kill("SIGTERM");
          if (!(await waitForExit(xctrace, 10_000))) {
            xctrace.kill("SIGKILL");
            await waitForExit(xctrace, 5000);
          }
        }
      }
      fs.writeFileSync(
        path.join(artifactDirectory, "profiler-stop.json"),
        JSON.stringify(
          {
            pid,
            xctraceExitCode: xctrace?.exitCode ?? null,
            xctraceSignal: xctrace?.signalCode ?? null,
            traceExists: fs.existsSync(
              path.join(artifactDirectory, "allocations.trace")
            ),
          },
          null,
          2
        ),
        "utf8"
      );
    },
  };
}
