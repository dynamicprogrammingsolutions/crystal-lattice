import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

import {
  appendSpan,
  loadSpans,
  removeFirstSpans,
  type SpanCacheStore,
} from '../src/humanTimeTelemetry/spanCache';
import {
  HumanTimeSpanUploader,
  isDefinitiveActionFailure,
} from '../src/humanTimeTelemetry/uploader';
import type { HumanTimeSpan } from '../src/humanTimeTelemetry/spanTracker';

function createMemoryStore(): SpanCacheStore {
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

function createBackend(
  executeAction: jest.Mock,
): AgentBackend {
  return { executeAction } as unknown as AgentBackend;
}

function spanAt(sessionId: string | null, startMs: number, durationMs = 60_000): HumanTimeSpan {
  return {
    sessionId,
    from: new Date(startMs).toISOString(),
    to: new Date(startMs + durationMs).toISOString(),
  };
}

interface UploaderHarness {
  uploader: HumanTimeSpanUploader;
  store: SpanCacheStore;
  executeAction: jest.Mock;
  onDefinitiveFailure: jest.Mock;
  setSpans: (spans: HumanTimeSpan[]) => Promise<void>;
  pendingCount: () => Promise<number>;
}

function createHarness(overrides: {
  spans?: HumanTimeSpan[];
  pluginId?: string;
  enabled?: boolean;
  busy?: boolean;
  batchLimit?: number;
  closeDebounceMs?: number;
  maxSpanAgeMs?: number;
  ageCheckIntervalMs?: number;
  now?: () => number;
} = {}): UploaderHarness {
  const store = createMemoryStore();
  const executeAction = jest.fn();
  const onDefinitiveFailure = jest.fn();
  let clockMs = 1_700_000_000_000;
  const uploader = new HumanTimeSpanUploader({
    getBackend: () => createBackend(executeAction),
    getConnectionId: () => 'connection-a',
    getPluginId: () => overrides.pluginId ?? 'duration_tracking_app',
    isEnabled: () => overrides.enabled ?? true,
    isBusy: () => overrides.busy ?? false,
    onDefinitiveFailure,
    batchLimit: overrides.batchLimit,
    closeDebounceMs: overrides.closeDebounceMs,
    maxSpanAgeMs: overrides.maxSpanAgeMs,
    ageCheckIntervalMs: overrides.ageCheckIntervalMs,
    store,
    now: overrides.now ?? (() => clockMs),
  });
  const setSpans = async (spans: HumanTimeSpan[]) => {
    const existing = await loadSpans('connection-a', store);
    if (existing.length > 0) {
      await removeFirstSpans('connection-a', existing.length, store);
    }
    for (const entry of spans) {
      await appendSpan('connection-a', entry, store);
    }
  };
  const pendingCount = async () =>
    (await loadSpans('connection-a', store)).length;
  return { uploader, store, executeAction, onDefinitiveFailure, setSpans, pendingCount };
}

describe('HumanTimeSpanUploader', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('drains the cache in batches through executeAction and confirms each batch', async () => {
    const harness = createHarness({ batchLimit: 2 });
    const spans = [
      spanAt('s1', 1_000),
      spanAt('s1', 200_000),
      spanAt(null, 400_000),
      spanAt('s2', 600_000),
      spanAt('s2', 800_000),
    ];
    await harness.setSpans(spans);
    harness.executeAction.mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });

    const outcome = await harness.uploader.flush();

    expect(outcome).toBe('flushed');
    expect(harness.executeAction).toHaveBeenCalledTimes(3);
    const first = harness.executeAction.mock.calls[0][0];
    expect(first.pluginId).toBe('duration_tracking_app');
    expect(first.actionId).toBe('record_human_time_spans');
    expect(first.actionOwner).toBe('application');
    const toWire = (list: Array<{ sessionId: string | null; from: string; to: string }>) =>
      list.map((span) => ({ session_id: span.sessionId, from: span.from, to: span.to }));
    expect(first.inputs.spans).toEqual(toWire(spans.slice(0, 2)));
    expect(typeof first.inputs.request_id).toBe('string');
    expect(first.inputs.request_id).toBeTruthy();
    expect(harness.executeAction.mock.calls[1][0].inputs.spans).toEqual(toWire(spans.slice(2, 4)));
    expect(harness.executeAction.mock.calls[2][0].inputs.spans).toEqual(toWire(spans.slice(4)));
    // Distinct batches carry distinct request ids.
    const ids = harness.executeAction.mock.calls.map(
      (call) => call[0].inputs.request_id,
    );
    expect(new Set(ids).size).toBe(3);
    await expect(harness.pendingCount()).resolves.toBe(0);
  });

  it('keeps the request id stable across retries of the same batch', async () => {
    const harness = createHarness();
    const spans = [spanAt('s1', 1_000), spanAt('s1', 200_000)];
    await harness.setSpans(spans);
    harness.executeAction
      .mockRejectedValueOnce(new Error('Network request failed'))
      .mockResolvedValueOnce({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });

    const first = await harness.uploader.flush();
    expect(first).toBe('transient-failure');
    await expect(harness.pendingCount()).resolves.toBe(2);

    const second = await harness.uploader.flush();
    expect(second).toBe('flushed');
    const firstId = harness.executeAction.mock.calls[0][0].inputs.request_id;
    const secondId = harness.executeAction.mock.calls[1][0].inputs.request_id;
    expect(secondId).toBe(firstId);
    await expect(harness.pendingCount()).resolves.toBe(0);
  });

  it('defers while the app reports busy', async () => {
    const harness = createHarness({ busy: true });
    await harness.setSpans([spanAt('s1', 1_000)]);

    const outcome = await harness.uploader.flush();

    expect(outcome).toBe('busy');
    expect(harness.executeAction).not.toHaveBeenCalled();
    await expect(harness.pendingCount()).resolves.toBe(1);
  });

  it('skips flushing when disabled or without a connection', async () => {
    const disabled = createHarness({ enabled: false });
    await disabled.setSpans([spanAt('s1', 1_000)]);
    expect(await disabled.uploader.flush()).toBe('disabled');
    expect(disabled.executeAction).not.toHaveBeenCalled();

    const noBackend = new HumanTimeSpanUploader({
      getBackend: () => null,
      getConnectionId: () => 'connection-a',
      getPluginId: () => 'duration_tracking_app',
      isEnabled: () => true,
      isBusy: () => false,
      onDefinitiveFailure: () => {},
      store: createMemoryStore(),
    });
    expect(await noBackend.flush()).toBe('no-connection');
  });

  it('warns once on a definitive failure and retains the spans', async () => {
    const harness = createHarness();
    await harness.setSpans([spanAt('s1', 1_000), spanAt('s1', 200_000)]);
    const definitive = new Error(
      "HTTP 404 POST /actions: Unknown application plugin 'nope'",
    );
    harness.executeAction.mockRejectedValue(definitive);

    const outcome = await harness.uploader.flush();

    expect(outcome).toBe('definitive-failure');
    expect(harness.onDefinitiveFailure).toHaveBeenCalledTimes(1);
    expect(harness.onDefinitiveFailure).toHaveBeenCalledWith(definitive);
    await expect(harness.pendingCount()).resolves.toBe(2);
  });

  it('does not warn on transient failures', async () => {
    const harness = createHarness();
    await harness.setSpans([spanAt('s1', 1_000)]);
    harness.executeAction.mockRejectedValue(new Error('HTTP 503 POST /actions: busy'));

    const outcome = await harness.uploader.flush();

    expect(outcome).toBe('transient-failure');
    expect(harness.onDefinitiveFailure).not.toHaveBeenCalled();
    await expect(harness.pendingCount()).resolves.toBe(1);
  });

  it('classifies a structured unknown-action error response as a definitive failure', async () => {
    // The action protocol reports an unknown plugin/action as HTTP 200 with
    // a structured error body, not as an HTTP error.
    const harness = createHarness();
    await harness.setSpans([spanAt('s1', 1_000)]);
    harness.executeAction.mockResolvedValue({
      status: 'error',
      plugin: 'no_such_telemetry_plugin',
      action_id: 'record_human_time_spans',
      error_type: 'unknown_action',
      message: "Unknown action_id 'record_human_time_spans'",
      details: {},
    });

    const outcome = await harness.uploader.flush();

    expect(outcome).toBe('definitive-failure');
    expect(harness.onDefinitiveFailure).toHaveBeenCalledTimes(1);
    await expect(harness.pendingCount()).resolves.toBe(1);
  });

  it('treats a structured non-definitive error response as transient', async () => {
    const harness = createHarness();
    await harness.setSpans([spanAt('s1', 1_000)]);
    harness.executeAction.mockResolvedValue({
      status: 'error',
      error_type: 'conflict',
      message: 'Session conflict',
      details: {},
    });

    const outcome = await harness.uploader.flush();

    expect(outcome).toBe('transient-failure');
    expect(harness.onDefinitiveFailure).not.toHaveBeenCalled();
    await expect(harness.pendingCount()).resolves.toBe(1);
  });

  it('coalesces close notifications into one debounced flush', async () => {
    const harness = createHarness({ closeDebounceMs: 2_000 });
    await harness.setSpans([spanAt('s1', 1_000), spanAt(null, 200_000)]);
    harness.executeAction.mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });
    harness.uploader.start();

    harness.uploader.notifySpanClosed();
    jest.advanceTimersByTime(1_000);
    harness.uploader.notifySpanClosed();
    jest.advanceTimersByTime(1_000);
    harness.uploader.notifySpanClosed();
    expect(harness.executeAction).not.toHaveBeenCalled();

    await jest.advanceTimersByTimeAsync(2_000);
    for (let index = 0; index < 5; index += 1) {
      await Promise.resolve();
    }

    expect(harness.executeAction).toHaveBeenCalledTimes(1);
    await expect(harness.pendingCount()).resolves.toBe(0);
    harness.uploader.dispose();
  });

  it('flushes when the oldest pending span ages past the limit', async () => {
    const harness = createHarness({
      maxSpanAgeMs: 300_000,
      ageCheckIntervalMs: 60_000,
    });
    harness.executeAction.mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });
    const nowMs = 1_700_000_000_000;
    // The pending span closed well over the age limit.
    await harness.setSpans([spanAt('s1', nowMs - 400_000)]);
    harness.uploader.start();

    await jest.advanceTimersByTimeAsync(60_000);
    await Promise.resolve();

    expect(harness.executeAction).toHaveBeenCalledTimes(1);
    await expect(harness.pendingCount()).resolves.toBe(0);
    harness.uploader.dispose();
  });

  it('keeps young spans in the cache on the age check', async () => {
    const harness = createHarness({
      maxSpanAgeMs: 300_000,
      ageCheckIntervalMs: 60_000,
    });
    const nowMs = 1_700_000_000_000;
    await harness.setSpans([spanAt('s1', nowMs - 10_000)]);
    harness.uploader.start();

    await jest.advanceTimersByTimeAsync(60_000);
    await Promise.resolve();

    expect(harness.executeAction).not.toHaveBeenCalled();
    await expect(harness.pendingCount()).resolves.toBe(1);
    harness.uploader.dispose();
  });

  it('uploads only the configured connection’s spans', async () => {
    const store = createMemoryStore();
    const executeAction = jest.fn().mockResolvedValue({ status: 'ok', plugin: 'duration_tracking_app', action_id: 'record_human_time_spans', result: { status: 'ok' } });
    await appendSpan('connection-a', spanAt('s1', 1_000), store);
    await appendSpan('connection-b', spanAt('s2', 200_000), store);

    const uploader = new HumanTimeSpanUploader({
      getBackend: () => createBackend(executeAction),
      getConnectionId: () => 'connection-b',
      getPluginId: () => 'duration_tracking_app',
      isEnabled: () => true,
      isBusy: () => false,
      onDefinitiveFailure: () => {},
      store,
    });
    const outcome = await uploader.flush();

    expect(outcome).toBe('flushed');
    expect(executeAction).toHaveBeenCalledTimes(1);
    expect(executeAction.mock.calls[0][0].inputs.spans).toEqual([
      { session_id: 's2', from: spanAt('s2', 200_000).from, to: spanAt('s2', 200_000).to },
    ]);
    await expect(loadSpans('connection-a', store)).resolves.toHaveLength(1);
    await expect(loadSpans('connection-b', store)).resolves.toHaveLength(0);
  });
});

describe('isDefinitiveActionFailure', () => {
  it('classifies HTTP 404/400 as definitive and the rest as transient', () => {
    expect(
      isDefinitiveActionFailure(
        new Error("HTTP 404 POST /actions: Unknown application plugin 'x'"),
      ),
    ).toBe(true);
    expect(
      isDefinitiveActionFailure(
        new Error("HTTP 404 POST /actions: Unknown action_id 'y' for plugin 'x'"),
      ),
    ).toBe(true);
    expect(isDefinitiveActionFailure(new Error('HTTP 400 POST /actions: bad'))).toBe(true);
    expect(isDefinitiveActionFailure(new Error('HTTP 503 POST /actions: busy'))).toBe(false);
    expect(isDefinitiveActionFailure(new Error('Network request failed'))).toBe(false);
    expect(isDefinitiveActionFailure(new Error('Aborted'))).toBe(false);
    expect(isDefinitiveActionFailure('HTTP 404 boom')).toBe(true);
    expect(isDefinitiveActionFailure(null)).toBe(false);
  });
});