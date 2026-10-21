import { expect, it } from "vitest";
import { FetchTransport } from "../../transport/fetchTransport";
import { RestAgentBackend } from "../../backend/restBackend";
import {
  startAcknowledgementProxy,
  startChatOperationsBackend,
} from "../../../../../test/fixture/chat-operations/backend";

it("delivers a delayed real modification acknowledgement", async () => {
  const started = await startChatOperationsBackend({ messageCount: 8 });
  const proxy = await startAcknowledgementProxy(started.server);
  try {
    const backend = new RestAgentBackend({
      transport: new FetchTransport({
        baseUrl: proxy.baseUrl,
        defaultRequestTimeoutMs: 15_000,
      }),
    });
    proxy.setRule("delay-edit");
    const requestedAt = Date.now();
    await backend.modifyMessage(started.sessions[0], 0, "modified");
    expect(Date.now() - requestedAt).toBeGreaterThanOrEqual(4000);
    expect(
      (await backend.listMessages(started.sessions[0], {})).messages[0].message
        .content
    ).toBe("modified");
  } finally {
    await proxy.stop();
    await started.server.stop();
  }
}, 30_000);
