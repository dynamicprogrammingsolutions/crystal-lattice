import { FetchTransport, RestAgentBackend, parseActionDeepLink } from '@crystal-lattice/frontend-sdk';

import { createActionDeepLinkHandler } from '../src/actionDeepLinkRouting';
import {
  startBackendServer,
  type StartedServer,
} from '../../../packages/frontend-sdk/src/integration/harness';
import {
  startMcpAuthFixture,
  type McpAuthFixture,
} from '../../../packages/frontend-sdk/src/integration/mcpAuthFixture';

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
        mcp_enabled: true,
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

function displayActions(response: any): any[] {
  const actions = response?.result?.display?.actions;
  return Array.isArray(actions) ? actions : [];
}

describe('mobile MCP login deep-link routing with a real backend', () => {
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

  it('routes the MCP completion callback to the named connection and session', async () => {
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
    const state = authorizationUrl.searchParams.get('state');
    const redirectUri = authorizationUrl.searchParams.get('redirect_uri');
    expect(state).toBeTruthy();
    expect(redirectUri).toBeTruthy();

    const callbackUrl = `${redirectUri}&code=code-123&state=${state}`;
    expect(parseActionDeepLink(callbackUrl)).toMatchObject({
      connectionId: 'test-connection',
      sessionId,
      pluginId: 'mcp_runtime_app',
      actionId: 'mcp_complete_login',
    });

    const handleIncomingUrl = createActionDeepLinkHandler({
      hasConnection: (connectionId) => connectionId === 'test-connection',
      getBackendForConnection: (connectionId) =>
        connectionId === 'test-connection' ? backend : null,
    });

    const result = await handleIncomingUrl(callbackUrl);

    expect(result).toMatchObject({
      handled: true,
      status: 'ok',
      response: {
        status: 'ok',
        plugin: 'mcp_runtime_app',
        action_id: 'mcp_complete_login',
        result: {
          message: 'Signed in to protected.',
        },
      },
    });
    expect(fixture.tokenRequests).toHaveLength(1);
    expect(fixture.mcpAuthorizationHeaders).toContain('Bearer access-123');
  }, 60000);
});