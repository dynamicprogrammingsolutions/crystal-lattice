import { FetchTransport, RestAgentBackend } from '@crystal-lattice/frontend-sdk';

import { createActionDeepLinkHandler } from '../src/actionDeepLinkRouting';
import {
  startBackendServer,
  type StartedServer,
} from '../../../packages/frontend-sdk/src/integration/harness';

const SERVER_CONFIG = {
  providers: {
    echo: { provider: 'echo_openai_like', model: 'test-model' },
  },
  plugins: [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'path:${env:BUILTIN_PLUGINS}/generic-callback-app',
  ],
  agents: {
    default: { provider: 'echo' },
  },
  application: {},
};

describe('mobile action deep-link routing with a real backend', () => {
  let started: StartedServer | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('routes handleIncomingUrl to the named connection and session', async () => {
    started = await startBackendServer({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const start = await backend.executeSessionAction!({
      sessionId,
      pluginId: 'generic_callback_app',
      actionId: 'start_external_flow',
      inputs: {
        connection_id: 'test-connection',
        result: 'approved',
        nonce: 'n-123',
      },
    });
    expect(start.status).toBe('ok');
    const copyAction = start.result.display?.actions?.find(
      (action: any) => action.kind === 'copy_text' && action.id === 'copy-generic-callback-link',
    ) as any;
    expect(copyAction).toBeTruthy();
    const url = copyAction.text;

    const handleIncomingUrl = createActionDeepLinkHandler({
      hasConnection: (connectionId) => connectionId === 'test-connection',
      getBackendForConnection: (connectionId) =>
        connectionId === 'test-connection' ? backend : null,
    });

    const result = await handleIncomingUrl(url);

    expect(result).toMatchObject({
      handled: true,
      status: 'ok',
      response: {
        status: 'ok',
        plugin: 'generic_callback_app',
        action_id: 'complete_external_flow',
        action_owner: 'application',
        result: {
          message: 'Generic action complete',
          handled: true,
          action: 'complete_external_flow',
          inputs: {
            result: 'approved',
            nonce: 'n-123',
            redirect_url: url,
          },
          context: {
            session_id: sessionId,
          },
        },
      },
    });
  });
});