import { describe, expect, it } from "vitest";

import type {
  ConnectionRecord,
  SessionRequestStatus,
} from "@crystal-lattice/frontend-sdk";

import {
  DEFAULT_SESSION_STATUS_BATCH_SIZE,
  buildSessionStatusRequestGroups,
  mergeSuccessfulStatusBatch,
  pruneSessionStatusesToRequests,
  removeExpiredRunningStatuses,
} from "./useSessionRequestStatuses";

const connection = {
  id: "connection",
  kind: "manual",
  name: "Connection",
  host: "127.0.0.1",
  port: 9000,
} as ConnectionRecord;

function status(
  sessionId: string,
  state: SessionRequestStatus["state"]
): SessionRequestStatus {
  return {
    session_id: sessionId,
    request_id: state === "running" ? `request-${sessionId}` : null,
    state,
    basis: state === "running" ? "active_request" : "session_tail",
    session_modified: 1,
  };
}

describe("session request-status polling state", () => {
  it("deduplicates and splits more than one endpoint-sized ID set", () => {
    const sessionIds = Array.from(
      { length: DEFAULT_SESSION_STATUS_BATCH_SIZE * 2 + 1 },
      (_value, index) => `session-${index}`
    );
    const [group] = buildSessionStatusRequestGroups(
      [connection],
      { connection: [...sessionIds, sessionIds[0]] },
      DEFAULT_SESSION_STATUS_BATCH_SIZE
    );

    expect(group.sessionIds).toEqual(sessionIds);
    expect(group.batches.flat()).toEqual(sessionIds);
    expect(group.batches).toHaveLength(3);
    expect(
      group.batches.every(
        (batch) => batch.length <= DEFAULT_SESSION_STATUS_BATCH_SIZE
      )
    ).toBe(true);
  });

  it("merges a successful subset without replacing unrelated statuses", () => {
    expect(
      mergeSuccessfulStatusBatch(
        {
          watched: status("watched", "running"),
          visible: status("visible", "running"),
        },
        ["visible", "completed"],
        [
          status("visible", "succeeded"),
          status("completed", "succeeded"),
          status("not-requested", "running"),
        ]
      )
    ).toEqual({
      watched: status("watched", "running"),
      visible: status("visible", "succeeded"),
      completed: status("completed", "succeeded"),
    });
  });

  it("retains running state through a transient failure and expires it later", () => {
    const running = { active: status("active", "running") };
    expect(
      removeExpiredRunningStatuses(
        running,
        ["active"],
        { active: 1_000 },
        1_500,
        1_000
      )
    ).toBe(running);
    expect(
      removeExpiredRunningStatuses(
        running,
        ["active"],
        { active: 1_000 },
        2_000,
        1_000
      )
    ).toEqual({});
  });

  it("prunes only identities that no longer have a consumer", () => {
    const groups = buildSessionStatusRequestGroups(
      [connection],
      { connection: ["tab"] },
      DEFAULT_SESSION_STATUS_BATCH_SIZE
    );
    expect(
      pruneSessionStatusesToRequests(
        {
          connection: {
            tab: status("tab", "running"),
            oldRow: status("oldRow", "succeeded"),
          },
          removedConnection: {
            other: status("other", "running"),
          },
        },
        groups
      )
    ).toEqual({
      connection: {
        tab: status("tab", "running"),
      },
    });
  });
});
