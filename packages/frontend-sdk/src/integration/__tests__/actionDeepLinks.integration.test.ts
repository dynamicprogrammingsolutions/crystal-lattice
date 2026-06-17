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
    'path:${env:BUILTIN_PLUGINS}/generic-callback-app',
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

  it('copies, parses, and executes an omitted-plugin session action through the SDK', async () => {
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
    expect(url).toBe(
      `crystal-lattice://action/test-connection/${sessionId}/complete_external_flow` +
        '?result=approved&nonce=n-123',
    );

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