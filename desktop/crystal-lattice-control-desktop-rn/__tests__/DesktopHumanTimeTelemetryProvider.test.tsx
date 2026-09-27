import React from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AppState, Pressable, Text } from 'react-native';
import { act, fireEvent, render, waitFor } from '@testing-library/react-native';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import { subscribeDisplayPresentation } from '@crystal-lattice/frontend-sdk';
import {
  appendHumanTimeSpan,
  loadHumanTimeSpans,
} from '@crystal-lattice/frontend-rn-components';

import {
  DesktopHumanTimeTelemetryProvider,
  useDesktopHumanTimeTelemetry,
} from '../src/humanTimeTelemetry/DesktopHumanTimeTelemetryProvider';
import { desktopHumanTimeDiagnosticsBridge } from '../src/humanTimeTelemetry/desktopHumanTimeDiagnostics';
import { asyncStorageKeyValueStore } from '../src/storage/asyncStorageKeyValueStore';

function backend(executeAction: jest.Mock): AgentBackend {
  return { executeAction } as unknown as AgentBackend;
}

function Probe({
  connectionId,
  sessionId,
  testID,
  splitTestID,
}: {
  connectionId: string;
  sessionId: string | null;
  testID: string;
  splitTestID?: string;
}) {
  const { recordActivity, splitForComposedMessage } =
    useDesktopHumanTimeTelemetry();
  return (
    <>
      <Pressable
        testID={testID}
        onPress={() => recordActivity(connectionId, sessionId)}
      >
        <Text>activity</Text>
      </Pressable>
      {splitTestID ? (
        <Pressable
          testID={splitTestID}
          onPress={() => splitForComposedMessage(connectionId, sessionId)}
        >
          <Text>split</Text>
        </Pressable>
      ) : null}
    </>
  );
}

async function drainMicrotasks() {
  for (let index = 0; index < 10; index += 1) {
    await Promise.resolve();
  }
}

