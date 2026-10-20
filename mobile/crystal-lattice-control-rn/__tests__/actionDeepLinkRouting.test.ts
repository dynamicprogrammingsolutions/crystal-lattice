import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

import { createActionDeepLinkHandler } from '../src/actionDeepLinkRouting';

const url =
  'crystal-lattice://action/test-connection/session-123/generic_callback_complete_external_flow?result=approved&nonce=n-123';

function makeBackend(): AgentBackend {
  return {
    executeAction: jest.fn(),
    executeSessionActionCallback: jest.fn(async () => ({
      status: 'ok',
      plugin: 'generic_callback_app',
      action_id: 'complete_external_flow',
      action_owner: 'application',
      result: { message: 'Generic action complete' },
    })),
  } as any;
}

test('handleIncomingUrl executes session action on the named connection', async () => {
  const backend = makeBackend();
  const handler = createActionDeepLinkHandler({
    hasConnection: (connectionId) => connectionId === 'test-connection',
    getBackendForConnection: (connectionId) =>
      connectionId === 'test-connection' ? backend : null,
  });

  const result = await handler(url);

  expect(result).toMatchObject({ handled: true, status: 'ok' });
  expect(backend.executeSessionActionCallback).toHaveBeenCalledWith({
    sessionId: 'session-123',
    pluginId: undefined,
    callbackElementId: 'generic_callback_complete_external_flow',
    redirectUrl: url,
  });
  expect(backend.executeAction).not.toHaveBeenCalled();
});

test('handleIncomingUrl rejects unknown connections without executing', async () => {
  const backend = makeBackend();
  const handler = createActionDeepLinkHandler({
    hasConnection: () => false,
    getBackendForConnection: () => backend,
  });

  const result = await handler(url);

  expect(result).toMatchObject({
    handled: true,
    status: 'error',
    errorType: 'unknown_connection',
  });
  expect(backend.executeSessionActionCallback).not.toHaveBeenCalled();
});

test('handleIncomingUrl queues existing but inactive connections', async () => {
  const queued: unknown[] = [];
  const handler = createActionDeepLinkHandler({
    hasConnection: (connectionId) => connectionId === 'test-connection',
    getBackendForConnection: () => null,
    queuePendingAction: (parsed) => queued.push(parsed),
  });

  const result = await handler(url);

  expect(result).toMatchObject({ handled: true, status: 'queued' });
  expect(queued).toHaveLength(1);
});

test('handleIncomingUrl ignores unrelated urls', async () => {
  const backend = makeBackend();
  const handler = createActionDeepLinkHandler({
    hasConnection: () => true,
    getBackendForConnection: () => backend,
  });

  await expect(handler('https://example.com')).resolves.toEqual({ handled: false });
  expect(backend.executeSessionActionCallback).not.toHaveBeenCalled();
});