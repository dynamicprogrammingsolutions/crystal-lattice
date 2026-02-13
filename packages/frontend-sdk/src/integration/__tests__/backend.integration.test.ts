import { afterAll, describe, expect, it } from 'vitest';

import { FetchTransport } from '../../transport/fetchTransport';
import { RestAgentBackend } from '../../backend/restBackend';
import { ChatController } from '../../chat/chatController';
import type { IndexedMessage } from '../../types/messages';
import {
  DelayingTransport,
  Gate,
  startBackendServer,
  TrackingTransport,
  waitFor,
  waitForAsync,
} from '../harness';

const RUN = process.env.RUN_BACKEND_INTEGRATION === '1';

const describeIf = RUN ? describe : describe.skip;

describeIf('backend integration (real FastAPI server + plugins + SDK)', () => {
  const serverConfig = {
    providers: {
      test_provider: {
        provider: 'deterministic_stream',
        model: 'test-model',
        timeout: 60,
        stream_chunk_count: 3,
        stream_chunk_delay_ms: 0,
        system_message_enabled: true,
        system_message: 'You are a helpful system template.',
      },
    },
    plugins: [
      'plugins.deterministic_stream_provider.DeterministicStreamProvider',
      'plugins.system_message_feature.SystemMessageFeature',
    ],
    agents: {
      default: {
        provider: 'test_provider',
      },
    },
  };

  let stopServer: (() => Promise<void>) | null = null;
  let baseUrl = '';

  afterAll(async () => {
    if (stopServer) {
      await stopServer();
      stopServer = null;
    }
  });

  async function ensureServer(): Promise<void> {
    if (stopServer) {
      return;
    }
    const started = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
    });
    baseUrl = started.baseUrl;
    stopServer = started.stop;
  }

  async function createSession(backend: RestAgentBackend): Promise<string> {
    const created = await backend.createSession({ agentId: 'default' });
    return created.session.session_id;
  }

  async function bootstrapController(options: {
    transportOptions?: { tracking?: boolean; gate?: Gate };
    range?: { startText: string; endText: string };
  }): Promise<{
    backend: RestAgentBackend;
    controller: ChatController;
    sessionId: string;
    tracking?: TrackingTransport;
    gate?: Gate;
    delaying?: DelayingTransport;
  }> {
    await ensureServer();

    const baseTransport = new FetchTransport({ baseUrl });
    let transport: any = baseTransport;
    let gate: Gate | undefined = options.transportOptions?.gate;
    let delaying: DelayingTransport | undefined;
    if (gate) {
      delaying = new DelayingTransport(transport, gate);
      transport = delaying;
    }
    let tracking: TrackingTransport | undefined;
    if (options.transportOptions?.tracking) {
      tracking = new TrackingTransport(transport);
      transport = tracking;
    }

    const backend = new RestAgentBackend({ transport });
    const sessionId = await createSession(backend);

    const controller = new ChatController({ backend, sessionId });
    const range = options.range ?? { startText: '-50', endText: '' };

    await controller.loadMessagesFromRangeText(range);
    controller.startEventStreaming({ initialSinceId: controller.getSnapshot().eventsCursorId });
    return { backend, controller, sessionId, tracking, gate, delaying };
  }

  function getContents(messages: IndexedMessage[]): string[] {
    return messages.map((m) => `${m.index}:${m.message.role}:${m.message.content}`);
  }

  function indexPlugins(plugins: Array<{ id: string; [k: string]: any }>): Record<string, any> {
    const byId: Record<string, any> = {};
    for (const p of plugins) {
      if (p && typeof p.id === 'string' && p.id) {
        byId[p.id] = p;
      }
    }
    return byId;
  }

  it('A: system_message_feature first append triggers one auto reload and recovers', async () => {
    const { controller, tracking, sessionId } = await bootstrapController({
      transportOptions: { tracking: true },
    });

    expect(tracking).toBeDefined();
    const listPath = `/sessions/${encodeURIComponent(sessionId)}/messages`;
    expect(tracking!.getCount({ method: 'GET', pathPrefix: listPath })).toBe(1);

    await controller.appendMessage({ role: 'user', content: 'hi' });

    await waitFor(() => {
      const snap = controller.getSnapshot();
      return snap.dirty === false && snap.messages.length >= 2;
    }, { timeoutMs: 10000 });

    const snap = controller.getSnapshot();
    expect(snap.dirty).toBe(false);
    expect(getContents(snap.messages).slice(0, 2)).toEqual([
      '0:system:You are a helpful system template.',
      '1:user:hi',
    ]);

    // Initial bootstrap + one auto-reload.
    expect(tracking!.getCount({ method: 'GET', pathPrefix: listPath })).toBeGreaterThanOrEqual(2);
  }, 30000);

  it('B: manual reload during an in-flight request does not leave the session dirty', async () => {
    const { controller } = await bootstrapController({});

    await controller.appendMessage({ role: 'user', content: 'hi' });
    await waitFor(() => controller.getSnapshot().dirty === false, { timeoutMs: 5000 });

    // Start a slow request so that polling overlaps with reload.
    controller.clearRequestState();
    await controller.send({
      configOverrides: {
        stream_chunk_count: 6,
        stream_chunk_delay_ms: 200,
      },
    });

    // Reload shortly after starting the request.
    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });

    await waitFor(() => {
      const snap = controller.getSnapshot();
      const hasAssistant = snap.messages.some((m) => m.message.role === 'assistant');
      return snap.dirty === false && hasAssistant && snap.activeRequestId == null;
    }, { timeoutMs: 20000, intervalMs: 100 });
  }, 30000);

  it('C1: server-side pause of /events keeps a poll in flight; reload stays consistent', async () => {
    const { controller, backend, sessionId } = await bootstrapController({});

    // Pause event delivery.
    await fetch(`${baseUrl}/__test/events/pause`, { method: 'POST' });

    controller.stopEventStreaming();
    controller.startEventStreaming({ initialSinceId: controller.getSnapshot().eventsCursorId });

    // Wait until the server reports at least one waiting /events request.
    await waitForAsync(async () => {
      const resp = await fetch(`${baseUrl}/__test/events/status`);
      const data = await resp.json();
      return !!data.waiters;
    }, { timeoutMs: 5000, intervalMs: 50 });

    // Generate some events.
    await backend.appendMessage(sessionId, { role: 'user', content: 'hi' });
    await backend.send(sessionId, {
      configOverrides: {
        stream_chunk_count: 6,
        stream_chunk_delay_ms: 100,
      },
    });

    // Reload while a poll is blocked.
    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });

    await fetch(`${baseUrl}/__test/events/resume`, { method: 'POST' });

    await waitFor(() => {
      const snap = controller.getSnapshot();
      const hasAssistant = snap.messages.some((m) => m.message.role === 'assistant');
      return snap.dirty === false && hasAssistant;
    }, { timeoutMs: 20000, intervalMs: 100 });
  }, 30000);

  it('C2: client-side delayed /events response keeps a poll in flight; reload stays consistent', async () => {
    const gate = new Gate();
    gate.close();

    const { controller, delaying } = await bootstrapController({ transportOptions: { gate } });
    expect(delaying).toBeDefined();

    await waitFor(() => (delaying!.pendingEventsRequests > 0), { timeoutMs: 5000, intervalMs: 20 });

    // Start a request and reload while /events is delayed.
    await controller.appendMessage({ role: 'user', content: 'hi' });
    controller.clearRequestState();
    await controller.send({
      configOverrides: {
        stream_chunk_count: 6,
        stream_chunk_delay_ms: 100,
      },
    });

    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });

    gate.release();

    await waitFor(() => {
      const snap = controller.getSnapshot();
      const hasAssistant = snap.messages.some((m) => m.message.role === 'assistant');
      return snap.dirty === false && hasAssistant && snap.activeRequestId == null;
    }, { timeoutMs: 20000, intervalMs: 100 });
  }, 30000);

  it('D: session plugins list/set/clear roundtrip', async () => {
    await ensureServer();

    const transport = new FetchTransport({ baseUrl });
    const backend = new RestAgentBackend({ transport });
    const sessionId = await createSession(backend);

    const initial = await backend.listSessionPlugins(sessionId);
    const initialById = indexPlugins(initial);

    expect(initialById.deterministic_stream).toBeDefined();
    expect(initialById.system_message).toBeDefined();
    expect(initialById.system_message.enabled).toBe(true);
    expect(initialById.system_message.source).toBe('implicit');

    await backend.setSessionPlugins(sessionId, ['deterministic_stream']);

    const afterSet = await backend.listSessionPlugins(sessionId);
    const afterSetById = indexPlugins(afterSet);
    expect(afterSetById.deterministic_stream.enabled).toBe(true);
    expect(afterSetById.deterministic_stream.source).toBe('session');
    expect(afterSetById.system_message.enabled).toBe(false);
    expect(afterSetById.system_message.source).toBe('session');

    await backend.clearSessionPlugins(sessionId);

    const afterClear = await backend.listSessionPlugins(sessionId);
    const afterClearById = indexPlugins(afterClear);
    expect(afterClearById.system_message.enabled).toBe(true);
    expect(afterClearById.system_message.source).toBe('implicit');
  }, 30000);

  it('E: disabling system_message removes the synthetic system message from stored history', async () => {
    await ensureServer();

    const transport = new FetchTransport({ baseUrl });
    const backend = new RestAgentBackend({ transport });
    const sessionId = await createSession(backend);

    await backend.setSessionPlugins(sessionId, ['deterministic_stream']);

    await backend.appendMessage(sessionId, { role: 'user', content: 'hi' });
    const listed = await backend.listMessages(sessionId);
    const contents = getContents(listed.messages);

    expect(contents).toEqual(['0:user:hi']);
  }, 30000);
});
