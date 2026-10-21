import { afterEach, describe, expect, it } from "vitest";
import { ChatController } from "../../chat/chatController";
import { FetchTransport } from "../../transport/fetchTransport";
import { RestAgentBackend } from "../../backend/restBackend";
import { waitForAsync, type StartedServer } from "../harness";
import { startChatOperationsServer } from "../../../../../test/fixture/chat-operations/backend";

let server: StartedServer | null = null;
const controllers: ChatController[] = [];
afterEach(async () => {
  controllers.splice(0).forEach((controller) => controller.dispose());
  await server?.stop();
  server = null;
});

describe("request recovery through public HTTP", () => {
  it("reconciles a completed cached request without manual refresh or retained events", async () => {
    server = await startChatOperationsServer({
      eventStoreOptions: { maxEventsGlobal: 8 },
      startupTimeoutMs: 30_000,
    });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const created = await backend.createSession({ agentId: "default" });
    const sessionId = created.session.session_id;
    const started = await backend.sendMessage(sessionId, {
      message: { role: "user", content: "recovery" },
      configOverrides: { stream_chunk_count: 2, stream_chunk_delay_ms: 50 },
    });
    const cached = await backend.listMessages(sessionId, {});
    await waitForAsync(async () => {
      const status = await backend.getSessionRequestStatuses([sessionId]);
      return status.statuses[0].state !== "running";
    });
    const reopened = new ChatController({
      backend,
      sessionId,
      initialMessages: cached.messages,
      initialEventsCursorId: cached.cursorEventId,
      initialActiveRequestId: started.request_id,
    });
    controllers.push(reopened);
    await reopened.recoverAfterResume();
    expect(reopened.getSnapshot().activeRequestId).toBeNull();
    expect(
      reopened
        .getSnapshot()
        .messages.some((entry) => entry.message.role === "assistant")
    ).toBe(true);
  }, 60_000);

  it("does not resurrect a completed request from a delayed HTTP acknowledgement", async () => {
    server = await startChatOperationsServer({ startupTimeoutMs: 30_000 });
    const transport = new FetchTransport({ baseUrl: server.baseUrl });
    const backend = new RestAgentBackend({
      transport: {
        request: async (request: any) => {
          const response = await transport.request(request);
          if (
            request.method === "POST" &&
            request.path.endsWith("/send_message")
          ) {
            await new Promise((resolve) => setTimeout(resolve, 1500));
          }
          return response;
        },
      },
    });
    const created = await backend.createSession({ agentId: "default" });
    const controller = new ChatController({
      backend,
      sessionId: created.session.session_id,
    });
    controllers.push(controller);
    await controller.loadMessages({});
    controller.startEventStreaming({
      initialSinceId: controller.getSnapshot().eventsCursorId ?? "0",
    });
    await controller.sendMessage({
      message: { role: "user", content: "fast response" },
      configOverrides: { stream_chunk_count: 1, stream_chunk_delay_ms: 0 },
    });
    expect(controller.getSnapshot().activeRequestId).toBeNull();
  }, 60_000);
});
