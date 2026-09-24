import React from 'react';
import { Text, TouchableOpacity } from 'react-native';
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import { subscribeDisplayPresentation } from '@crystal-lattice/frontend-sdk';

import {
  HumanTimeTelemetryProvider,
  useHumanTimeTelemetry,
} from '../src/humanTimeTelemetry/HumanTimeTelemetryProvider';
import { appendSpan, loadSpans } from '../src/humanTimeTelemetry/spanCache';
import { HomeWorkspaceProvider } from '../src/HomeWorkspaceContext';
import { MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY } from '../src/homeWorkspaceState';

function createMemoryStore(seed?: Record<string, unknown>) {
  const data = new Map<string, string>(
    Object.entries(seed ?? {}).map(([key, value]) => [
      key,
      JSON.stringify(value),
    ]),
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

function ActivityProbe({ sessionId }: { sessionId: string | null }) {
  const { recordActivity } = useHumanTimeTelemetry();
  return (
    <TouchableOpacity
      testID="telemetry-activity-button"
      onPress={() => recordActivity(sessionId)}
    >
      <Text>activity</Text>
    </TouchableOpacity>
  );
}

function Host({
  backend,
  connectionId,
  isBusy,
  store,
  sessionId = 'session-1',
}: {
  backend: AgentBackend;
  connectionId: string;
  isBusy: boolean;
  store: ReturnType<typeof createMemoryStore>;
  sessionId?: string | null;
}) {
  return (
    <HomeWorkspaceProvider store={store}>
      <HumanTimeTelemetryProvider
        backend={backend}
        connectionId={connectionId}
        isBusy={isBusy}
      >
        <ActivityProbe sessionId={sessionId} />
      </HumanTimeTelemetryProvider>
    </HomeWorkspaceProvider>
  );
}

async function drainMicrotasks() {
  for (let index = 0; index < 10; index += 1) {
    await Promise.resolve();
  }
}

/** Let the workspace hydrate and the provider re-render with the settings. */
async function settleAfterRender() {
  await act(async () => {
    await drainMicrotasks();
  });
}

describe('HumanTimeTelemetryProvider', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('collects nothing while the opt-in toggle is off', async () => {
    const store = createMemoryStore();
    const executeAction = jest.fn().mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });
    const { getByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
        isBusy={false}
        store={store}
      />,
    );
    await settleAfterRender();

    fireEvent.press(getByTestId('telemetry-activity-button'));
    await jest.advanceTimersByTimeAsync(60_000);
    await drainMicrotasks();

    expect(await loadSpans('connection-a')).toEqual([]);
    expect(executeAction).not.toHaveBeenCalled();
  });

  it('tracks activity, closes the span on inactivity, and uploads the batch', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
        timeTrackingPluginId: 'duration_tracking_app',
      },
    });
    const executeAction = jest.fn().mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });
    const { getByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
        isBusy={false}
        store={store}
      />,
    );
    await settleAfterRender();

    fireEvent.press(getByTestId('telemetry-activity-button'));
    await jest.advanceTimersByTimeAsync(5_000);
    fireEvent.press(getByTestId('telemetry-activity-button'));
    // 30s of inactivity closes the span; the close debounce then flushes.
    await jest.advanceTimersByTimeAsync(30_000);
    await jest.advanceTimersByTimeAsync(2_000);
    await drainMicrotasks();

    expect(executeAction).toHaveBeenCalledTimes(1);
    const call = executeAction.mock.calls[0][0];
    expect(call.pluginId).toBe('duration_tracking_app');
    expect(call.actionId).toBe('record_human_time_spans');
    expect(call.actionOwner).toBe('application');
    expect(call.inputs.spans).toHaveLength(1);
    expect(call.inputs.spans[0].session_id).toBe('session-1');
    expect(typeof call.inputs.request_id).toBe('string');
    await expect(loadSpans('connection-a')).resolves.toEqual([]);
  });

  it('attributes session-less activity to a null session id', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
      },
    });
    const executeAction = jest.fn().mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });
    const { getByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
        isBusy={false}
        store={store}
        sessionId={null}
      />,
    );
    await settleAfterRender();

    fireEvent.press(getByTestId('telemetry-activity-button'));
    await jest.advanceTimersByTimeAsync(30_000);
    await jest.advanceTimersByTimeAsync(2_000);
    await drainMicrotasks();

    const call = executeAction.mock.calls[0][0];
    expect(call.inputs.spans[0].session_id).toBeNull();
  });

  it('defers the connection-open flush while busy and retries once idle', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
      },
    });
    const executeAction = jest.fn().mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });
    const backend = createBackend(executeAction);
    await appendSpan('connection-a', {
      sessionId: 'session-1',
      from: new Date(Date.now() - 120_000).toISOString(),
      to: new Date(Date.now() - 60_000).toISOString(),
    });

    const { rerender, getByTestId } = render(
      <Host
        backend={backend}
        connectionId="connection-a"
        isBusy
        store={store}
      />,
    );
    await settleAfterRender();
    expect(getByTestId('telemetry-activity-button')).toBeTruthy();
    // The connection-open flush deferred while busy.
    await jest.advanceTimersByTimeAsync(30_000);
    expect(executeAction).not.toHaveBeenCalled();

    // Work settles: the busy retry uploads the pending span.
    rerender(
      <Host
        backend={backend}
        connectionId="connection-a"
        isBusy={false}
        store={store}
      />,
    );
    await jest.advanceTimersByTimeAsync(15_000);
    await drainMicrotasks();

    await waitFor(() => {
      expect(executeAction).toHaveBeenCalledTimes(1);
    });
    await expect(loadSpans('connection-a')).resolves.toEqual([]);
  });

  it('emits the one-time warning banner on a definitive plugin failure', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
        timeTrackingPluginId: 'missing_plugin',
      },
    });
    const executeAction = jest
      .fn()
      .mockRejectedValue(
        new Error("HTTP 404 POST /actions: Unknown application plugin 'missing_plugin'"),
      );
    const backend = createBackend(executeAction);
    const received: unknown[] = [];
    const unsubscribe = subscribeDisplayPresentation(backend, (envelope) => {
      received.push(envelope);
    });
    await appendSpan('connection-a', {
      sessionId: 'session-1',
      from: new Date(Date.now() - 120_000).toISOString(),
      to: new Date(Date.now() - 60_000).toISOString(),
    });

    render(
      <Host
        backend={backend}
        connectionId="connection-a"
        isBusy={false}
        store={store}
      />,
    );
    await settleAfterRender();

    await waitFor(() => {
      expect(received).toHaveLength(1);
    });
    const envelope = received[0] as any;
    expect(envelope.display.variant).toBe('warning');
    expect(envelope.display.presentation).toBe('banner');
    // The spans are retained for a later retry.
    await expect(loadSpans('connection-a')).resolves.toHaveLength(1);
    unsubscribe();
  });
});