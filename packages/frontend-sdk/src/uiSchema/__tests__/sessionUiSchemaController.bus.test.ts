import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import { SdkEventBus } from '../../runtime/sdkEventBus';
import { SESSION_MUTATION_EVENT_TYPES } from '../../sessionMutations/sessionMutationEventTypes';
import { SessionUiSchemaController } from '../sessionUiSchemaController';

function createFakeBackend(overrides: Partial<AgentBackend> = {}): AgentBackend {
  const base = {
    kind: 'fake',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: true,
      sessionConfigOverrides: true,
      sessionPlugins: true,
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: vi.fn(async () => ['default']),
    getSessionAgent: vi.fn(async () => 'default'),
    switchSessionAgent: vi.fn(async () => {}),
    createSession: vi.fn(async () => ({ session: { session_id: 's1' } })),
    listSessions: vi.fn(async () => []),
    forkSession: vi.fn(async () => ({ session: { session_id: 's2' }, source_session_id: 's1' })),
    listSessionPlugins: vi.fn(async () => []),
    setSessionPlugins: vi.fn(async () => {}),
    clearSessionPlugins: vi.fn(async () => {}),
    listMessages: vi.fn(async () => ({ messages: [], cursorEventId: null, activeRequestId: null })),
    appendMessage: vi.fn(async () => {}),
    sendMessage: vi.fn(async () => ({ status: 'started', request_id: 'r1', session_id: 's1' })),
    modifyMessage: vi.fn(async () => {}),
    deleteMessages: vi.fn(async () => ({ deleted_indices: [] })),
    send: vi.fn(async () => ({ status: 'started', request_id: 'r1' })),
    cancelRequest: vi.fn(async () => {}),
    listEvents: vi.fn(async () => []),
    getSessionUiSchema: vi.fn(async () => []),
    getSessionOverrides: vi.fn(async () => ({})),
    patchSessionOverrides: vi.fn(async () => {}),
    deleteSessionOverride: vi.fn(async () => {}),
    getSessionConfigSchema: vi.fn(async () => []),
    getSessionBaseConfig: vi.fn(async () => ({})),
    listApplicationActions: vi.fn(async () => []),
    listApplicationUiSchema: vi.fn(async () => []),
    executeAction: vi.fn(async () => ({
      status: 'ok' as const,
      plugin: 'p',
      action_id: 'a',
      result: {},
    })),
  } satisfies AgentBackend;

  return {
    ...base,
    ...overrides,
  };
}

async function flushAsyncWork(): Promise<void> {
  await Promise.resolve();
  await new Promise<void>((resolve) => {
    setTimeout(() => resolve(), 0);
  });
}

