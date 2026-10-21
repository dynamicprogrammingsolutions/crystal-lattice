import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import { createActionDeepLinkHandler } from '../actionDeepLinkRouting';

const url =
  'crystal-lattice://action/test-connection/session-123/generic_callback_complete_external_flow?result=approved&nonce=n-123';

function makeBackend(): AgentBackend {
  return {
    executeAction: vi.fn(),
    executeSessionActionCallback: vi.fn(async () => ({
      status: 'ok',
      plugin: 'generic_callback_app',
      action_id: 'complete_external_flow',
      action_owner: 'application',
      result: { message: 'Generic action complete' },
    })),
  } as any;
}

describe('createActionDeepLinkHandler', () => {
  it('routes an opaque callback to the named connection and callback element', async () => {
    const backend = makeBackend();
    const handler = createActionDeepLinkHandler({
      hasConnection: (connectionId) => connectionId === 'test-connection',
      getBackendForConnection: () => backend,
    });

    await expect(handler(url)).resolves.toMatchObject({
      handled: true,
      status: 'ok',
    });
    expect(backend.executeSessionActionCallback).toHaveBeenCalledWith({
      sessionId: 'session-123',
      pluginId: undefined,
      callbackElementId: 'generic_callback_complete_external_flow',
      redirectUrl: url,
    });
  });

  it('queues a known connection without an active backend', async () => {
    const queued = vi.fn();
    const handler = createActionDeepLinkHandler({
      hasConnection: () => true,
      getBackendForConnection: () => null,
      queuePendingAction: queued,
    });

    await expect(handler(url)).resolves.toMatchObject({
      handled: true,
      status: 'queued',
    });
    expect(queued).toHaveBeenCalledOnce();
  });

  it('rejects unknown connections before backend dispatch', async () => {
    const backend = makeBackend();
    const handler = createActionDeepLinkHandler({
      hasConnection: () => false,
      getBackendForConnection: () => backend,
    });

    await expect(handler(url)).resolves.toMatchObject({
      handled: true,
      status: 'error',
      errorType: 'unknown_connection',
    });
    expect(backend.executeSessionActionCallback).not.toHaveBeenCalled();
  });
});