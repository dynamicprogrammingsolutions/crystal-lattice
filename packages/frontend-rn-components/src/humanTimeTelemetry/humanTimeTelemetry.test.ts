import { describe, expect, it, vi } from "vitest";

import type {
  AgentBackend,
  KeyValueStore,
} from "@crystal-lattice/frontend-sdk";

import { appendSpan, loadSpans } from "./spanCache";
import { runComposedMessageSubmission } from "./composedMessageSubmission";
import { HumanTimeSpanUploader } from "./uploader";

function memoryStore(): KeyValueStore {
  const data = new Map<string, string>();
  return {
    get: async (key) => data.get(key) ?? null,
    set: async (key, value) => {
      data.set(key, value);
    },
    delete: async (key) => {
      data.delete(key);
    },
  };
}

describe("shared human-time telemetry", () => {
  it("records a composed-message boundary without delaying submission", () => {
    const calls: string[] = [];
    const submission = Promise.resolve("sent");

    const result = runComposedMessageSubmission(
      () => {
        calls.push("boundary");
      },
      () => {
        calls.push("submit");
        return submission;
      },
    );

    expect(calls).toEqual(["boundary", "submit"]);
    expect(result).toBe(submission);
  });

  it("continues submission when boundary collection throws", () => {
    const submit = vi.fn(() => "sent");

    expect(
      runComposedMessageSubmission(() => {
        throw new Error("telemetry failed");
      }, submit),
    ).toBe("sent");
    expect(submit).toHaveBeenCalledOnce();
  });

  it("isolates rejected spans and removes them from the active queue", async () => {
    const store = memoryStore();
    const rejected = {
      sessionId: "missing",
      from: "2026-09-24T10:00:00.000Z",
      to: "2026-09-24T10:01:00.000Z",
    };
    const valid = {
      sessionId: null,
      from: "2026-09-24T10:02:00.000Z",
      to: "2026-09-24T10:03:00.000Z",
    };
    await appendSpan("connection", rejected, store);
    await appendSpan("connection", valid, store);

    const executeAction = vi.fn(async ({ inputs }) => {
      const spans = inputs.spans as Array<{ session_id: string | null }>;
      const skipped = spans.some((span) => span.session_id === "missing");
      return {
        status: "ok" as const,
        plugin: "duration_tracking_app",
        action_id: "record_human_time_spans",
        result: {
          recorded: skipped ? 0 : spans.length,
          merged: 0,
          skipped: skipped ? 1 : 0,
          absorbed: 0,
          duplicate: false,
        },
      };
    });
    const uploader = new HumanTimeSpanUploader({
      getBackend: () => ({ executeAction }) as unknown as AgentBackend,
      getConnectionId: () => "connection",
      getPluginId: () => "duration_tracking_app",
      isEnabled: () => true,
      store,
    });

    await expect(uploader.flush()).resolves.toBe("partial-failure");
    await expect(loadSpans("connection", store)).resolves.toEqual([]);
    expect(executeAction).toHaveBeenCalledTimes(3);
    await expect(uploader.flush()).resolves.toBe("empty");
    expect(executeAction).toHaveBeenCalledTimes(3);
  });
});
