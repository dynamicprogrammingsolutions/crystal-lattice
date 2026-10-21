import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import type { AddressInfo } from "node:net";
import {
  FetchTransport,
  RestAgentBackend,
} from "../../../packages/frontend-sdk/src";
import {
  findRepoRoot,
  startBackendServer,
  type StartedServer,
} from "../../../packages/frontend-sdk/src/integration/harness";

export const CHAT_OPERATIONS_CONFIG = {
  providers: {
    deterministic: {
      provider: "deterministic_stream",
      model: "test-model",
      timeout: 180,
      stream_chunk_count: 6,
      stream_chunk_delay_ms: 1000,
    },
  },
  agents: { default: { provider: "deterministic" } },
  plugins: [
    "plugins.deterministic_stream_provider.DeterministicStreamProvider",
    "path:${env:REPO_ROOT}/test/fixture/chat-operations",
  ],
};

export async function startChatOperationsBackend(
  options: {
    messageCount?: number;
    streamChunkCount?: number;
    firstMessageParts?: any[];
  } = {}
) {
  const server = await startChatOperationsServer({
    streamChunkCount: options.streamChunkCount,
  });
  const backend = new RestAgentBackend({
    transport: new FetchTransport({ baseUrl: server.baseUrl }),
  });
  const sessions: string[] = [];
  for (let sessionNumber = 0; sessionNumber < 4; sessionNumber += 1) {
    const created = await backend.createSession({ agentId: "default" });
    sessions.push(created.session.session_id);
  }
  for (let index = 0; index < (options.messageCount ?? 24); index += 1) {
    await backend.appendMessage(sessions[0], {
      role: index === 2 ? "system" : index % 2 === 0 ? "user" : "assistant",
      content: `Message ${index}: a scrollable transcript line.\nMore content in message ${index}.`,
      metadata: { fixture: index },
      ...(index === 0 && options.firstMessageParts
        ? { multipartContent: options.firstMessageParts }
        : {}),
    });
  }
  return { server, backend, sessions };
}

export async function startChatOperationsServer(
  options: Omit<Parameters<typeof startBackendServer>[0], "config"> & {
    streamChunkCount?: number;
  } = {}
) {
  const fixtureRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "clc-chat-operations-plugin-")
  );
  const source = path.join(
    findRepoRoot(process.cwd()),
    "test/fixture/chat-operations"
  );
  for (const filename of [
    "agent_plugin.json",
    "pyproject.toml",
    "chat_operations_fixture.py",
  ]) {
    fs.copyFileSync(
      path.join(source, filename),
      path.join(fixtureRoot, filename)
    );
  }
  try {
    const server = await startBackendServer({
      ...options,
      config: {
        ...CHAT_OPERATIONS_CONFIG,
        providers: {
          deterministic: {
            ...CHAT_OPERATIONS_CONFIG.providers.deterministic,
            stream_chunk_count: options.streamChunkCount ?? 6,
          },
        },
        plugins: [CHAT_OPERATIONS_CONFIG.plugins[0], `path:${fixtureRoot}`],
      },
      startupTimeoutMs: options.startupTimeoutMs ?? 30_000,
    });
    return {
      ...server,
      stop: async () => {
        await server.stop();
        fs.rmSync(fixtureRoot, { recursive: true, force: true });
      },
    };
  } catch (error) {
    fs.rmSync(fixtureRoot, { recursive: true, force: true });
    throw error;
  }
}

export type AcknowledgementRule =
  | "none"
  | "drop-send-before"
  | "drop-send-after"
  | "delay-edit"
  | "reject-edit-before"
  | "reject-send-before"
  | "reject-send-after";

export async function startAcknowledgementProxy(
  server: StartedServer,
  options: { editDelayMs?: number } = {}
) {
  let rule: AcknowledgementRule = "none";
  let remaining = Infinity;
  let sendRules: AcknowledgementRule[] = [];
  const timers = new Set<ReturnType<typeof setTimeout>>();
  const sockets = new Set<import("node:net").Socket>();
  const receipts: { method: string; path: string; stage: string }[] = [];
  const proxy = http.createServer((request, response) => {
    const record = (stage: string) =>
      receipts.push({
        method: request.method ?? "",
        path: request.url ?? "",
        stage,
      });
    record("received");
    response.on("finish", () => record("delivered"));
    const rejectSend = () => {
      response.writeHead(503, { "content-type": "application/json" });
      response.end(
        JSON.stringify({ detail: "Send acknowledgement unavailable." })
      );
    };
    const isSend =
      request.method === "POST" &&
      /\/sessions\/[^/]+\/send(?:_message)?$/.test(request.url ?? "");
    const isEdit =
      request.method === "PATCH" &&
      /\/sessions\/[^/]+\/messages\/\d+$/.test(request.url ?? "");
    const appliedRule =
      isSend && sendRules.length > 0
        ? sendRules.shift()!
        : remaining > 0
        ? rule
        : "none";
    if (isSend && appliedRule !== "none" && appliedRule !== "delay-edit")
      remaining -= 1;
    if (isEdit && appliedRule === "reject-edit-before") {
      remaining -= 1;
      record("rejected-edit");
      response.writeHead(503, { "content-type": "application/json" });
      response.end(
        JSON.stringify({ detail: "Edit acknowledgement unavailable." })
      );
      return;
    }
    if (isSend && appliedRule === "reject-send-before") {
      rejectSend();
      return;
    }
    if (isSend && appliedRule === "drop-send-before") {
      response.destroy();
      return;
    }
    const forwarded = http.request(
      `${server.baseUrl}${request.url}`,
      {
        agent: false,
        method: request.method,
        headers: request.headers,
      },
      (upstream) => {
        record("upstream");
        if (isSend && appliedRule === "reject-send-after") {
          upstream.resume();
          upstream.once("end", rejectSend);
          return;
        }
        if (isSend && appliedRule === "drop-send-after") {
          upstream.resume();
          upstream.once("end", () => response.destroy());
          return;
        }
        const chunks: Buffer[] = [];
        upstream.on("data", (chunk) => chunks.push(chunk));
        upstream.on("end", () => {
          record("buffered");
          const body = Buffer.concat(chunks);
          const deliver = () => {
            if (response.destroyed) return;
            response.writeHead(upstream.statusCode ?? 500, upstream.headers);
            response.end(body);
          };
          if (isEdit && appliedRule === "delay-edit") {
            const timer = setTimeout(() => {
              timers.delete(timer);
              deliver();
            }, options.editDelayMs ?? 5000);
            timers.add(timer);
          } else {
            deliver();
          }
        });
        upstream.on("error", () => response.destroy());
      }
    );
    forwarded.on("error", () => {
      record("error");
      response.destroy();
    });
    request.pipe(forwarded);
  });
  proxy.on("connection", (socket) => {
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
  });
  await new Promise<void>((resolve) => proxy.listen(0, "0.0.0.0", resolve));
  const port = (proxy.address() as AddressInfo).port;
  return {
    port,
    receipts,
    baseUrl: `http://127.0.0.1:${port}`,
    setRule: (next: AcknowledgementRule, count = Infinity) => {
      rule = next;
      remaining = count;
    },
    setSendRules: (next: AcknowledgementRule[]) => {
      sendRules = next;
    },
    stop: async () => {
      timers.forEach((timer) => clearTimeout(timer));
      sockets.forEach((socket) => socket.destroy());
      await new Promise<void>((resolve, reject) =>
        proxy.close((error) => (error ? reject(error) : resolve()))
      );
    },
  };
}
