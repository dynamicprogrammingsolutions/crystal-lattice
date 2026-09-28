import type {
  ConnectionRecord,
  SessionSummary,
} from "@crystal-lattice/frontend-sdk";
import type { HomeSessionItem } from "@crystal-lattice/frontend-rn-components";

import {
  formatMobileHomeRelativeTime,
  resolveMobileHomeSessionPresentation,
} from "../homeSessionPresentation";

const connection = {
  id: "connection",
  name: "A deliberately long connection name",
  kind: "manual",
  host: "127.0.0.1",
  port: 9000,
} as ConnectionRecord;

function item(summary: Partial<SessionSummary>): HomeSessionItem {
  const resolved = {
    session_id: "abcdefgh-long-session-id",
    modified: 1_000,
    preview: "",
    ...summary,
  } as SessionSummary;
  return {
    key: "connection::abcdefgh-long-session-id",
    connectionId: connection.id,
    sessionId: resolved.session_id,
    connection,
    summary: resolved,
    note: null,
  };
}

describe("mobile Home session presentation", () => {
  it.each([
    {
      name: "keeps supplied title and subtitle",
      summary: {
        preview: "Message preview",
        presentation: {
          title: "Server title",
          subtitle: "Server subtitle",
          meta: null,
        },
      },
      title: "Server title",
      subtitle: "Server subtitle",
    },
    {
      name: "uses a distinct preview when title has no subtitle",
      summary: {
        preview: "Message preview",
        presentation: {
          title: "Server title",
          subtitle: null,
          meta: null,
        },
      },
      title: "Server title",
      subtitle: "Message preview",
    },
    {
      name: "does not repeat preview when it equals the title",
      summary: {
        preview: "Same text",
        presentation: {
          title: "Same text",
          subtitle: null,
          meta: null,
        },
      },
      title: "Same text",
      subtitle: null,
    },
    {
      name: "preserves subtitle when preview supplies a missing title",
      summary: {
        preview: "Message preview",
        presentation: {
          title: " ",
          subtitle: "Server subtitle",
          meta: null,
        },
      },
      title: "Message preview",
      subtitle: "Server subtitle",
    },
    {
      name: "renders preview-only content once",
      summary: {
        preview: "Message preview",
        presentation: undefined,
      },
      title: "Message preview",
      subtitle: null,
    },
    {
      name: "normalizes whitespace-only presentation fields",
      summary: {
        preview: "  Message preview  ",
        presentation: {
          title: " ",
          subtitle: " ",
          meta: null,
        },
      },
      title: "Message preview",
      subtitle: null,
    },
    {
      name: "uses the SDK session fallback when all display text is empty",
      summary: {
        preview: " ",
        presentation: undefined,
      },
      title: "Session abcdefgh",
      subtitle: null,
    },
    {
      name: "keeps a title without inventing secondary text",
      summary: {
        preview: "",
        presentation: {
          title: "Server title",
          subtitle: null,
          meta: null,
        },
      },
      title: "Server title",
      subtitle: null,
    },
  ])("$name", ({ summary, title, subtitle }) => {
    expect(
      resolveMobileHomeSessionPresentation(item(summary), 1_000_000)
    ).toMatchObject({
      title,
      subtitle,
      sessionId: "abcdefgh-long-session-id",
      connectionName: connection.name,
    });
  });

  it.each([
    [1_000, "Just now"],
    [940, "1m ago"],
    [-2_600, "1h ago"],
    [-85_400, "1d ago"],
  ])("formats modified=%s against a controlled clock", (modified, expected) => {
    expect(formatMobileHomeRelativeTime(modified, 1_000_000)).toBe(expected);
  });
});
