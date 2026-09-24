import {
  FetchTransport,
  RestAgentBackend,
  type AgentBackend,
  type IndexedMessage,
} from '@crystal-lattice/frontend-sdk';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

import {
  startBackendServer,
  type StartedServer,
} from '../../../packages/frontend-sdk/src/integration/harness';
import {
  appendSpan,
  loadSpans,
  type SpanCacheStore,
} from '../src/humanTimeTelemetry/spanCache';
import { HumanTimeSpanUploader } from '../src/humanTimeTelemetry/uploader';

// Deterministic pre-generated spans: this tier proves the transport →
// server → plugin → store → surfacing chain from stored entries. The
// actual collection of user actions is proven by the focused Detox test,
// which asserts that real UI activity lands in this same store.
const CONNECTION_ID = 'integration-connection';

function createMemoryStore(): SpanCacheStore {
  const data = new Map<string, string>();
  return {
    get: async (key) => data.get(key) ?? null,
    set: async (key, value) => {
      data.set(key, value);
    },
    delete: async (key) => {
      data.delete(key);
    },
  };
}

function makeUploader(
  backend: AgentBackend,
  store: SpanCacheStore,
  pluginId: string,
): HumanTimeSpanUploader {
  return new HumanTimeSpanUploader({
    getBackend: () => backend,
    getConnectionId: () => CONNECTION_ID,
    getPluginId: () => pluginId,
    isEnabled: () => true,
    isBusy: () => false,
    store,
  });
}

async function seedSpans(
  store: SpanCacheStore,
  spans: Array<{ sessionId: string | null; fromMs: number; toMs: number }>,
): Promise<void> {
  for (const span of spans) {
    const appended = await appendSpan(
      CONNECTION_ID,
      {
        sessionId: span.sessionId,
        from: new Date(span.fromMs).toISOString(),
        to: new Date(span.toMs).toISOString(),
      },
      store,
    );
    if (!appended) {
      throw new Error('Test setup failed: span was not appended');
    }
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
      (message) => message.message.role === 'assistant',
    );
    if (assistant) {
      return assistant;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
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

describe('human time span upload with a real backend (transport → server → plugin)', () => {
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
      path.join(os.tmpdir(), 'clc-human-time-integration-'),
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
          },
        },
      },
      env: {
        TEST_WORKSPACE: workspace,
      },
      startupTimeoutMs: 30000,
    });
    return started;
  }

  it('uploads stored spans through the real action path and surfaces the session total at the next request finalize', async () => {
    const server = await startServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const store = createMemoryStore();

    // Deterministic spans: one for the session (60s), one session-less (30s).
    const now = Date.now();
    await seedSpans(store, [
      { sessionId, fromMs: now - 240_000, toMs: now - 180_000 },
      { sessionId: null, fromMs: now - 120_000, toMs: now - 90_000 },
    ]);

    const uploader = makeUploader(backend, store, 'duration_tracking_app');
    await expect(uploader.flush()).resolves.toBe('flushed');
    // The confirmed batch is drained from the frontend cache.
    await expect(loadSpans(CONNECTION_ID, store)).resolves.toEqual([]);

    // The stored entries surface through the production request path: the
    // next request finalize stamps the session's human time total onto the
    // assistant message metadata (the chat status bar renders this).
    const assistant = await runChatRequest(backend, sessionId, 'hello spans');
    const metadata = (assistant.message.metadata ?? {}) as Record<
      string,
      unknown
    >;
    expect(metadata.human_time_session_total).toBe(60_000);
    expect(typeof metadata.human_time_session_total_formatted).toBe('string');
    expect(metadata.human_time_session_total_formatted).not.toBe('');
  });

  it('dedups a retried batch by request id so re-uploads never double-count', async () => {
    const server = await startServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const store = createMemoryStore();

    const now = Date.now();
    const spans = [
      { sessionId, fromMs: now - 240_000, toMs: now - 180_000 },
    ];
    await seedSpans(store, spans);

    const uploader = makeUploader(backend, store, 'duration_tracking_app');
    await expect(uploader.flush()).resolves.toBe('flushed');

    // A retry of the same batch (e.g. a removal that never confirmed)
    // re-seeds the same span content, so the content-derived request id is
    // identical and the server must skip it as a duplicate.
    await seedSpans(store, spans);
    await expect(uploader.flush()).resolves.toBe('flushed');
    await expect(loadSpans(CONNECTION_ID, store)).resolves.toEqual([]);

    const assistant = await runChatRequest(backend, sessionId, 'hello retry');
    const metadata = (assistant.message.metadata ?? {}) as Record<
      string,
      unknown
    >;
    expect(metadata.human_time_session_total).toBe(60_000);
  });

  it('classifies an unknown telemetry plugin as a definitive failure and retains the spans', async () => {
    const server = await startServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: server.baseUrl }),
    });
    const store = createMemoryStore();

    const now = Date.now();
    await seedSpans(store, [
      { sessionId: null, fromMs: now - 60_000, toMs: now - 30_000 },
    ]);

    const uploader = makeUploader(backend, store, 'no_such_telemetry_plugin');
    await expect(uploader.flush()).resolves.toBe('definitive-failure');
    // Definitive failures retain the spans; only a setting change re-arms
    // the one-time warning (covered by the unit tier).
    const retained = await loadSpans(CONNECTION_ID, store);
    expect(retained).toHaveLength(1);
    expect(retained[0].sessionId).toBeNull();
  });
});