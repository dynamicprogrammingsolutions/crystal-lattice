import { AppState } from "react-native";
import { act, renderHook, waitFor } from "@testing-library/react-native";
import type {
  ConnectionSessionStatusReader,
  ConnectionSessionStatusResult,
} from "@crystal-lattice/frontend-sdk";

import { useSessionRequestStatuses } from "../useSessionRequestStatuses";

const connections = [
  {
    id: "one",
    kind: "manual" as const,
    name: "One",
    host: "one.test",
    port: 8000,
    lastUsedAt: 1,
  },
  {
    id: "two",
    kind: "manual" as const,
    name: "Two",
    host: "two.test",
    port: 8000,
    lastUsedAt: 2,
  },
];

describe("useSessionRequestStatuses", () => {
  it("retains an observed running session when the consumer set and reader change", async () => {
    const originalAppState = AppState.currentState;
    (AppState as any).currentState = "active";
    const running: ConnectionSessionStatusResult = {
      status: "ok",
      snapshot: {
        version: 1,
        authority: "derived_transient",
        statuses: [
          {
            session_id: "a",
            request_id: "request",
            state: "running",
            basis: "active_request",
            session_modified: 1,
          },
        ],
        missing_session_ids: [],
      },
    };
    const firstReader = {
      getSessionRequestStatuses: jest.fn(async () => running),
    } as ConnectionSessionStatusReader;
    const secondReader = {
      getSessionRequestStatuses: jest.fn(async () => ({
        status: "unavailable" as const,
      })),
    } as ConnectionSessionStatusReader;
    const { result, rerender, unmount } = renderHook(
      ({
        reader,
        sessionIds,
      }: {
        reader: ConnectionSessionStatusReader;
        sessionIds: string[];
      }) =>
        useSessionRequestStatuses({
          enabled: true,
          connections,
          sessionIdsByConnection: { one: sessionIds },
          reader,
        }),
      {
        initialProps: {
          reader: firstReader,
          sessionIds: ["a"],
        },
      }
    );

    await waitFor(() => expect(result.current.one.a.state).toBe("running"));
    expect(firstReader.getSessionRequestStatuses).toHaveBeenCalledTimes(1);
    rerender({ reader: secondReader, sessionIds: ["a", "b"] });
    await waitFor(() =>
      expect(secondReader.getSessionRequestStatuses).toHaveBeenCalled()
    );
    expect(result.current.one.a.state).toBe("running");

    unmount();
    (AppState as any).currentState = originalAppState;
  });

  it("keeps running status through a transient read and clears it on authoritative success", async () => {
    jest.useFakeTimers();
    const originalAppState = AppState.currentState;
    (AppState as any).currentState = "active";
    const results: ConnectionSessionStatusResult[] = [
      {
        status: "ok",
        snapshot: {
          version: 1,
          authority: "derived_transient",
          statuses: [
            {
              session_id: "a",
              request_id: "request",
              state: "running",
              basis: "active_request",
              session_modified: 1,
            },
          ],
          missing_session_ids: ["gone"],
        },
      },
      { status: "unavailable" },
      {
        status: "ok",
        snapshot: {
          version: 1,
          authority: "derived_transient",
          statuses: [],
          missing_session_ids: [],
        },
      },
    ];
    const getSessionRequestStatuses = jest.fn(async () => results.shift()!);
    const reader = {
      getSessionRequestStatuses,
    } as ConnectionSessionStatusReader;
    const onMissingSessionIds = jest.fn();
    const sessionIdsByConnection = {
      one: ["a", "a"],
    };
    const { result, unmount } = renderHook(() =>
      useSessionRequestStatuses({
        enabled: true,
        connections,
        sessionIdsByConnection,
        reader,
        intervalMs: 100,
        onMissingSessionIds,
      })
    );

    await waitFor(() =>
      expect(getSessionRequestStatuses).toHaveBeenCalledTimes(1)
    );
    expect(getSessionRequestStatuses.mock.calls).toEqual([
      [connections[0], ["a"], { signal: expect.any(AbortSignal) }],
    ]);
    await waitFor(() => expect(result.current.one.a.state).toBe("running"));
    expect(onMissingSessionIds).toHaveBeenCalledWith("one", ["gone"]);

    await act(async () => {
      jest.advanceTimersByTime(100);
      await Promise.resolve();
    });
    await waitFor(() =>
      expect(getSessionRequestStatuses).toHaveBeenCalledTimes(2)
    );
    expect(result.current.one.a.state).toBe("running");

    await act(async () => {
      jest.advanceTimersByTime(200);
      await Promise.resolve();
    });
    await waitFor(() =>
      expect(getSessionRequestStatuses).toHaveBeenCalledTimes(3)
    );
    expect(result.current.one.a).toBeUndefined();

    unmount();
    (AppState as any).currentState = originalAppState;
    jest.useRealTimers();
  });
});
