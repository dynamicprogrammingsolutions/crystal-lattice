import { afterEach, describe, expect, it, vi } from "vitest";
import type { AgentBackend } from "../../backend/backend";
import { ChatController } from "../chatController";

const controllers: ChatController[] = [];
afterEach(() =>
  controllers.splice(0).forEach((controller) => controller.dispose())
);

function createController(backend: Partial<AgentBackend>) {
  const controller = new ChatController({
    backend: backend as AgentBackend,
    sessionId: "session",
    initialMessages: [
      { index: 0, message: { role: "user", content: "hello" } },
    ],
    initialEventsCursorId: "store:1",
    initialActiveRequestId: "old-request",
  });
  controllers.push(controller);
  return controller;
}

function status(requestId: string | null) {
  return {
    version: 1 as const,
    authority: "derived_transient",
    statuses: [
      {
        session_id: "session",
        request_id: requestId,
        state: requestId ? ("running" as const) : ("succeeded" as const),
        basis: requestId
          ? ("active_request" as const)
          : ("session_tail" as const),
        session_modified: 1,
      },
    ],
    missing_session_ids: [],
  };
}

describe("request recovery", () => {
  it("does not restart polling when a message reload completes after disposal", async () => {
    let finish!: (value: any) => void;
    const pending = new Promise<any>((resolve) => {
      finish = resolve;
    });
    const controller = createController({
      listMessages: async () => pending,
      listEvents: async () => ({
        events: [],
        latestEventId: "store:1",
        cursorExpired: false,
      }),
    });
    controller.startEventStreaming({ initialSinceId: "store:1" });
    const loading = controller.loadMessages({});
    controller.dispose();
    finish({ messages: [], cursorEventId: "store:2", activeRequestId: null });
    await loading;
    expect(controller.isEventStreaming()).toBe(false);
  });

  it("clears a stale checkpoint request using current status on return", async () => {
    const controller = createController({
      listMessages: async () => ({
        messages: [],
        cursorEventId: "store:2",
        activeRequestId: "old-request",
      }),
      getSessionRequestStatuses: async () => status(null),
    });
    await controller.recoverAfterResume();
    expect(controller.getSnapshot().activeRequestId).toBeNull();
  });

  it("accepts explicit null cache authority", () => {
    const controller = createController({});
    controller.hydrateFromCache({
      messages: [],
      eventsCursorId: "store:2",
      activeRequestId: null,
    });
    expect(controller.getSnapshot().activeRequestId).toBeNull();
  });

  it.each(["send", "sendMessage"] as const)(
    "does not resurrect a request when %s acknowledgement follows completion",
    async (method) => {
      let acknowledge!: (value: { request_id: string }) => void;
      const response = new Promise<{ request_id: string }>((resolve) => {
        acknowledge = resolve;
      });
      const listEvents = vi.fn(async () => ({
        events: [
          {
            type: "request_started",
            event_id: "store:2",
            session_id: "session",
            request_id: "request",
          },
          {
            type: "request_completed",
            event_id: "store:3",
            session_id: "session",
            request_id: "request",
          },
        ],
        latestEventId: "store:3",
        cursorExpired: false,
      }));
      const controller = createController({
        send: async () => response,
        sendMessage: async () => response,
        listEvents,
        listMessages: async () => ({
          messages: [],
          cursorEventId: "store:3",
          activeRequestId: "request",
        }),
      } as Partial<AgentBackend>);
      const sending =
        method === "send"
          ? controller.send()
          : controller.sendMessage({
              message: { role: "user", content: "hello" },
            });
      controller.startEventStreaming({ initialSinceId: "store:1" });
      await vi.waitFor(() => expect(listEvents).toHaveBeenCalled());
      expect(controller.getSnapshot().activeRequestId).toBeNull();
      controller.stopEventStreaming();
      await controller.loadMessages({});
      expect(controller.getSnapshot().activeRequestId).toBeNull();
      acknowledge({ request_id: "request" });
      await sending;
      expect(controller.getSnapshot().activeRequestId).toBeNull();
    }
  );

  it("does not let an older resume query clear a newer request", async () => {
    let finishStatus!: (value: ReturnType<typeof status>) => void;
    const pendingStatus = new Promise<ReturnType<typeof status>>((resolve) => {
      finishStatus = resolve;
    });
    const query = vi
      .fn()
      .mockImplementationOnce(async () => pendingStatus)
      .mockImplementation(async () => status("new-request"));
    const controller = createController({
      listMessages: async () => ({
        messages: [],
        cursorEventId: "store:2",
        activeRequestId: null,
      }),
      getSessionRequestStatuses: query,
      send: async () => ({ request_id: "new-request" }),
    });
    const recovery = controller.recoverAfterResume();
    await vi.waitFor(() => expect(query).toHaveBeenCalledTimes(1));
    const sending = controller.send();
    await vi.waitFor(() =>
      expect(controller.getSnapshot().activeRequestId).toBe("new-request")
    );
    finishStatus(status(null));
    await Promise.all([recovery, sending]);
    expect(controller.getSnapshot().activeRequestId).toBe("new-request");
  });
});