function createDeferred<T>(): {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (error: unknown) => void;
} {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('SessionUiSchemaController bus invalidation', () => {
  it('invalidates and reloads for matching session mutation events', async () => {
    const getSessionUiSchema = vi
      .fn()
      .mockResolvedValueOnce([{ key: 'old', ui_type: 'footer' }])
      .mockResolvedValueOnce([{ key: 'new', ui_type: 'footer' }]);
    const backend = createFakeBackend({ getSessionUiSchema });
    const bus = new SdkEventBus();
    const controller = new SessionUiSchemaController({
      backend,
      cacheKey: 'conn-match',
      scopeKey: 'conn-match',
      sessionId: 's1',
      bus,
      enabled: true,
    });

    await controller.load();
    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);

    bus.emit({
      type: SESSION_MUTATION_EVENT_TYPES.PLUGINS_CHANGED,
      scopeKey: 'conn-match',
      sessionId: 's1',
    });
    await flushAsyncWork();

    expect(getSessionUiSchema).toHaveBeenCalledTimes(2);
    expect(controller.getSnapshot().elements).toEqual([{ key: 'new', ui_type: 'footer' }]);

    controller.dispose();
  });

  it('ignores events for other session ids', async () => {
    const getSessionUiSchema = vi
      .fn()
      .mockResolvedValueOnce([{ key: 'old', ui_type: 'footer' }])
      .mockResolvedValueOnce([{ key: 'new', ui_type: 'footer' }]);
    const backend = createFakeBackend({ getSessionUiSchema });
    const bus = new SdkEventBus();
    const controller = new SessionUiSchemaController({
      backend,
      cacheKey: 'conn-other-session',
      scopeKey: 'conn-other-session',
      sessionId: 's1',
      bus,
      enabled: true,
    });

    await controller.load();
    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);

    bus.emit({
      type: SESSION_MUTATION_EVENT_TYPES.OVERRIDES_CHANGED,
      scopeKey: 'conn-other-session',
      sessionId: 's2',
    });
    await flushAsyncWork();

    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot().elements).toEqual([{ key: 'old', ui_type: 'footer' }]);

    controller.dispose();
  });

  it('ignores events for other scope keys', async () => {
    const getSessionUiSchema = vi
      .fn()
      .mockResolvedValueOnce([{ key: 'old', ui_type: 'footer' }])
      .mockResolvedValueOnce([{ key: 'new', ui_type: 'footer' }]);
    const backend = createFakeBackend({ getSessionUiSchema });
    const bus = new SdkEventBus();
    const controller = new SessionUiSchemaController({
      backend,
      cacheKey: 'conn-scope-controller',
      scopeKey: 'conn-scope-controller',
      sessionId: 's1',
      bus,
      enabled: true,
    });

    await controller.load();
    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);

    bus.emit({
      type: SESSION_MUTATION_EVENT_TYPES.AGENT_CHANGED,
      scopeKey: 'conn-scope-event',
      sessionId: 's1',
    });
    await flushAsyncWork();

    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot().elements).toEqual([{ key: 'old', ui_type: 'footer' }]);

    controller.dispose();
  });

  it('invalidates without immediate reload while disabled', async () => {
    const getSessionUiSchema = vi
      .fn()
      .mockResolvedValueOnce([{ key: 'old', ui_type: 'footer' }])
      .mockResolvedValueOnce([{ key: 'new', ui_type: 'footer' }]);
    const backend = createFakeBackend({ getSessionUiSchema });
    const bus = new SdkEventBus();
    const controller = new SessionUiSchemaController({
      backend,
      cacheKey: 'conn-disabled',
      scopeKey: 'conn-disabled',
      sessionId: 's1',
      bus,
      enabled: false,
    });

    await controller.load();
    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);

    bus.emit({
      type: SESSION_MUTATION_EVENT_TYPES.PLUGINS_CHANGED,
      scopeKey: 'conn-disabled',
      sessionId: 's1',
    });
    await flushAsyncWork();

    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);

    await controller.load();
    expect(getSessionUiSchema).toHaveBeenCalledTimes(2);
    expect(controller.getSnapshot().elements).toEqual([{ key: 'new', ui_type: 'footer' }]);

    controller.dispose();
  });

  it('coalesces an in-flight load into one follow-up reload', async () => {
    const deferred = createDeferred<Array<{ key: string; ui_type: string }>>();
    const getSessionUiSchema = vi
      .fn()
      .mockImplementationOnce(async () => deferred.promise)
      .mockResolvedValueOnce([{ key: 'fresh', ui_type: 'footer' }]);
    const backend = createFakeBackend({ getSessionUiSchema });
    const bus = new SdkEventBus();
    const controller = new SessionUiSchemaController({
      backend,
      cacheKey: 'conn-coalesce',
      scopeKey: 'conn-coalesce',
      sessionId: 's1',
      bus,
      enabled: true,
    });

    const loadPromise = controller.load();
    expect(getSessionUiSchema).toHaveBeenCalledTimes(1);

    bus.emit({
      type: SESSION_MUTATION_EVENT_TYPES.OVERRIDES_CHANGED,
      scopeKey: 'conn-coalesce',
      sessionId: 's1',
    });

    deferred.resolve([{ key: 'stale', ui_type: 'footer' }]);
    await loadPromise;

    expect(getSessionUiSchema).toHaveBeenCalledTimes(2);
    expect(controller.getSnapshot().elements).toEqual([{ key: 'fresh', ui_type: 'footer' }]);

    controller.dispose();
  });
});