describe('DesktopHumanTimeTelemetryProvider', () => {
  beforeEach(async () => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2026-09-25T10:00:00.000Z'));
    await AsyncStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('routes spans to their owning connections and uploads on demand', async () => {
    const executeA = jest.fn().mockResolvedValue({
      status: 'ok',
      result: { recorded: 1, skipped: 0 },
    });
    const executeB = jest.fn().mockResolvedValue({
      status: 'ok',
      result: { recorded: 1, skipped: 0 },
    });
    const backends: Record<string, AgentBackend> = {
      a: backend(executeA),
      b: backend(executeB),
    };
    const screen = render(
      <DesktopHumanTimeTelemetryProvider
        enabled
        pluginId="duration_tracking_app"
        inactivityMs={30_000}
        connectionIds={['a', 'b']}
        connectedConnectionIds={['a', 'b']}
        activeSurfaceKey="session:a:s1"
        getBackend={id => backends[id] ?? null}
        store={asyncStorageKeyValueStore}
      >
        <Probe connectionId="a" sessionId="s1" testID="activity-a" />
        <Probe connectionId="b" sessionId="s2" testID="activity-b" />
      </DesktopHumanTimeTelemetryProvider>,
    );

    fireEvent.press(screen.getByTestId('activity-a'));
    await jest.advanceTimersByTimeAsync(1_000);
    fireEvent.press(screen.getByTestId('activity-a'));
    fireEvent.press(screen.getByTestId('activity-b'));
    await jest.advanceTimersByTimeAsync(1_000);
    fireEvent.press(screen.getByTestId('activity-b'));
    await act(async () => {
      await desktopHumanTimeDiagnosticsBridge.uploadNow();
    });

    expect(executeA).toHaveBeenCalledTimes(1);
    expect(executeA.mock.calls[0][0].inputs.spans[0].session_id).toBe('s1');
    expect(executeB).toHaveBeenCalledTimes(1);
    expect(executeB.mock.calls[0][0].inputs.spans[0].session_id).toBe('s2');
    await expect(
      loadHumanTimeSpans('a', asyncStorageKeyValueStore),
    ).resolves.toEqual([]);
    await expect(
      loadHumanTimeSpans('b', asyncStorageKeyValueStore),
    ).resolves.toEqual([]);
  });

  it('closes on background and uploads when the app foregrounds', async () => {
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      result: { recorded: 1, skipped: 0 },
    });
    let appStateListener: ((state: string) => void) | null = null;
    const appStateSpy = jest
      .spyOn(AppState, 'addEventListener')
      .mockImplementation((_event, listener) => {
        appStateListener = listener as (state: string) => void;
        return { remove: jest.fn() };
      });
    const screen = render(
      <DesktopHumanTimeTelemetryProvider
        enabled
        pluginId="duration_tracking_app"
        inactivityMs={30_000}
        connectionIds={['a']}
        connectedConnectionIds={['a']}
        activeSurfaceKey="session:a:s1"
        getBackend={() => backend(executeAction)}
        store={asyncStorageKeyValueStore}
      >
        <Probe connectionId="a" sessionId="s1" testID="activity-a" />
      </DesktopHumanTimeTelemetryProvider>,
    );

    fireEvent.press(screen.getByTestId('activity-a'));
    await act(async () => {
      appStateListener?.('background');
      await drainMicrotasks();
    });
    expect(executeAction).not.toHaveBeenCalled();
    await expect(
      loadHumanTimeSpans('a', asyncStorageKeyValueStore),
    ).resolves.toHaveLength(1);

    await act(async () => {
      appStateListener?.('active');
      await drainMicrotasks();
    });
    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));
    appStateSpy.mockRestore();
  });

  it('splits at composed-message submission and starts a fresh inactivity span', async () => {
    const screen = render(
      <DesktopHumanTimeTelemetryProvider
        enabled
        pluginId="duration_tracking_app"
        inactivityMs={30_000}
        connectionIds={['a']}
        connectedConnectionIds={[]}
        activeSurfaceKey="session:a:s1"
        getBackend={() => null}
        store={asyncStorageKeyValueStore}
      >
        <Probe
          connectionId="a"
          sessionId="s1"
          testID="activity-a"
          splitTestID="split-a"
        />
      </DesktopHumanTimeTelemetryProvider>,
    );

    fireEvent.press(screen.getByTestId('activity-a'));
    await act(async () => {
      await jest.advanceTimersByTimeAsync(10_000);
    });
    fireEvent.press(screen.getByTestId('split-a'));
    await act(async () => {
      await drainMicrotasks();
    });

    const firstPending = await loadHumanTimeSpans(
      'a',
      asyncStorageKeyValueStore,
    );
    expect(firstPending).toHaveLength(1);
    expect(
      Date.parse(firstPending[0].to) - Date.parse(firstPending[0].from),
    ).toBe(10_000);
    expect(
      desktopHumanTimeDiagnosticsBridge.getSnapshot().openSpan?.span.from,
    ).toBe('2026-09-25T10:00:10.000Z');

    await act(async () => {
      await jest.advanceTimersByTimeAsync(30_000);
      await drainMicrotasks();
    });

    const allPending = await loadHumanTimeSpans(
      'a',
      asyncStorageKeyValueStore,
    );
    expect(allPending).toHaveLength(2);
    expect(
      Date.parse(allPending[1].to) - Date.parse(allPending[1].from),
    ).toBe(30_000);
  });

  it('uploads valid neighbors, retains only rejected spans, and shows no unavailable warning', async () => {
    const rejected = {
      sessionId: 'missing-session',
      from: '2026-09-24T10:00:00.000Z',
      to: '2026-09-24T10:01:00.000Z',
    };
    const valid = {
      sessionId: null,
      from: '2026-09-24T10:02:00.000Z',
      to: '2026-09-24T10:03:00.000Z',
    };
    await appendHumanTimeSpan('a', rejected, asyncStorageKeyValueStore);
    await appendHumanTimeSpan('a', valid, asyncStorageKeyValueStore);

    const executeAction = jest.fn().mockImplementation(async ({ inputs }) => {
      const skipped = inputs.spans.some(
        (span: { session_id: string | null }) =>
          span.session_id === 'missing-session',
      );
      return {
        status: 'ok',
        result: {
          recorded: skipped ? 0 : inputs.spans.length,
          skipped: skipped ? 1 : 0,
        },
      };
    });
    const activeBackend = backend(executeAction);
    const warnings: unknown[] = [];
    const unsubscribe = subscribeDisplayPresentation(activeBackend, envelope =>
      warnings.push(envelope),
    );

    render(
      <DesktopHumanTimeTelemetryProvider
        enabled
        pluginId="duration_tracking_app"
        inactivityMs={30_000}
        connectionIds={['a']}
        connectedConnectionIds={['a']}
        activeSurfaceKey="list:a"
        getBackend={() => activeBackend}
        store={asyncStorageKeyValueStore}
      >
        <Text>host</Text>
      </DesktopHumanTimeTelemetryProvider>,
    );

    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(3));
    await expect(
      loadHumanTimeSpans('a', asyncStorageKeyValueStore),
    ).resolves.toEqual([rejected]);
    expect(warnings).toEqual([]);
    expect(desktopHumanTimeDiagnosticsBridge.getSnapshot().pendingCount).toBe(
      1,
    );
    unsubscribe();
  });

  it('shows the unavailable-plugin warning once for a definitive action failure', async () => {
    await appendHumanTimeSpan(
      'a',
      {
        sessionId: 'session-1',
        from: '2026-09-24T10:00:00.000Z',
        to: '2026-09-24T10:01:00.000Z',
      },
      asyncStorageKeyValueStore,
    );
    const executeAction = jest
      .fn()
      .mockRejectedValue(
        new Error(
          "HTTP 404 POST /actions: Unknown application plugin 'missing'",
        ),
      );
    const activeBackend = backend(executeAction);
    const warnings: unknown[] = [];
    const unsubscribe = subscribeDisplayPresentation(activeBackend, envelope =>
      warnings.push(envelope),
    );

    render(
      <DesktopHumanTimeTelemetryProvider
        enabled
        pluginId="missing"
        inactivityMs={30_000}
        connectionIds={['a']}
        connectedConnectionIds={['a']}
        activeSurfaceKey="session:a:session-1"
        getBackend={() => activeBackend}
        store={asyncStorageKeyValueStore}
      >
        <Text>host</Text>
      </DesktopHumanTimeTelemetryProvider>,
    );

    await waitFor(() => expect(warnings).toHaveLength(1));
    await act(async () => {
      await desktopHumanTimeDiagnosticsBridge.uploadNow();
    });
    expect(executeAction).toHaveBeenCalledTimes(2);
    expect(warnings).toHaveLength(1);
    expect((warnings[0] as any).display.body).toContain(
      'telemetry plugin is not available',
    );
    unsubscribe();
  });

  it('includes configurable inactivity and ignores session-less activity', async () => {
    const executeAction = jest.fn().mockResolvedValue({
      status: 'ok',
      result: { recorded: 1, skipped: 0 },
    });
    const screen = render(
      <DesktopHumanTimeTelemetryProvider
        enabled
        pluginId="duration_tracking_app"
        inactivityMs={60_000}
        connectionIds={['a']}
        connectedConnectionIds={['a']}
        activeSurfaceKey="session:a:s1"
        getBackend={() => backend(executeAction)}
        store={asyncStorageKeyValueStore}
      >
        <Probe connectionId="a" sessionId={null} testID="session-less" />
        <Probe connectionId="a" sessionId="s1" testID="session" />
      </DesktopHumanTimeTelemetryProvider>,
    );

    fireEvent.press(screen.getByTestId('session-less'));
    fireEvent.press(screen.getByTestId('session'));
    await jest.advanceTimersByTimeAsync(60_000);
    await jest.advanceTimersByTimeAsync(2_000);
    await waitFor(() => expect(executeAction).toHaveBeenCalledTimes(1));

    const spans = executeAction.mock.calls[0][0].inputs.spans;
    expect(spans).toHaveLength(1);
    expect(spans[0].session_id).toBe('s1');
    expect(Date.parse(spans[0].to) - Date.parse(spans[0].from)).toBe(60_000);
  });
});
