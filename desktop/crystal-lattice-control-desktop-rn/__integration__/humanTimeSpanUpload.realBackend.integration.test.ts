import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

import {
  FetchTransport,
  RestAgentBackend,
  type AgentBackend,
  type IndexedMessage,
} from '@crystal-lattice/frontend-sdk';
import {
  HumanTimeSpanUploader,
  appendHumanTimeSpan,
  loadHumanTimeSpans,
  type SpanCacheStore,
} from '@crystal-lattice/frontend-rn-components';

import {
  startBackendServer,
  type StartedServer,
} from '../../../packages/frontend-sdk/src/integration/harness';

const CONNECTION_ID = 'desktop-integration-connection';

jest.setTimeout(45_000);

function createMemoryStore(): SpanCacheStore {
  const data = new Map<string, string>();
  return {
    get: async key => data.get(key) ?? null,
    set: async (key, value) => {
      data.set(key, value);
    },
    delete: async key => {
      data.delete(key);
    },
  };
}

function makeUploader(
  backend: AgentBackend,
  store: SpanCacheStore,
  pluginId = 'duration_tracking_app',
  onDefinitiveFailure?: (error: unknown) => void,
): HumanTimeSpanUploader {
  return new HumanTimeSpanUploader({
    getBackend: () => backend,
    getConnectionId: () => CONNECTION_ID,
    getPluginId: () => pluginId,
    isEnabled: () => true,
    onDefinitiveFailure,
    store,
  });
}

async function seedSpans(
  store: SpanCacheStore,
  spans: Array<{ sessionId: string | null; fromMs: number; toMs: number }>,
): Promise<void> {
  for (const span of spans) {
    const appended = await appendHumanTimeSpan(
      CONNECTION_ID,
      {
        sessionId: span.sessionId,
        from: new Date(span.fromMs).toISOString(),
        to: new Date(span.toMs).toISOString(),
      },
      store,
    );
    if (!appended) throw new Error('Failed to seed human-time span');
  }
}

async function waitForAssistantMessage(
  backend: RestAgentBackend,
  sessionId: string,
): Promise<IndexedMessage> {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    const result = await backend.listMessages(sessionId, {});
    const assistant = result.messages.find(
      message => message.message.role === 'assistant',
    );
    if (assistant) return assistant;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('Assistant message did not arrive within 30s');
}

async function runChatRequest(
  backend: RestAgentBackend,
  sessionId: string,
  text: string,
): Promise<IndexedMessage> {
  await backend.appendMessage(sessionId, {
    role: 'user',
    content: text,
    metadata: {},
  });
  await backend.send(sessionId, {});
  return await waitForAssistantMessage(backend, sessionId);
}

