import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import { createDefaultSdkRuntime } from '../../runtimeFactory/createDefaultSdkRuntime';
import type { BackendMiddleware } from '../eventedBackend';
import {
  createSessionScopedSuccessEventMiddleware,
} from '../../sessionMutations/createSessionScopedSuccessEventMiddleware';
import { SdkRuntime } from '../sdkRuntime';

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
    executeAction: vi.fn(async () => ({ status: 'ok', plugin: 'p', action_id: 'a', result: {} })),
  } satisfies AgentBackend;

  return {
    ...base,
    ...overrides,
  };
}

describe('evented backend wrapper', () => {
  it('emits mapped mutation events after successful writes', async () => {
    const rawBackend = createFakeBackend();
    const runtime = createDefaultSdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
    });
    const observedTypes: string[] = [];

    runtime.bus.subscribe(() => {
      const ev = runtime.bus.getSnapshot().lastEvent;
      if (ev) {
        observedTypes.push(ev.type);
      }
    });

    await runtime.backend!.setSessionPlugins('s1', ['p1']);
    await runtime.backend!.clearSessionPlugins('s1');
    await runtime.backend!.patchSessionOverrides('s1', { temperature: 0.2 });
    await runtime.backend!.deleteSessionOverride('s1', 'temperature');
    await runtime.backend!.switchSessionAgent('s1', 'agent-b');

    expect(observedTypes).toEqual([
      'session.plugins.changed',
      'session.plugins.changed',
      'session.overrides.changed',
      'session.overrides.changed',
      'session.agent.changed',
    ]);
    expect(rawBackend.setSessionPlugins).toHaveBeenCalledTimes(1);
    expect(rawBackend.clearSessionPlugins).toHaveBeenCalledTimes(1);
    expect(rawBackend.patchSessionOverrides).toHaveBeenCalledTimes(1);
    expect(rawBackend.deleteSessionOverride).toHaveBeenCalledTimes(1);
    expect(rawBackend.switchSessionAgent).toHaveBeenCalledTimes(1);
  });

  it('does not emit when a mutation throws', async () => {
    const rawBackend = createFakeBackend({
      switchSessionAgent: vi.fn(async () => {
        throw new Error('boom');
      }),
    });
    const runtime = createDefaultSdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
    });

    await expect(runtime.backend!.switchSessionAgent('s1', 'agent-b')).rejects.toThrow('boom');
    expect(runtime.bus.getSnapshot().seq).toBe(0);
    expect(runtime.bus.getSnapshot().lastEvent).toBeNull();
  });

  it('does not emit for non-mutation methods', async () => {
    const rawBackend = createFakeBackend();
    const runtime = createDefaultSdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
    });

    await runtime.backend!.listAgents();

    expect(runtime.bus.getSnapshot().seq).toBe(0);
    expect(runtime.bus.getSnapshot().lastEvent).toBeNull();
    expect(rawBackend.listAgents).toHaveBeenCalledTimes(1);
  });

  it('preserves synchronous getCapabilities contract', () => {
    const rawBackend = createFakeBackend();
    const runtime = new SdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
    });

    const caps = runtime.backend!.getCapabilities();
    expect(caps).toEqual(rawBackend.getCapabilities());
    expect(caps).not.toBeInstanceOf(Promise);
  });

  it('supports middleware before/success/finally control', async () => {
    const rawBackend = createFakeBackend();
    const observed: Array<{ type: string; method: unknown }> = [];
    const middleware: BackendMiddleware = async (context, next) => {
      context.bus.emit({
        type: 'custom.before',
        scopeKey: context.scopeKey,
        method: context.method,
      });

      try {
        const result = await next();
        context.bus.emit({
          type: 'custom.success',
          scopeKey: context.scopeKey,
          method: context.method,
        });
        return result;
      } finally {
        context.bus.emit({
          type: 'custom.finally',
          scopeKey: context.scopeKey,
          method: context.method,
        });
      }
    };

    const runtime = new SdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
      backendMiddlewares: [middleware],
    });

    runtime.bus.subscribe(() => {
      const ev = runtime.bus.getSnapshot().lastEvent;
      if (ev?.type.startsWith('custom.')) {
        observed.push({ type: ev.type, method: ev.method });
      }
    });

    await runtime.backend!.modifyMessage('s1', 0, 'updated');

    expect(observed).toEqual([
      { type: 'custom.before', method: 'modifyMessage' },
      { type: 'custom.success', method: 'modifyMessage' },
      { type: 'custom.finally', method: 'modifyMessage' },
    ]);
    expect(rawBackend.modifyMessage).toHaveBeenCalledTimes(1);
  });

  it('supports middleware error handling and emits after error before rethrow', async () => {
    const rawBackend = createFakeBackend();
    const observed: Array<{ type: string; method: unknown }> = [];
    const middleware: BackendMiddleware = async (context, next) => {
      context.bus.emit({
        type: 'custom.before',
        scopeKey: context.scopeKey,
        method: context.method,
      });

      try {
        return await next();
      } catch (error) {
        context.bus.emit({
          type: 'custom.error',
          scopeKey: context.scopeKey,
          method: context.method,
          message: error instanceof Error ? error.message : 'unknown',
        });
        throw error;
      } finally {
        context.bus.emit({
          type: 'custom.finally',
          scopeKey: context.scopeKey,
          method: context.method,
        });
      }
    };

    rawBackend.modifyMessage = vi.fn(async () => {
      throw new Error('boom');
    });

    const runtime = new SdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
      backendMiddlewares: [middleware],
    });

    runtime.bus.subscribe(() => {
      const ev = runtime.bus.getSnapshot().lastEvent;
      if (ev?.type.startsWith('custom.')) {
        observed.push({ type: ev.type, method: ev.method });
      }
    });

    await expect(runtime.backend!.modifyMessage('s1', 0, 'updated')).rejects.toThrow('boom');

    expect(observed).toEqual([
      { type: 'custom.before', method: 'modifyMessage' },
      { type: 'custom.error', method: 'modifyMessage' },
      { type: 'custom.finally', method: 'modifyMessage' },
    ]);
  });

  it('supports adding new method mapping as a dedicated middleware entry', async () => {
    const rawBackend = createFakeBackend();
    const runtime = new SdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
      backendMiddlewares: [
        createSessionScopedSuccessEventMiddleware({
          method: 'modifyMessage',
          eventType: 'session.message.changed',
        }),
      ],
    });

    await runtime.backend!.modifyMessage('s1', 0, 'updated');

    expect(runtime.bus.getSnapshot().lastEvent).toEqual({
      type: 'session.message.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });
  });
});
