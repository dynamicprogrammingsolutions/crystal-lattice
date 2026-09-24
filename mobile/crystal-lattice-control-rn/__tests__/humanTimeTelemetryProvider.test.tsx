import React from 'react';
import { AppState, Text, TouchableOpacity } from 'react-native';
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
import GlobalSettingsModal from '../src/components/GlobalSettingsModal';

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

function ActivityProbeList({ sessionIds }: { sessionIds: string[] }) {
  const { recordActivity } = useHumanTimeTelemetry();
  return (
    <>
      {sessionIds.map((sessionId, index) => (
        <TouchableOpacity
          key={sessionId}
          testID={`telemetry-activity-button-${index}`}
          onPress={() => recordActivity(sessionId)}
        >
          <Text>{sessionId}</Text>
        </TouchableOpacity>
      ))}
    </>
  );
}

function Host({
  backend,
  connectionId,
  store,
  sessionId = 'session-1',
  sessionIds,
  showSettings = false,
}: {
  backend: AgentBackend;
  connectionId: string;
  store: ReturnType<typeof createMemoryStore>;
  sessionId?: string | null;
  sessionIds?: string[];
  showSettings?: boolean;
}) {
  return (
    <HomeWorkspaceProvider store={store}>
      <HumanTimeTelemetryProvider backend={backend} connectionId={connectionId}>
        {sessionIds ? (
          <ActivityProbeList sessionIds={sessionIds} />
        ) : (
          <ActivityProbe sessionId={sessionId} />
        )}
        {showSettings ? (
          <GlobalSettingsModal visible onRequestClose={() => {}} />
        ) : null}
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
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
      result: { status: 'ok' },
    });
    const { getByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
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
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
      result: { status: 'ok' },
    });
    const { getByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
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
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
      result: { status: 'ok' },
    });
    const { getByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
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

  it('flushes durable pending spans as soon as a connection is usable', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
      },
    });
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
      result: { status: 'ok' },
    });
    const backend = createBackend(executeAction);
    await appendSpan('connection-a', {
      sessionId: 'session-1',
      from: new Date(Date.now() - 120_000).toISOString(),
      to: new Date(Date.now() - 60_000).toISOString(),
    });

    const { getByTestId } = render(
      <Host backend={backend} connectionId="connection-a" store={store} />,
    );
    await settleAfterRender();
    expect(getByTestId('telemetry-activity-button')).toBeTruthy();

    await waitFor(() => {
      expect(executeAction).toHaveBeenCalledTimes(1);
    });
    await expect(loadSpans('connection-a')).resolves.toEqual([]);
  });

  it('closes on background and flushes the durable span on foreground', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
      },
    });
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
      result: {
        recorded: 1,
        merged: 0,
        skipped: 0,
        absorbed: 0,
        duplicate: false,
      },
    });
    let appStateListener: ((state: string) => void) | null = null;
    const subscription = { remove: jest.fn() };
    const appStateSpy = jest
      .spyOn(AppState, 'addEventListener')
      .mockImplementation((_event, listener) => {
        appStateListener = listener as (state: string) => void;
        return subscription;
      });
    const { getByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
        store={store}
      />,
    );
    await settleAfterRender();

    fireEvent.press(getByTestId('telemetry-activity-button'));
    await act(async () => {
      appStateListener?.('background');
      await drainMicrotasks();
    });
    expect(executeAction).not.toHaveBeenCalled();
    await expect(loadSpans('connection-a')).resolves.toHaveLength(1);

    await act(async () => {
      appStateListener?.('active');
      await drainMicrotasks();
    });
    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));
    await expect(loadSpans('connection-a')).resolves.toEqual([]);
    appStateSpy.mockRestore();
  });

  it('shows compact diagnostics and uploads the open span on demand', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
      },
    });
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
      result: {
        recorded: 1,
        merged: 0,
        skipped: 0,
        absorbed: 0,
        duplicate: false,
      },
    });
    const { getByTestId, getByText } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-a"
        store={store}
        showSettings
      />,
    );
    await settleAfterRender();

    fireEvent.press(getByTestId('global-settings-time-tracking-diagnostics'));
    fireEvent.press(getByTestId('telemetry-activity-button'));
    expect(getByText('Open span: Session session-')).toBeTruthy();

    fireEvent.press(getByTestId('time-tracking-upload-now'));
    await waitFor(() => {
      expect(getByTestId('time-tracking-pending-count').props.children).toEqual(
        ['Pending uploads: ', 0],
      );
      expect(getByTestId('time-tracking-last-upload').props.children).toEqual([
        'Last upload: ',
        'Successful',
      ]);
    });
    expect(executeAction).toHaveBeenCalledTimes(1);
    expect(getByTestId('time-tracking-entry-0')).toBeTruthy();
    expect(getByText('Uploaded')).toBeTruthy();
    expect(getByText('session-1')).toBeTruthy();
    expect(getByText('0ms')).toBeTruthy();
  });

  it('shows only the ten most recent collected entries', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
      },
    });
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
      result: {
        recorded: 11,
        merged: 0,
        skipped: 0,
        absorbed: 0,
        duplicate: false,
      },
    });
    const sessionIds = Array.from(
      { length: 11 },
      (_, index) => `recent-session-${index}`,
    );
    const { getAllByText, getByTestId, queryByTestId } = render(
      <Host
        backend={createBackend(executeAction)}
        connectionId="connection-recent-entries"
        store={store}
        sessionIds={sessionIds}
        showSettings
      />,
    );
    await settleAfterRender();

    fireEvent.press(getByTestId('global-settings-time-tracking-diagnostics'));
    for (let index = 0; index < sessionIds.length; index += 1) {
      fireEvent.press(getByTestId(`telemetry-activity-button-${index}`));
      await jest.advanceTimersByTimeAsync(1);
    }
    fireEvent.press(getByTestId('time-tracking-upload-now'));

    await waitFor(() => {
      expect(executeAction).toHaveBeenCalledTimes(1);
      expect(getAllByText('Uploaded')).toHaveLength(10);
    });
    expect(getByTestId('time-tracking-entry-9')).toBeTruthy();
    expect(queryByTestId('time-tracking-entry-10')).toBeNull();
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
        new Error(
          "HTTP 404 POST /actions: Unknown application plugin 'missing_plugin'",
        ),
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
      <Host backend={backend} connectionId="connection-a" store={store} />,
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

  it('does not show the unavailable-plugin banner for a rejected span', async () => {
    const store = createMemoryStore({
      [MOBILE_GLOBAL_PREFERENCES_STORAGE_KEY]: {
        timeTrackingEnabled: true,
      },
    });
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      plugin: 'duration_tracking_app',
      action_id: 'record_human_time_spans',
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
    await appendSpan('connection-rejected-span', {
      sessionId: 'missing-session',
      from: new Date(Date.now() - 120_000).toISOString(),
      to: new Date(Date.now() - 60_000).toISOString(),
    });

    render(
      <Host
        backend={backend}
        connectionId="connection-rejected-span"
        store={store}
      />,
    );
    await settleAfterRender();
    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));

    expect(received).toEqual([]);
    await expect(loadSpans('connection-rejected-span')).resolves.toHaveLength(
      1,
    );
    unsubscribe();
  });
});