describe('desktop human-time upload with a real backend', () => {
  let started: StartedServer | null = null;
  let workspace: string | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
    workspace = null;
  });

  async function startServer(): Promise<StartedServer> {
    workspace = fs.mkdtempSync(
      path.join(os.tmpdir(), 'clc-desktop-human-time-integration-'),
    );
    started = await startBackendServer({
      config: {
        providers: {
          stream: {
            provider: 'deterministic_stream',
            model: 'test-model',
            timeout: 60,
            stream_chunk_count: 3,
            stream_chunk_delay_ms: 0,
            working_directory: '${env:TEST_WORKSPACE}',
            duration_tracking_db_path:
              '${env:TEST_WORKSPACE}/human_time.sqlite',
          },
        },
        agents: {
          default: {
            provider: 'stream',
            working_directory: '${env:TEST_WORKSPACE}',
            allowed_paths: ['${env:TEST_WORKSPACE}'],
          },
        },
        plugins: [
          'plugins.deterministic_stream_provider.DeterministicStreamProvider',
          'path:${env:REPO_ROOT}/plugins/timestamp-extension',
          'path:${env:REPO_ROOT}/plugins/duration-tracking',
        ],
        application: {
          duration_tracking: {
            working_directory: '${env:TEST_WORKSPACE}',
            db_path: '${env:TEST_WORKSPACE}/human_time.sqlite',
          },
        },
      },
      env: { TEST_WORKSPACE: workspace },
      startupTimeoutMs: 30_000,
    });
    return started;
  }

  it('uploads session and session-less spans and surfaces the session total', async () => {
    const server = await startServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const store = createMemoryStore();
    const now = Date.now();
    await seedSpans(store, [
      { sessionId, fromMs: now - 240_000, toMs: now - 180_000 },
      { sessionId: null, fromMs: now - 120_000, toMs: now - 90_000 },
    ]);

    await expect(makeUploader(backend, store).flush()).resolves.toBe('flushed');
    await expect(loadHumanTimeSpans(CONNECTION_ID, store)).resolves.toEqual([]);

    const assistant = await runChatRequest(backend, sessionId, 'desktop spans');
    const metadata = (assistant.message.metadata ?? {}) as Record<
      string,
      unknown
    >;
    expect(metadata.human_time_session_total).toBe(60_000);
    const report = await backend.executeAction({
      pluginId: 'duration_tracking_app',
      actionId: 'show_duration_report',
      actionOwner: 'application',
      inputs: { session_id: sessionId },
    });
    expect(
      (report.result as { human_time_summary?: { total_ms?: number } })
        .human_time_summary?.total_ms,
    ).toBe(90_000);
  });

  it('deduplicates a retried content-identical batch', async () => {
    const server = await startServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const store = createMemoryStore();
    const now = Date.now();
    const spans = [{ sessionId, fromMs: now - 240_000, toMs: now - 180_000 }];

    await seedSpans(store, spans);
    await expect(makeUploader(backend, store).flush()).resolves.toBe('flushed');
    await seedSpans(store, spans);
    await expect(makeUploader(backend, store).flush()).resolves.toBe('flushed');

    const assistant = await runChatRequest(backend, sessionId, 'desktop retry');
    const metadata = (assistant.message.metadata ?? {}) as Record<
      string,
      unknown
    >;
    expect(metadata.human_time_session_total).toBe(60_000);
  });

  it('retains spans and reports a definitive unknown-plugin failure', async () => {
    const server = await startServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const store = createMemoryStore();
    const warning = jest.fn();
    const now = Date.now();
    await seedSpans(store, [
      { sessionId: null, fromMs: now - 60_000, toMs: now - 30_000 },
    ]);

    await expect(
      makeUploader(backend, store, 'no_such_telemetry_plugin', warning).flush(),
    ).resolves.toBe('definitive-failure');
    await expect(
      loadHumanTimeSpans(CONNECTION_ID, store),
    ).resolves.toHaveLength(1);
    expect(warning).toHaveBeenCalledTimes(1);
  });

  it('isolates a rejected span and uploads valid neighbors', async () => {
    const server = await startServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const store = createMemoryStore();
    const warning = jest.fn();
    const now = Date.now();
    await seedSpans(store, [
      {
        sessionId: 'missing-session',
        fromMs: now - 360_000,
        toMs: now - 330_000,
      },
      { sessionId, fromMs: now - 240_000, toMs: now - 180_000 },
      { sessionId: null, fromMs: now - 120_000, toMs: now - 90_000 },
    ]);

    await expect(
      makeUploader(backend, store, 'duration_tracking_app', warning).flush(),
    ).resolves.toBe('partial-failure');
    const retained = await loadHumanTimeSpans(CONNECTION_ID, store);
    expect(retained).toHaveLength(1);
    expect(retained[0].sessionId).toBe('missing-session');
    expect(warning).not.toHaveBeenCalled();

    const assistant = await runChatRequest(
      backend,
      sessionId,
      'desktop partial upload',
    );
    const metadata = (assistant.message.metadata ?? {}) as Record<
      string,
      unknown
    >;
    expect(metadata.human_time_session_total).toBe(60_000);
  });
});
