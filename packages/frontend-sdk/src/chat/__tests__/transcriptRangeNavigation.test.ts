import { describe, expect, it } from "vitest";

import type { IndexedMessage } from "../../types/messages";
import { selectTranscriptRangeRestoreAnchor } from "../transcriptRangeNavigation";

function message(index: number, content = `message-${index}`): IndexedMessage {
  return {
    index,
    message: {
      role: index % 2 === 0 ? "user" : "assistant",
      content,
      metadata: { nested: { index } },
    },
  };
}

describe("selectTranscriptRangeRestoreAnchor", () => {
  it("selects the first visual-order candidate retained by a compatible response", () => {
    const messages = [message(25), message(26), message(27)];

    expect(
      selectTranscriptRangeRestoreAnchor({
        candidates: [
          {
            messageIndex: 24,
            offsetFromViewportTop: -10,
            message: message(24).message,
          },
          {
            messageIndex: 26,
            offsetFromViewportTop: 42,
            message: message(26).message,
          },
          {
            messageIndex: 27,
            offsetFromViewportTop: 110,
            message: message(27).message,
          },
        ],
        completedMessages: messages,
        previousContext: { cursorEventId: "cursor:1" },
        completedContext: { cursorEventId: "cursor:1" },
      }),
    ).toEqual({
      messageIndex: 26,
      offsetFromViewportTop: 42,
    });
  });

  it("uses the message witness when the live cursor changed", () => {
    expect(
      selectTranscriptRangeRestoreAnchor({
        candidates: [
          {
            messageIndex: 26,
            offsetFromViewportTop: 42,
            message: {
              ...message(26).message,
              metadata: { nested: { index: 26 } },
            },
          },
        ],
        completedMessages: [message(26), message(27)],
        previousContext: { cursorEventId: "cursor:1" },
        completedContext: { cursorEventId: "cursor:2" },
      }),
    ).toEqual({
      messageIndex: 26,
      offsetFromViewportTop: 42,
    });
  });

  it("does not restore a reused index when its message witness changed", () => {
    expect(
      selectTranscriptRangeRestoreAnchor({
        candidates: [
          {
            messageIndex: 26,
            offsetFromViewportTop: 42,
            message: message(26).message,
          },
        ],
        completedMessages: [message(26, "shifted-message")],
        previousContext: { cursorEventId: "cursor:1" },
        completedContext: { cursorEventId: "cursor:2" },
      }),
    ).toBeNull();
  });

  it("requires the witness even when response cursors match or are absent", () => {
    expect(
      selectTranscriptRangeRestoreAnchor({
        candidates: [
          {
            messageIndex: 26,
            offsetFromViewportTop: 42,
            message: message(26).message,
          },
        ],
        completedMessages: [message(26, "different-message")],
        previousContext: { cursorEventId: null },
        completedContext: { cursorEventId: null },
      }),
    ).toBeNull();
  });

  it("rejects a different read-only snapshot even when the index exists", () => {
    expect(
      selectTranscriptRangeRestoreAnchor({
        candidates: [
          {
            messageIndex: 26,
            offsetFromViewportTop: 42,
            message: message(26).message,
          },
        ],
        completedMessages: [message(26)],
        previousContext: {
          cursorEventId: "cursor:1",
          snapshotId: "snapshot:1",
        },
        completedContext: {
          cursorEventId: "cursor:1",
          snapshotId: "snapshot:2",
        },
      }),
    ).toBeNull();
  });

  it("returns null when no candidate overlaps the completed range", () => {
    expect(
      selectTranscriptRangeRestoreAnchor({
        candidates: [
          {
            messageIndex: 10,
            offsetFromViewportTop: 0,
            message: message(10).message,
          },
        ],
        completedMessages: [message(20), message(21)],
        previousContext: { cursorEventId: "cursor:1" },
        completedContext: { cursorEventId: "cursor:1" },
      }),
    ).toBeNull();
  });
});
