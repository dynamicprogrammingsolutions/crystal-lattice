import React from "react";
import { AppState, Pressable, Text } from "react-native";
import { act, fireEvent, render, waitFor } from "@testing-library/react-native";
import type { AgentBackend } from "@crystal-lattice/frontend-sdk";
import { subscribeDisplayPresentation } from "@crystal-lattice/frontend-sdk";

import {
  HumanTimeTelemetryProvider,
  useHumanTimeTelemetry,
} from "../src/humanTimeTelemetry/HumanTimeTelemetryProvider";
import { appendSpan, loadSpans } from "../src/humanTimeTelemetry/spanCache";
import { HomeWorkspaceProvider } from "../src/HomeWorkspaceContext";
import { MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY } from "../src/homeWorkspaceState";
import GlobalSettingsModal from "../src/components/GlobalSettingsModal";

const originalAppState = AppState.currentState;

function createMemoryStore(seed?: Record<string, unknown>) {
  const data = new Map<string, string>(
    Object.entries(seed ?? {}).map(([key, value]) => [
      key,
      JSON.stringify(value),
    ])
  );
  return {
    get: async (key: string) => data.get(key) ?? null,
    set: async (key: string, value: string) => {
      data.set(key, value);
    },
    delete: async (key: string) => {
      data.delete(key);
    },
  };
}

function createBackend(executeAction: jest.Mock): AgentBackend {
  return { executeAction } as unknown as AgentBackend;
}

function Host({
  backend,
  connectionId,
  activeSessionId,
  store,
  showSettings = false,
  children,
}: {
  backend: AgentBackend | null;
  connectionId: string;
  activeSessionId: string | null;
  store: ReturnType<typeof createMemoryStore>;
  showSettings?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <HomeWorkspaceProvider store={store}>
      <HumanTimeTelemetryProvider
        backend={backend}
        connectionId={connectionId}
        activeSessionId={activeSessionId}
      >
        {showSettings ? (
          <GlobalSettingsModal visible onRequestClose={() => {}} />
        ) : null}
        {children}
      </HumanTimeTelemetryProvider>
    </HomeWorkspaceProvider>
  );
}

function BoundaryProbe({ sessionId }: { sessionId: string }) {
  const { splitForComposedMessage } = useHumanTimeTelemetry();
  return (
    <Pressable
      testID="split-composed-message"
      onPress={() => splitForComposedMessage(sessionId)}
    >
      <Text>split</Text>
    </Pressable>
  );
}

async function drainMicrotasks() {
  for (let index = 0; index < 10; index += 1) {
    await Promise.resolve();
  }
}

async function settleAfterRender() {
  await act(async () => {
    await drainMicrotasks();
  });
}

function enabledStore(pluginId = "duration_tracking_app") {
  return createMemoryStore({
    [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
      timeTrackingEnabled: true,
      timeTrackingPluginId: pluginId,
    },
  });
}

function successfulActionResult(recorded = 1) {
  return {
    status: "ok",
    plugin: "duration_tracking_app",
    action_id: "record_human_time_spans",
    result: {
      recorded,
      merged: 0,
      skipped: 0,
      absorbed: 0,
      duplicate: false,
    },
  };
}

