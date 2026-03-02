import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import { SdkRuntime } from '../../runtime/sdkRuntime';
import { createDefaultSessionMutationMiddlewares } from '../sessionMutationMiddlewares';

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

describe('session mutation middlewares', () => {
  it('emits mapped mutation events after successful writes', async () => {
    const rawBackend = createFakeBackend();
    const runtime = new SdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
      backendMiddlewares: createDefaultSessionMutationMiddlewares(),
    });

    await runtime.backend!.setSessionPlugins('s1', ['p1']);

    expect(runtime.bus.getSnapshot().lastEvent).toEqual({
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });
  });

  it('does not emit mapped event when a mapped mutation throws', async () => {
    const rawBackend = createFakeBackend({
      switchSessionAgent: vi.fn(async () => {
        throw new Error('boom');
      }),
    });
    const runtime = new SdkRuntime({
      scopeKey: 'conn-1',
      backend: rawBackend,
      backendMiddlewares: createDefaultSessionMutationMiddlewares(),
    });

    await expect(runtime.backend!.switchSessionAgent('s1', 'agent-b')).rejects.toThrow('boom');
    expect(runtime.bus.getSnapshot().lastEvent).toBeNull();
  });
});
