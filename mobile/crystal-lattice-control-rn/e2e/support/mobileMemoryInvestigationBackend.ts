import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import {
  findRepoRoot,
  startBackendServer,
  type StartedServer,
} from "../../../../packages/frontend-sdk/src/integration/harness";

const MIN_SESSION_MESSAGES = 300;
const MIN_SESSION_BYTES = 5 * 1024 * 1024;
const MAX_SESSION_BYTES = 64 * 1024 * 1024;
const REQUIRED_SESSION_COUNT = 3;

type StoredSession = {
  session_id?: unknown;
  messages?: unknown;
  metadata?: unknown;
  [key: string]: unknown;
};

export type MemoryInvestigationSession = {
  label: "A" | "B" | "C";
  sessionId: string;
  sourceFilename: string;
  sourceBytes: number;
  messageCount: number;
  visibleTextBytes: number;
  agentId: string;
};

export type StartedMemoryInvestigationBackend = {
  server: StartedServer;
  sessions: MemoryInvestigationSession[];
  runtimeRoot: string;
  stop: () => Promise<void>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function utf8Bytes(value: unknown): number {
  return typeof value === "string" ? Buffer.byteLength(value, "utf8") : 0;
}

function visibleMessageBytes(messages: unknown[]): number {
  return messages.reduce<number>((total, candidate) => {
    if (!isRecord(candidate)) {
      return total;
    }
    const metadata = isRecord(candidate.metadata) ? candidate.metadata : {};
    const display = isRecord(metadata.display) ? metadata.display : {};
    return (
      total +
      utf8Bytes(candidate.content) +
      utf8Bytes(display.content) +
      utf8Bytes(metadata.reasoning)
    );
  }, 0);
}

function configuredSessionPaths(sessionsRoot: string): string[] | null {
  const configured = process.env.CLC_MEMORY_SESSION_IDS?.split(",")
    .map((value) => value.trim())
    .filter(Boolean);
  if (!configured || configured.length === 0) {
    return null;
  }
  if (configured.length < REQUIRED_SESSION_COUNT) {
    throw new Error(
      `CLC_MEMORY_SESSION_IDS must contain at least ${REQUIRED_SESSION_COUNT} session IDs.`
    );
  }
  return configured.slice(0, REQUIRED_SESSION_COUNT).map((sessionId) => {
    const candidate = path.join(sessionsRoot, `${sessionId}.json`);
    if (!fs.existsSync(candidate)) {
      throw new Error(`Configured session does not exist: ${candidate}`);
    }
    return candidate;
  });
}

function selectCandidatePaths(sessionsRoot: string): string[] {
  const configured = configuredSessionPaths(sessionsRoot);
  if (configured) {
    return configured;
  }

  const candidates = fs
    .readdirSync(sessionsRoot, { withFileTypes: true })
    .filter(
      (entry) =>
        entry.isFile() &&
        entry.name.endsWith(".json") &&
        !entry.name.includes(".tool-loop-conflict.")
    )
    .map((entry) => {
      const filename = path.join(sessionsRoot, entry.name);
      return {
        filename,
        size: fs.statSync(filename).size,
      };
    })
    .filter(
      (candidate) =>
        candidate.size >= MIN_SESSION_BYTES &&
        candidate.size <= MAX_SESSION_BYTES
    )
    .sort((left, right) => right.size - left.size);

  const selected: string[] = [];
  for (const candidate of candidates) {
    let parsed: StoredSession;
    try {
      parsed = JSON.parse(
        fs.readFileSync(candidate.filename, "utf8")
      ) as StoredSession;
    } catch {
      continue;
    }
    if (
      typeof parsed.session_id !== "string" ||
      !Array.isArray(parsed.messages) ||
      parsed.messages.length < MIN_SESSION_MESSAGES
    ) {
      continue;
    }
    selected.push(candidate.filename);
    if (selected.length === REQUIRED_SESSION_COUNT) {
      return selected;
    }
  }

  throw new Error(
    `Expected ${REQUIRED_SESSION_COUNT} sessions with at least ` +
      `${MIN_SESSION_MESSAGES} messages and ${MIN_SESSION_BYTES} bytes under ` +
      `${sessionsRoot}, found ${selected.length}.`
  );
}

function prepareSessionCopy(options: {
  sourcePath: string;
  destinationRoot: string;
  label: "A" | "B" | "C";
  modifiedAtMs: number;
}): MemoryInvestigationSession {
  const sourceText = fs.readFileSync(options.sourcePath, "utf8");
  const parsed = JSON.parse(sourceText) as StoredSession;
  if (
    typeof parsed.session_id !== "string" ||
    !Array.isArray(parsed.messages)
  ) {
    throw new Error(`Invalid stored session: ${options.sourcePath}`);
  }

  const metadata = isRecord(parsed.metadata) ? parsed.metadata : {};
  const agentId =
    typeof metadata.agent_id === "string" && metadata.agent_id.trim()
      ? metadata.agent_id
      : "default";
  const prepared: StoredSession = {
    ...parsed,
    metadata: {
      ...metadata,
      agent_id: agentId,
      archived: false,
      notifications: [],
      overrides: {},
      pinned: false,
      status: "done",
      subtitle: `${parsed.messages.length} messages`,
      title: `Memory investigation ${options.label}`,
    },
  };
  const destination = path.join(
    options.destinationRoot,
    `${parsed.session_id}.json`
  );
  fs.writeFileSync(destination, JSON.stringify(prepared), "utf8");
  const modifiedAt = new Date(options.modifiedAtMs);
  fs.utimesSync(destination, modifiedAt, modifiedAt);

  return {
    label: options.label,
    sessionId: parsed.session_id,
    sourceFilename: path.basename(options.sourcePath),
    sourceBytes: Buffer.byteLength(sourceText, "utf8"),
    messageCount: parsed.messages.length,
    visibleTextBytes: visibleMessageBytes(parsed.messages),
    agentId,
  };
}

export async function startMemoryInvestigationBackend(
  artifactRoot: string
): Promise<StartedMemoryInvestigationBackend> {
  const repoRoot = findRepoRoot(process.cwd());
  const sourceSessionsRoot = path.join(repoRoot, ".crystal", "sessions");
  const runtimeRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "clc-mobile-memory-investigation-")
  );
  const sessionsRoot = path.join(runtimeRoot, "sessions");
  const configPath = path.join(runtimeRoot, "config.json");
  fs.mkdirSync(sessionsRoot, { recursive: true });
  fs.mkdirSync(artifactRoot, { recursive: true });

  const labels = ["A", "B", "C"] as const;
  const sourcePaths = selectCandidatePaths(sourceSessionsRoot);
  const now = Date.now();
  const sessions = sourcePaths.map((sourcePath, index) =>
    prepareSessionCopy({
      sourcePath,
      destinationRoot: sessionsRoot,
      label: labels[index],
      modifiedAtMs: now - index * 1000,
    })
  );
  const agentIds = [...new Set(sessions.map((session) => session.agentId))];
  const config = {
    default_agent: agentIds[0],
    agents: Object.fromEntries(
      agentIds.map((agentId) => [
        agentId,
        {
          provider: "deterministic_stream",
          model: "memory-investigation",
        },
      ])
    ),
    plugins: [
      "plugins.deterministic_stream_provider.DeterministicStreamProvider",
    ],
  };
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2), "utf8");
  fs.writeFileSync(
    path.join(artifactRoot, "selected-sessions.json"),
    JSON.stringify(sessions, null, 2),
    "utf8"
  );

  try {
    const server = await startBackendServer({
      config,
      configPath,
      sessionsRoot,
      startupTimeoutMs: 120_000,
    });
    return {
      server,
      sessions,
      runtimeRoot,
      stop: async () => {
        await server.stop();
        fs.rmSync(runtimeRoot, { recursive: true, force: true });
      },
    };
  } catch (error) {
    fs.rmSync(runtimeRoot, { recursive: true, force: true });
    throw error;
  }
}
