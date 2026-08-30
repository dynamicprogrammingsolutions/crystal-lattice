import { afterAll, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import { startBackendServer, waitForAsync } from '../harness';

describe('session request status integration', () => {
  let stopServer: (() => Promise<void>) | null = null;

  afterAll(async () => {
    await stopServer?.();
    stopServer = null;
  });

  it('crosses real FastAPI, HTTP transport, and the production backend adapter', async () => {
    const started = await startBackendServer({
      config: {
        providers: {
          test_provider: {
            provider: 'deterministic_stream',
            model: 'test-model',
            timeout: 60,
            stream_chunk_count: 3,
            stream_chunk_delay_ms: 0,
          },
        },
        plugins: [
          'plugins.deterministic_stream_provider.DeterministicStreamProvider',
        ],
        agents: {
          default: {
            provider: 'test_provider',
          },
        },
      },
      enableTestControl: true,
    });
    stopServer = started.stop;
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;

    const idle = await backend.getSessionRequestStatuses([
      sessionId,
      'missing-session',
    ]);
    expect(idle.statuses).toMatchObject([
      { session_id: sessionId, state: 'idle', basis: 'session_tail' },
    ]);
    expect(idle.missing_session_ids).toEqual(['missing-session']);

    await backend.appendMessage(sessionId, {
      role: 'user',
      content: 'status integration',
    });
    await expect(
      backend.getSessionRequestStatuses([sessionId]),
    ).resolves.toMatchObject({
      statuses: [{ session_id: sessionId, state: 'not_started' }],
    });

    await backend.send(sessionId, {
      configOverrides: {
        stream_chunk_count: 3,
        stream_chunk_delay_ms: 150,
      },
    });
    await waitForAsync(async () => {
      const snapshot = await backend.getSessionRequestStatuses([sessionId]);
      return snapshot.statuses[0]?.state === 'running';
    }, { timeoutMs: 5000, intervalMs: 25 });
    await waitForAsync(async () => {
      const snapshot = await backend.getSessionRequestStatuses([sessionId]);
      return snapshot.statuses[0]?.state === 'succeeded';
    }, { timeoutMs: 10000, intervalMs: 50 });
  });
});