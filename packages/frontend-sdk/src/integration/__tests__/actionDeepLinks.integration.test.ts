import { afterEach, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import { parseActionDeepLink } from '../../plugins/actionDeepLinks';
import { startBackendServer, type StartedServer } from '../harness';

const SERVER_CONFIG = {
  providers: {
    echo: { provider: 'echo_openai_like', model: 'test-model' },
  },
  plugins: [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'tests.generic_callback_app_plugin.GenericCallbackAppPlugin',
  ],
  agents: {
    default: { provider: 'echo' },
  },
  application: {},
};

describe('generic action deep links against a real backend', () => {
  let started: StartedServer | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('parses and executes an omitted-plugin session action through the SDK', async () => {
    started = await startBackendServer({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const url =
      `crystal-lattice://action/test-connection/${sessionId}/complete_external_flow` +
      '?result=approved&nonce=n-123';

    const parsed = parseActionDeepLink(url);

    expect(parsed).toEqual({
      connectionId: 'test-connection',
      sessionId,
      actionId: 'complete_external_flow',
      inputs: {
        result: 'approved',
        nonce: 'n-123',
        redirect_url: url,
      },
      redirectUrl: url,
    });

    const response = await backend.executeSessionAction!({
      sessionId: parsed!.sessionId,
      pluginId: parsed!.pluginId,
      actionId: parsed!.actionId,
      inputs: parsed!.inputs,
    });

    expect(response.status).toBe('ok');
    expect(response.plugin).toBe('generic_callback_app');
    expect(response.action_id).toBe('complete_external_flow');
    expect(response.action_owner).toBe('application');
    expect(response.result).toMatchObject({
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
    });
  });
});