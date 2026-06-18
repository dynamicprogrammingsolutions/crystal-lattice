import {
  FetchTransport,
  RestAgentBackend,
  type Transport,
} from '@crystal-lattice/frontend-sdk';
import {
  startBackendServer,
  type StartedServer,
} from '../../../../packages/frontend-sdk/src/integration/harness';

export interface StartedMobileComponentBackend extends StartedServer {
  transport: Transport;
  backend: RestAgentBackend;
}

export async function startMobileComponentBackend(
  options: Parameters<typeof startBackendServer>[0],
): Promise<StartedMobileComponentBackend> {
  const started = await startBackendServer(options);
  const transport = new FetchTransport({ baseUrl: started.baseUrl });
  const backend = new RestAgentBackend({ transport });

  return {
    ...started,
    transport,
    backend,
  };
}

export async function createMobileComponentSession(
  backend: RestAgentBackend,
  agentId = 'default',
): Promise<string> {
  const created = await backend.createSession({ agentId });
  return created.session.session_id;
}
