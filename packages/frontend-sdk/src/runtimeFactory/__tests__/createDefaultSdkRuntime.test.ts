import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import type { BackendMiddleware } from '../../runtime/eventedBackend';
import { createDefaultSdkRuntime } from '../createDefaultSdkRuntime';

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

describe('createDefaultSdkRuntime', () => {
  it('includes default session mutation middleware composition', async () => {
    const rawBackend = createFakeBackend();
    const runtime = createDefaultSdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
    });

    await runtime.backend!.setSessionPlugins('s1', ['p1']);

    expect(runtime.bus.getSnapshot().lastEvent).toEqual({
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });
  });

  it('appends extra backend middlewares after defaults', async () => {
    const rawBackend = createFakeBackend();
    const observed: string[] = [];
    const extraMiddleware: BackendMiddleware = async (context, next) => {
      observed.push(`before:${context.method}`);
      const result = await next();
      observed.push(`after:${context.method}`);
      return result;
    };

    const runtime = createDefaultSdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
      extraBackendMiddlewares: [extraMiddleware],
    });

    await runtime.backend!.setSessionPlugins('s1', ['p1']);

    expect(observed).toEqual(['before:setSessionPlugins', 'after:setSessionPlugins']);
    expect(runtime.bus.getSnapshot().lastEvent).toEqual({
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });
  });
});