describe("HumanTimeTelemetryProvider", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-09-25T10:00:00.000Z"));
    (AppState as any).currentState = "active";
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
    (AppState as any).currentState = originalAppState;
  });

  it("collects nothing while the opt-in toggle is off", async () => {
    const executeAction = jest.fn().mockResolvedValue(successfulActionResult());
    const store = createMemoryStore();
    const backend = createBackend(executeAction);
    const screen = render(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId="session-1"
        store={store}
      />
    );
    await settleAfterRender();
    await jest.advanceTimersByTimeAsync(10_000);
    screen.rerender(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId={null}
        store={store}
      />
    );
    await drainMicrotasks();

    expect(await loadSpans("connection-a")).toEqual([]);
    expect(executeAction).not.toHaveBeenCalled();
  });

  it("tracks the complete foreground period while a session is open", async () => {
    const executeAction = jest.fn().mockResolvedValue(successfulActionResult());
    const backend = createBackend(executeAction);
    const store = enabledStore();
    const screen = render(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId="session-1"
        store={store}
      />
    );
    await settleAfterRender();

    await jest.advanceTimersByTimeAsync(15_000);
    screen.rerender(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId={null}
        store={store}
      />
    );
    await act(async () => {
      await drainMicrotasks();
      await jest.advanceTimersByTimeAsync(2_000);
    });

    expect(executeAction).toHaveBeenCalledTimes(1);
    const span = executeAction.mock.calls[0][0].inputs.spans[0];
    expect(span.session_id).toBe("session-1");
    expect(Date.parse(span.to) - Date.parse(span.from)).toBe(15_000);
    await expect(loadSpans("connection-a")).resolves.toEqual([]);
  });

  it("closes on background, restarts on foreground, and flushes the prior span", async () => {
    const executeAction = jest.fn().mockResolvedValue(successfulActionResult());
    const backend = createBackend(executeAction);
    const store = enabledStore();
    let appStateListener: ((state: string) => void) | null = null;
    jest
      .spyOn(AppState, "addEventListener")
      .mockImplementation((_event, listener) => {
        appStateListener = listener as (state: string) => void;
        return { remove: jest.fn() };
      });

    render(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId="session-1"
        store={store}
      />
    );
    await settleAfterRender();
    await jest.advanceTimersByTimeAsync(10_000);

    await act(async () => {
      appStateListener?.("background");
      await drainMicrotasks();
    });
    await expect(loadSpans("connection-a")).resolves.toHaveLength(1);

    await act(async () => {
      appStateListener?.("active");
      await drainMicrotasks();
    });
    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));
    const firstSpan = executeAction.mock.calls[0][0].inputs.spans[0];
    expect(Date.parse(firstSpan.to) - Date.parse(firstSpan.from)).toBe(10_000);

    await jest.advanceTimersByTimeAsync(5_000);
    await act(async () => {
      appStateListener?.("background");
      await drainMicrotasks();
      await jest.advanceTimersByTimeAsync(2_000);
    });
    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(2));
    const secondSpan = executeAction.mock.calls[1][0].inputs.spans[0];
    expect(Date.parse(secondSpan.to) - Date.parse(secondSpan.from)).toBe(5_000);
  });

  it("closes and immediately starts a new span when the session changes", async () => {
    const executeAction = jest
      .fn()
      .mockResolvedValue(successfulActionResult(2));
    const backend = createBackend(executeAction);
    const store = enabledStore();
    const screen = render(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId="session-1"
        store={store}
        showSettings
      />
    );
    await settleAfterRender();
    await jest.advanceTimersByTimeAsync(4_000);

    screen.rerender(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId="session-2"
        store={store}
        showSettings
      />
    );
    await jest.advanceTimersByTimeAsync(1_000);
    fireEvent.press(
      screen.getByTestId("global-settings-time-tracking-diagnostics")
    );
    fireEvent.press(screen.getByTestId("time-tracking-upload-now"));

    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));
    const spans = executeAction.mock.calls[0][0].inputs.spans;
    expect(spans.map((span: any) => span.session_id)).toEqual([
      "session-1",
      "session-2",
    ]);
    expect(Date.parse(spans[0].to) - Date.parse(spans[0].from)).toBe(4_000);
    expect(Date.parse(spans[1].to) - Date.parse(spans[1].from)).toBe(1_000);
  });

  it("splits at composed-message submission and continues foreground tracking", async () => {
    const store = enabledStore();
    const screen = render(
      <Host
        backend={null}
        connectionId="connection-split"
        activeSessionId="session-1"
        store={store}
      >
        <BoundaryProbe sessionId="session-1" />
      </Host>
    );
    await settleAfterRender();
    await jest.advanceTimersByTimeAsync(10_000);

    fireEvent.press(screen.getByTestId("split-composed-message"));
    await act(async () => {
      await drainMicrotasks();
    });

    const firstPending = await loadSpans("connection-split");
    expect(firstPending).toHaveLength(1);
    expect(
      Date.parse(firstPending[0].to) - Date.parse(firstPending[0].from)
    ).toBe(10_000);

    await jest.advanceTimersByTimeAsync(5_000);
    screen.rerender(
      <Host
        backend={null}
        connectionId="connection-split"
        activeSessionId={null}
        store={store}
      >
        <BoundaryProbe sessionId="session-1" />
      </Host>
    );
    await act(async () => {
      await drainMicrotasks();
    });

    const allPending = await loadSpans("connection-split");
    expect(allPending).toHaveLength(2);
    expect(Date.parse(allPending[1].to) - Date.parse(allPending[1].from)).toBe(
      5_000
    );
  });

  it("persists the open span when tracking is disabled", async () => {
    const executeAction = jest.fn().mockResolvedValue(successfulActionResult());
    const store = enabledStore();
    const screen = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
        activeSessionId="session-1"
        store={store}
        showSettings
      />
    );
    await settleAfterRender();
    await jest.advanceTimersByTimeAsync(8_000);

    fireEvent(
      screen.getByTestId("global-settings-time-tracking-toggle"),
      "valueChange",
      false
    );
    await act(async () => {
      await drainMicrotasks();
    });

    const pending = await loadSpans("connection-a");
    expect(pending).toHaveLength(1);
    expect(Date.parse(pending[0].to) - Date.parse(pending[0].from)).toBe(8_000);
    expect(executeAction).not.toHaveBeenCalled();
  });

  it("flushes durable pending spans as soon as a connection is usable", async () => {
    const executeAction = jest.fn().mockResolvedValue(successfulActionResult());
    const backend = createBackend(executeAction);
    const store = enabledStore();
    await appendSpan("connection-a", {
      sessionId: "session-1",
      from: "2026-09-25T09:58:00.000Z",
      to: "2026-09-25T09:59:00.000Z",
    });

    render(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId={null}
        store={store}
      />
    );
    await settleAfterRender();

    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));
    await expect(loadSpans("connection-a")).resolves.toEqual([]);
  });

  it("shows diagnostics and upload now restarts the foreground session span", async () => {
    const executeAction = jest.fn().mockResolvedValue(successfulActionResult());
    const backend = createBackend(executeAction);
    const store = enabledStore();
    const screen = render(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId="session-1"
        store={store}
        showSettings
      />
    );
    await settleAfterRender();
    await jest.advanceTimersByTimeAsync(5_000);

    fireEvent.press(
      screen.getByTestId("global-settings-time-tracking-diagnostics")
    );
    expect(screen.getByText("Open span: Session session-")).toBeTruthy();
    fireEvent.press(screen.getByTestId("time-tracking-upload-now"));

    await waitFor(() => {
      expect(
        screen.getByTestId("time-tracking-pending-count").props.children
      ).toEqual(["Pending uploads: ", 0]);
      expect(
        screen.getByTestId("time-tracking-last-upload").props.children
      ).toEqual(["Last upload: ", "Successful"]);
    });
    expect(executeAction).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("time-tracking-entry-0")).toBeTruthy();
    expect(screen.getByText("Uploaded")).toBeTruthy();
    expect(screen.getByText("session-1")).toBeTruthy();
    expect(screen.getByText("5s")).toBeTruthy();
    expect(screen.getByText("Open span: Session session-")).toBeTruthy();
  });

  it("emits the one-time warning banner on a definitive plugin failure", async () => {
    const store = enabledStore("missing_plugin");
    const executeAction = jest
      .fn()
      .mockRejectedValue(
        new Error(
          "HTTP 404 POST /actions: Unknown application plugin 'missing_plugin'"
        )
      );
    const backend = createBackend(executeAction);
    const received: unknown[] = [];
    const unsubscribe = subscribeDisplayPresentation(backend, (envelope) => {
      received.push(envelope);
    });
    await appendSpan("connection-a", {
      sessionId: "session-1",
      from: "2026-09-25T09:58:00.000Z",
      to: "2026-09-25T09:59:00.000Z",
    });

    render(
      <Host
        backend={backend}
        connectionId="connection-a"
        activeSessionId={null}
        store={store}
      />
    );
    await settleAfterRender();

    await waitFor(() => expect(received).toHaveLength(1));
    const envelope = received[0] as any;
    expect(envelope.display.variant).toBe("warning");
    expect(envelope.display.presentation).toBe("banner");
    await expect(loadSpans("connection-a")).resolves.toHaveLength(1);
    unsubscribe();
  });

  it("does not show the unavailable-plugin banner for a rejected span", async () => {
    const store = enabledStore();
    const executeAction = jest.fn().mockResolvedValue({
      ...successfulActionResult(),
      result: {
        recorded: 0,
        merged: 0,
        skipped: 1,
        absorbed: 0,
        duplicate: false,
      },
    });
    const backend = createBackend(executeAction);
    const received: unknown[] = [];
    const unsubscribe = subscribeDisplayPresentation(backend, (envelope) => {
      received.push(envelope);
    });
    await appendSpan("connection-rejected-span", {
      sessionId: "missing-session",
      from: "2026-09-25T09:58:00.000Z",
      to: "2026-09-25T09:59:00.000Z",
    });

    render(
      <Host
        backend={backend}
        connectionId="connection-rejected-span"
        activeSessionId={null}
        store={store}
      />
    );
    await settleAfterRender();
    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));

    expect(received).toEqual([]);
    await expect(loadSpans("connection-rejected-span")).resolves.toHaveLength(
      0
    );
    unsubscribe();
  });
});
