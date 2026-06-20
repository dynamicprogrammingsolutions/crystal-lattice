import { afterEach, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import { parseActionDeepLink } from '../../plugins/actionDeepLinks';
import { startBackendServer, type StartedServer } from '../harness';
import { startMcpAuthFixture, type McpAuthFixture } from '../mcpAuthFixture';

function serverConfig(fixture: McpAuthFixture) {
  return {
    providers: {
      echo: { provider: 'echo_openai_like', model: 'test-model' },
    },
    plugins: [
      'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
      'path:${env:REPO_ROOT}/plugins/mcp-runtime-app',
    ],
    agents: {
      default: {
        provider: 'echo',
        mcp_enabled: false,
        mcp_fail_on_startup_error: false,
        mcp_servers: {
          protected: {
            enabled: true,
            transport: 'http',
            url: fixture.mcpUrl,
            startup_timeout_seconds: 1,
            oauth_authorization_url: fixture.authorizeUrl,
            oauth_token_endpoint: fixture.tokenUrl,
            oauth_client_id: 'client-123',
          },
        },
      },
    },
    application: {},
  };
}

function displayBody(response: any): string {
  const body = response?.result?.display?.body;
  return typeof body === 'string' ? body : '';
}

function displayActions(response: any): any[] {
  const actions = response?.result?.display?.actions;
  return Array.isArray(actions) ? actions : [];
}

describe('MCP runtime login flow against a real backend', () => {
  let started: StartedServer | null = null;
  let fixture: McpAuthFixture | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
    if (fixture) {
      await fixture.stop();
      fixture = null;
    }
  });

  it('checks auth-required status before a request and completes the callback action', async () => {
    fixture = await startMcpAuthFixture();
    started = await startBackendServer({
      config: serverConfig(fixture),
      startupTimeoutMs: 30000,
    });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    await backend.patchSessionOverrides(sessionId, { mcp_enabled: true });

    const checked = await backend.executeSessionAction!({
      sessionId,
      pluginId: 'mcp_runtime_app',
      actionId: 'mcp_check_servers',
      inputs: { connection_id: 'test-connection' },
    });

    expect(checked.status).toBe('ok');
    expect(displayBody(checked)).toContain('protected');
    expect(displayBody(checked)).toContain('auth_required');
    expect(displayActions(checked).some((action) => action.action_id === 'mcp_start_login')).toBe(true);

    const login = await backend.executeSessionAction!({
      sessionId,
      pluginId: 'mcp_runtime_app',
      actionId: 'mcp_start_login',
      inputs: {
        server_name: 'protected',
        connection_id: 'test-connection',
      },
    });

    expect(login.status).toBe('ok');
    const copyAction = displayActions(login).find(
      (action) => action.kind === 'copy_text' && action.id === 'copy-mcp-login-protected',
    );
    expect(copyAction).toBeTruthy();
    const authorizationUrl = new URL(copyAction.text);
    expect(authorizationUrl.origin).toBe(fixture.baseUrl);
    expect(authorizationUrl.pathname).toBe('/authorize');
    const state = authorizationUrl.searchParams.get('state');
    const redirectUri = authorizationUrl.searchParams.get('redirect_uri');
    expect(state).toBeTruthy();
    expect(redirectUri).toBeTruthy();

    const callbackUrl = `${redirectUri}&code=code-123&state=${state}`;
    const parsed = parseActionDeepLink(callbackUrl);
    expect(parsed).toMatchObject({
      connectionId: 'test-connection',
      sessionId,
      pluginId: 'mcp_runtime_app',
      actionId: 'mcp_complete_login',
    });

    const completed = await backend.executeSessionAction!({
      sessionId: parsed!.sessionId,
      pluginId: parsed!.pluginId,
      actionId: parsed!.actionId,
      inputs: parsed!.inputs,
    });

    expect(completed.status).toBe('ok');
    expect(completed.result.message).toBe('Signed in to protected.');
    expect(fixture.tokenRequests).toHaveLength(1);
    expect(fixture.tokenRequests[0].code).toBe('code-123');
    expect(fixture.mcpAuthorizationHeaders).toContain('Bearer access-123');
  }, 60000);
});