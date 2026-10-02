import { afterAll, describe, expect, it } from 'vitest';

import { FetchTransport } from '../../transport/fetchTransport';
import { RestAgentBackend } from '../../backend/restBackend';
import { ChatController } from '../../chat/chatController';
import type { IndexedMessage } from '../../types/messages';
import { storeSessionAttachment } from '../../plugins/attachmentActions';
import {
  DelayingTransport,
  Gate,
  startBackendServer,
  TrackingTransport,
  waitFor,
  waitForAsync,
} from '../harness';

describe('backend integration (real FastAPI server + plugins + SDK)', () => {
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
      'path:${env:REPO_ROOT}/plugins/feature-system-message',
    ],
    agents: {
      default: {
        provider: 'test_provider',
        display: {
          title: 'Default agent',
          description: 'Primary deterministic profile.',
          order: 20,
        },
      },
      alternate: {
        provider: 'test_provider',
        display: {
          title: 'Alternative agent',
          description: 'Secondary deterministic profile.',
          order: 10,
        },
      },
    },
  };

  const toolLoopServerConfig = {
    providers: {
      dummy: {
        provider: 'dummy_provider',
        model: 'dummy-model',
        sleep_per_char: 0.01,
      },
    },
    plugins: [
      'tests.dummy_provider.DummyProvider',
      'tests.dummy_tool.DummyCalculator',
    ],
    agents: {
      default: {
        provider: 'dummy',
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

  it(
    'preserves agent ids and exposes ordered descriptors through real HTTP',
    async () => {
      await ensureServer();
      const backend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl }),
      });

      await expect(backend.listAgents()).resolves.toEqual([
        'alternate',
        'default',
      ]);
      await expect(backend.listAgentDescriptors()).resolves.toEqual([
        {
          id: 'alternate',
          title: 'Alternative agent',
          description: 'Secondary deterministic profile.',
          order: 10,
        },
        {
          id: 'default',
          title: 'Default agent',
          description: 'Primary deterministic profile.',
          order: 20,
        },
      ]);
    },
    30000,
  );

  function countMessagesByRole(messages: IndexedMessage[], role: string): number {
    return messages.filter((m) => m.message.role === role).length;
  }

  class ResponseLatencyTransport {
    private inner: { request: <T = any>(req: any) => Promise<{ status: number; data: T }> };
    private readonly rules: Array<{
      method?: string;
      pathPrefix: string;
      delayMs: number;
    }>;

    constructor(
      inner: { request: <T = any>(req: any) => Promise<{ status: number; data: T }> },
      rules: Array<{ method?: string; pathPrefix: string; delayMs: number }>,
    ) {
      this.inner = inner;
      this.rules = rules;
    }

    async request<T = any>(req: {
      method: any;
      path: string;
      headers?: Record<string, string>;
      body?: any;
      timeoutMs?: number;
    }): Promise<{ status: number; data: T }> {
      const response = await this.inner.request<T>(req);
      const method = String(req.method).toUpperCase();
      const path = req.path.split('?')[0];
      const rule = this.rules.find((candidate) => {
        const matchesMethod =
          candidate.method == null || method === candidate.method.toUpperCase();
        return matchesMethod && path.startsWith(candidate.pathPrefix);
      });
      if (rule && rule.delayMs > 0) {
        await new Promise((resolve) => setTimeout(resolve, rule.delayMs));
      }
      return response;
    }
  }

  function assertMonotonicUniqueIndices(messages: IndexedMessage[]): void {
    for (let idx = 1; idx < messages.length; idx += 1) {
      expect(messages[idx].index).toBeGreaterThan(messages[idx - 1].index);
    }
  }

  async function seedSessionWithCompletedTurn(
    backend: RestAgentBackend,
    sessionId: string,
    content: string,
  ): Promise<void> {
    await backend.sendMessage(sessionId, {
      message: { role: 'user', content },
      configOverrides: {
        stream_chunk_count: 3,
        stream_chunk_delay_ms: 20,
      },
    });

    await waitForAsync(async () => {
      const listed = await backend.listMessages(sessionId);
      return listed.messages.some(
        (m) => m.message.role === 'user' && m.message.content === content,
      ) && listed.messages.some((m) => m.message.role === 'assistant') &&
        listed.activeRequestId == null;
    }, { timeoutMs: 10000, intervalMs: 100 });

    // The session-level active-send reservation is released just after the
    // request completes; give the background worker a brief moment to clear it
    // before the next seeded send starts.
    await new Promise((resolve) => setTimeout(resolve, 150));
  }

  async function createCacheSnapshot(
    backend: RestAgentBackend,
    sessionId: string,
  ): Promise<ReturnType<ChatController['getCacheSnapshot']>> {
    const controller = new ChatController({ backend, sessionId });
    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
    controller.ensureEventStreamingStarted({
      initialSinceId: controller.getSnapshot().eventsCursorId,
    });
    await new Promise((resolve) => setTimeout(resolve, 150));
    const cache = controller.getCacheSnapshot();
    controller.dispose();
    return cache;
  }

  async function rehydrateAndOpenController(options: {
    backend: RestAgentBackend;
    sessionId: string;
    cache: ReturnType<ChatController['getCacheSnapshot']>;
  }): Promise<ChatController> {
    const controller = new ChatController({
      backend: options.backend,
      sessionId: options.sessionId,
    });
    controller.hydrateFromCache(options.cache);
    await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
    controller.ensureEventStreamingStarted({
      initialSinceId: controller.getSnapshot().eventsCursorId,
    });
    return controller;
  }

  async function waitForCompletedTurn(options: {
    controller: ChatController;
    userContent: string;
    initialAssistantCount: number;
    timeoutMs?: number;
  }): Promise<void> {
    await waitFor(() => {
      const snapshot = options.controller.getSnapshot();
      return (
        snapshot.activeRequestId == null &&
        snapshot.messages.some(
          (m) => m.message.role === 'user' && m.message.content === options.userContent,
        ) &&
        countMessagesByRole(snapshot.messages, 'assistant') > options.initialAssistantCount
      );
    }, { timeoutMs: options.timeoutMs ?? 15000, intervalMs: 50 });
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

  async function seedPendingToolLoopSession(baseUrl: string, sessionId: string): Promise<void> {
    const transport = new FetchTransport({ baseUrl });
    await transport.request({
      method: 'POST',
      path: `/__test/sessions/${encodeURIComponent(sessionId)}/inject_pending_tool_call`,
      body: {
        assistant_content: 'Running tools.',
        tool_name: 'add',
        arguments: { a: 2, b: 3 },
      },
    });
  }

  it('Q: production REST adapter retrieves projected sessions and messages without changing complete loads', async () => {
    await ensureServer();
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl }),
    });
    const sessionId = await createSession(backend);
    await backend.appendMessage(sessionId, {
      role: 'user',
      content: 'Crystal Lattice projected query',
      metadata: { private: 'omit-me' },
    });

    const projectedSessions = await backend.querySessions({
      include: ['$.sessions[*].session_id'],
    });
    expect(projectedSessions).toEqual({
      sessions: [{ session_id: sessionId }],
    });

    const projectedMessages = await backend.queryMessages(sessionId, {
      include: [
        '$.messages[*].index',
        '$.messages[*].message.role',
        '$.messages[*].message.content',
      ],
    });
    expect(projectedMessages).toEqual({
      messages: [
        {
          index: 0,
          message: {
            role: 'system',
            content: 'You are a helpful system template.',
          },
        },
        {
          index: 1,
          message: {
            role: 'user',
            content: 'Crystal Lattice projected query',
          },
        },
      ],
    });

    const complete = await backend.listMessages(sessionId);
    expect(complete.messages[1]).toMatchObject({
      index: 1,
      message: {
        role: 'user',
        content: 'Crystal Lattice projected query',
        metadata: { private: 'omit-me' },
      },
    });
  }, 30000);

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

  it('F: append message with multipartContent roundtrips', async () => {
    await ensureServer();

    const transport = new FetchTransport({ baseUrl });
    const backend = new RestAgentBackend({ transport });
    const sessionId = await createSession(backend);

    const multipart = [
      {
        type: 'image',
        content: {
          url: 'data:image/png;base64,AAAA',
          mime_type: 'image/png',
          filename: 'test.png',
        },
        metadata: { source: 'sdk-test' },
      },
    ];

    await backend.appendMessage(sessionId, {
      role: 'user',
      content: '',
      multipartContent: multipart,
    });

    const listed = await backend.listMessages(sessionId);
    expect(listed.messages.length).toBeGreaterThanOrEqual(1);

    const last = listed.messages[listed.messages.length - 1].message;
    expect(last.role).toBe('user');
    expect(last.content).toBe('');
    expect((last as any).multipartContent).toEqual(multipart);
  }, 30000);

  it('F2: stored attachment previews are available in frontend-visible user messages', async () => {
    const started = await startBackendServer({
      config: {
        providers: {
          reference_openai: {
            provider: 'reference_openai_compatible',
            model: 'test-model',
            timeout: 60,
          },
        },
        plugins: [
          'path:${env:REPO_ROOT}/plugins/reference-openai-compatible-provider',
        ],
        agents: {
          default: {
            provider: 'reference_openai',
          },
        },
      },
    });

    try {
      const transport = new FetchTransport({ baseUrl: started.baseUrl });
      const backend = new RestAgentBackend({ transport });
      const created = await backend.createSession({ agentId: 'default' });
      const sessionId = created.session.session_id;

      const asset = await storeSessionAttachment({
        backend,
        sessionId,
        attachmentType: 'image',
        filename: 'red.png',
        mimeType: 'image/png',
        dataBase64: 'QUJDRA==',
        pluginId: 'reference_openai_compatible_attachments',
      });

      await backend.appendMessage(sessionId, {
        role: 'user',
        content: 'show preview',
        multipartContent: [
          {
            type: 'image',
            content: {
              asset_ref: asset.asset_ref,
              filename: asset.filename,
              mime_type: asset.mime_type,
              preview_data_base64: 'QUJDRA==',
              preview_mime_type: 'image/png',
            },
            metadata: {},
          },
        ],
      });

      const listed = await backend.listMessages(sessionId);
      const userWithAttachment = listed.messages.find(
        (message) =>
          message.message.role === 'user' &&
          message.message.content === 'show preview' &&
          Array.isArray((message.message as any).multipartContent),
      );

      expect(userWithAttachment).toBeDefined();
      const imageContent = (userWithAttachment?.message as any)?.multipartContent?.[0]?.content ?? {};
      expect(
        imageContent.url ?? `data:${imageContent.preview_mime_type};base64,${imageContent.preview_data_base64 ?? ''}`,
      ).toBe('data:image/png;base64,QUJDRA==');
    } finally {
      await started.stop();
    }
  }, 30000);

  it('G: FetchTransport times out cleanly against a delayed backend response', async () => {
    await ensureServer();

    const transport = new FetchTransport({
      baseUrl,
      defaultRequestTimeoutMs: 20,
    });

    await expect(
      transport.request({ method: 'GET', path: '/__test/sleep?ms=200' }),
    ).rejects.toThrow(/timeout/i);
  }, 30000);

  it('H: recoverAfterResume reloads the active window and reconciles a stale request id', async () => {
    const { controller } = await bootstrapController({});

    controller.clearRequestState();
    await controller.sendMessage({
      message: { role: 'user', content: 'resume me' },
      configOverrides: {
        stream_chunk_count: 6,
        stream_chunk_delay_ms: 120,
      },
    });

    const startedRequestId = controller.getSnapshot().activeRequestId;
    expect(startedRequestId).toBeTruthy();

    controller.stopEventStreaming();

    await new Promise((resolve) => setTimeout(resolve, 1200));

    expect(controller.getSnapshot().activeRequestId).toBe(startedRequestId);

    await controller.recoverAfterResume();

    const snapshot = controller.getSnapshot();
    expect(snapshot.activeRequestId).toBeNull();
    expect(snapshot.messages.some((m) => m.message.role === 'assistant')).toBe(true);
  }, 30000);

  it('I: reopened persisted sessions after backend restart keep the next user send visible before assistant final', async () => {
    const startedA = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
    });
    let startedB: Awaited<ReturnType<typeof startBackendServer>> | null = null;

    try {
      const backendA = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: startedA.baseUrl }),
      });
      const sessionId = await createSession(backendA);

      await backendA.sendMessage(sessionId, {
        message: { role: 'user', content: 'history before restart' },
        configOverrides: {
          stream_chunk_count: 2,
          stream_chunk_delay_ms: 20,
        },
      });

      await waitForAsync(async () => {
        const listed = await backendA.listMessages(sessionId);
        return listed.messages.some((m) => m.message.role === 'assistant');
      }, { timeoutMs: 10000, intervalMs: 100 });

      await startedA.stop();

      startedB = await startBackendServer({
        config: serverConfig,
        configPath: startedA.configPath,
        sessionsRoot: startedA.sessionsRoot,
        enableTestControl: true,
      });

      const eventBatches: Array<Array<{ type?: string }>> = [];
      const baseTransportB = new FetchTransport({ baseUrl: startedB.baseUrl });
      const observingTransport = {
        async request<T = any>(req: {
          method: any;
          path: string;
          headers?: Record<string, string>;
          body?: any;
          timeoutMs?: number;
        }): Promise<{ status: number; data: T }> {
          const resp = await baseTransportB.request<T>(req);
          if (
            String(req.method).toUpperCase() === 'GET' &&
            req.path.startsWith('/events') &&
            Array.isArray((resp.data as any)?.events) &&
            (resp.data as any).events.length > 0
          ) {
            eventBatches.push((resp.data as any).events);
          }
          return resp;
        },
      };
      const backendB = new RestAgentBackend({
        transport: observingTransport,
      });
      const controller = new ChatController({ backend: backendB, sessionId });

      await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });

      const reopened = controller.getSnapshot();
      expect(reopened.messages.some((m) => m.message.content === 'history before restart')).toBe(true);
      expect(reopened.eventsCursorId).toBeNull();

      controller.startEventStreaming({ initialSinceId: reopened.eventsCursorId });
      await new Promise((resolve) => setTimeout(resolve, 150));

      await controller.sendMessage({
        message: { role: 'user', content: 'after restart' },
        configOverrides: {
          stream_chunk_count: 6,
          stream_chunk_delay_ms: 80,
        },
      });

      await waitForAsync(async () => {
        const listed = await backendB.listMessages(sessionId);
        return listed.messages.some((m) => m.message.role === 'assistant');
      }, { timeoutMs: 15000, intervalMs: 100 });

      const replayEvents = await backendB.listEvents({ sessionId, sinceId: '0' });
      expect(replayEvents.events.length).toBeGreaterThan(0);

      await waitFor(() => {
        const snapshot = controller.getSnapshot();
        return (
          snapshot.activeRequestId == null &&
          snapshot.messages.some((m) => m.message.role === 'assistant') &&
          snapshot.messages.some((m) => m.message.role === 'user' && m.message.content === 'after restart')
        );
      }, { timeoutMs: 15000, intervalMs: 50 });

      const observedEventTypes = eventBatches.flat().map((event) => event.type).filter(Boolean);
      expect(observedEventTypes).toContain('message_appended');
    } finally {
      if (startedB) {
        await startedB.stop();
      }
      await startedA.stop();
    }
  }, 30000);

  it('J: polling continues across backend restart while the same controller remains open', async () => {
    const startedA = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
    });
    let startedB: Awaited<ReturnType<typeof startBackendServer>> | null = null;

    try {
      const eventBatches: Array<Array<{ type?: string }>> = [];
      const baseTransport = new FetchTransport({
        baseUrl: startedA.baseUrl,
        defaultRequestTimeoutMs: 1000,
        timeoutRules: [
          {
            method: 'GET',
            pathPrefix: '/events',
            timeoutMs: 1000,
          },
        ],
      });
      const transport = {
        async request<T = any>(req: {
          method: any;
          path: string;
          headers?: Record<string, string>;
          body?: any;
          timeoutMs?: number;
        }): Promise<{ status: number; data: T }> {
          const resp = await baseTransport.request<T>(req);
          if (
            String(req.method).toUpperCase() === 'GET' &&
            req.path.startsWith('/events') &&
            Array.isArray((resp.data as any)?.events) &&
            (resp.data as any).events.length > 0
          ) {
            eventBatches.push((resp.data as any).events);
          }
          return resp;
        },
      };
      const backend = new RestAgentBackend({ transport });
      const sessionId = await createSession(backend);

      await seedSessionWithCompletedTurn(backend, sessionId, 'before live restart');

      const controller = new ChatController({ backend, sessionId });
      await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
      controller.startEventStreaming({ initialSinceId: controller.getSnapshot().eventsCursorId });
      await new Promise((resolve) => setTimeout(resolve, 150));

      const assistantCountBefore = countMessagesByRole(
        controller.getSnapshot().messages,
        'assistant',
      );

      await startedA.stop();
      await new Promise((resolve) => setTimeout(resolve, 2200));

      startedB = await startBackendServer({
        config: serverConfig,
        configPath: startedA.configPath,
        sessionsRoot: startedA.sessionsRoot,
        port: startedA.port,
        enableTestControl: true,
      });

      await controller.sendMessage({
        message: { role: 'user', content: 'after live restart' },
        configOverrides: {
          stream_chunk_count: 6,
          stream_chunk_delay_ms: 80,
        },
      });

      await waitForAsync(async () => {
        const listed = await backend.listMessages(sessionId);
        return listed.messages.some(
          (m) => m.message.role === 'user' && m.message.content === 'after live restart',
        ) && countMessagesByRole(listed.messages, 'assistant') > assistantCountBefore;
      }, { timeoutMs: 15000, intervalMs: 100 });

      await waitFor(() => eventBatches.length > 0, {
        timeoutMs: 15000,
        intervalMs: 50,
      });

      const observedEventTypes = eventBatches.flat().map((event) => event.type).filter(Boolean);
      expect(observedEventTypes).toContain('message_appended');

      await waitForCompletedTurn({
        controller,
        userContent: 'after live restart',
        initialAssistantCount: assistantCountBefore,
        timeoutMs: 20000,
      });
    } finally {
      if (startedB) {
        await startedB.stop();
      }
      await startedA.stop();
    }
  }, 40000);

  it('K1: rehydrated cached session without restart can send and stream immediately', async () => {
    await ensureServer();

    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl }),
    });
    const sessionId = await createSession(backend);

    await seedSessionWithCompletedTurn(backend, sessionId, 'cache seed without restart');

    const cache = await createCacheSnapshot(backend, sessionId);
    const controller = await rehydrateAndOpenController({ backend, sessionId, cache });

    expect(controller.getSnapshot().messages.length).toBeGreaterThan(0);

    const assistantCountBefore = countMessagesByRole(
      controller.getSnapshot().messages,
      'assistant',
    );

    await controller.sendMessage({
      message: { role: 'user', content: 'rehydrated without restart' },
      configOverrides: {
        stream_chunk_count: 6,
        stream_chunk_delay_ms: 80,
      },
    });

    await waitForCompletedTurn({
      controller,
      userContent: 'rehydrated without restart',
      initialAssistantCount: assistantCountBefore,
    });
  }, 30000);

  it('K2: rehydrated cached session after backend restart can send and stream immediately', async () => {
    const startedA = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
    });
    let startedB: Awaited<ReturnType<typeof startBackendServer>> | null = null;

    try {
      const backendA = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: startedA.baseUrl }),
      });
      const sessionId = await createSession(backendA);

      await seedSessionWithCompletedTurn(backendA, sessionId, 'cache seed before restart');
      const cache = await createCacheSnapshot(backendA, sessionId);

      await startedA.stop();

      startedB = await startBackendServer({
        config: serverConfig,
        configPath: startedA.configPath,
        sessionsRoot: startedA.sessionsRoot,
        enableTestControl: true,
      });

      const backendB = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: startedB.baseUrl }),
      });
      const controller = await rehydrateAndOpenController({ backend: backendB, sessionId, cache });

      const assistantCountBefore = countMessagesByRole(
        controller.getSnapshot().messages,
        'assistant',
      );

      await controller.sendMessage({
        message: { role: 'user', content: 'rehydrated after restart' },
        configOverrides: {
          stream_chunk_count: 6,
          stream_chunk_delay_ms: 80,
        },
      });

      await waitForCompletedTurn({
        controller,
        userContent: 'rehydrated after restart',
        initialAssistantCount: assistantCountBefore,
      });
    } finally {
      if (startedB) {
        await startedB.stop();
      }
      await startedA.stop();
    }
  }, 40000);

  it('K3: empty cached session without restart still reloads and can send immediately', async () => {
    await ensureServer();

    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl }),
    });
    const sessionId = await createSession(backend);

    const cache = {
      messages: [],
      eventsCursorId: null,
      activeRequestId: null,
      updatedAtMs: null,
    };

    const controller = await rehydrateAndOpenController({ backend, sessionId, cache });
    expect(controller.getSnapshot().messages).toEqual([]);

    const assistantCountBefore = countMessagesByRole(
      controller.getSnapshot().messages,
      'assistant',
    );

    await controller.sendMessage({
      message: { role: 'user', content: 'empty cache without restart' },
      configOverrides: {
        stream_chunk_count: 6,
        stream_chunk_delay_ms: 80,
      },
    });

    await waitForCompletedTurn({
      controller,
      userContent: 'empty cache without restart',
      initialAssistantCount: assistantCountBefore,
    });
  }, 30000);

  it('K4: empty cached session after backend restart still reloads and can send immediately', async () => {
    const startedA = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
    });
    let startedB: Awaited<ReturnType<typeof startBackendServer>> | null = null;

    try {
      const backendA = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: startedA.baseUrl }),
      });
      const sessionId = await createSession(backendA);

      const cache = {
        messages: [],
        eventsCursorId: null,
        activeRequestId: null,
        updatedAtMs: null,
      };

      await startedA.stop();

      startedB = await startBackendServer({
        config: serverConfig,
        configPath: startedA.configPath,
        sessionsRoot: startedA.sessionsRoot,
        enableTestControl: true,
      });

      const backendB = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: startedB.baseUrl }),
      });
      const controller = await rehydrateAndOpenController({ backend: backendB, sessionId, cache });

      const assistantCountBefore = countMessagesByRole(
        controller.getSnapshot().messages,
        'assistant',
      );

      await controller.sendMessage({
        message: { role: 'user', content: 'empty cache after restart' },
        configOverrides: {
          stream_chunk_count: 6,
          stream_chunk_delay_ms: 80,
        },
      });

      await waitForCompletedTurn({
        controller,
        userContent: 'empty cache after restart',
        initialAssistantCount: assistantCountBefore,
      });
    } finally {
      if (startedB) {
        await startedB.stop();
      }
      await startedA.stop();
    }
  }, 40000);

  it('L: expired event cursors trigger automatic controller reload recovery', async () => {
    const started = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
      eventStoreOptions: {
        maxEventsGlobal: 8,
      },
    });

    try {
      const backend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: started.baseUrl }),
      });
      const sessionId = await createSession(backend);

      await seedSessionWithCompletedTurn(backend, sessionId, 'seed before expiry');

      const cached = await createCacheSnapshot(backend, sessionId);
      expect(cached.eventsCursorId).toBeTruthy();

      await seedSessionWithCompletedTurn(backend, sessionId, 'after expiry one');
      await seedSessionWithCompletedTurn(backend, sessionId, 'after expiry two');
      await seedSessionWithCompletedTurn(backend, sessionId, 'after expiry three');

      const expiredProbe = await backend.listEvents({
        sessionId,
        sinceId: cached.eventsCursorId ?? undefined,
      });
      expect(expiredProbe.cursorExpired).toBe(true);

      const controller = new ChatController({
        backend,
        sessionId,
        initialMessages: cached.messages,
        initialEventsCursorId: cached.eventsCursorId,
        initialActiveRequestId: cached.activeRequestId,
      });

      controller.startEventStreaming({ initialSinceId: cached.eventsCursorId });

      await waitFor(() => {
        const snapshot = controller.getSnapshot();
        return (
          snapshot.loading === false &&
          snapshot.dirty === false &&
          snapshot.eventsStatus === 'running' &&
          snapshot.messages.some(
            (m) => m.message.role === 'user' && m.message.content === 'after expiry three',
          ) &&
          countMessagesByRole(snapshot.messages, 'assistant') >= 4
        );
      }, { timeoutMs: 15000, intervalMs: 50 });

      controller.dispose();
    } finally {
      await started.stop();
    }
  }, 30000);

  it('M: expired snapshot cursor does not trigger a /messages reload loop', async () => {
    const started = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
      eventStoreOptions: {
        maxEventsGlobal: 8,
      },
    });

    try {
      const setupBackend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: started.baseUrl }),
      });
      const sessionId = await createSession(setupBackend);

      await seedSessionWithCompletedTurn(setupBackend, sessionId, 'stale cursor target');
      const cached = await createCacheSnapshot(setupBackend, sessionId);
      expect(cached.eventsCursorId).toBeTruthy();

      for (let idx = 0; idx < 4; idx += 1) {
        const noisySessionId = await createSession(setupBackend);
        await seedSessionWithCompletedTurn(setupBackend, noisySessionId, `noise ${idx}`);
      }

      const expiredProbe = await setupBackend.listEvents({
        sessionId,
        sinceId: cached.eventsCursorId ?? undefined,
      });
      expect(expiredProbe.cursorExpired).toBe(true);

      const tracking = new TrackingTransport(
        new FetchTransport({ baseUrl: started.baseUrl }),
      );
      const backend = new RestAgentBackend({ transport: tracking });
      const controller = new ChatController({
        backend,
        sessionId,
        initialMessages: cached.messages,
        initialEventsCursorId: cached.eventsCursorId,
        initialActiveRequestId: cached.activeRequestId,
      });

      const listPath = `/sessions/${encodeURIComponent(sessionId)}/messages`;
      await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
      controller.ensureEventStreamingStarted({
        initialSinceId: controller.getSnapshot().eventsCursorId,
      });

      await waitFor(() => {
        const snapshot = controller.getSnapshot();
        return (
          snapshot.loading === false &&
          snapshot.eventsStatus === 'running' &&
          snapshot.eventsCursorId == null &&
          snapshot.listCursorEventId == null
        );
      }, { timeoutMs: 5000, intervalMs: 50 });

      await new Promise((resolve) => setTimeout(resolve, 2200));

      expect(tracking.getCount({ method: 'GET', pathPrefix: listPath })).toBe(1);
      expect(
        controller.getSnapshot().messages.some(
          (m) => m.message.role === 'user' && m.message.content === 'stale cursor target',
        ),
      ).toBe(true);
      controller.dispose();
    } finally {
      await started.stop();
    }
  }, 30000);

  it('N: reload and polling timing matrix stays clean during delayed persistence', async () => {
    const started = await startBackendServer({
      config: serverConfig,
      enableTestControl: true,
      sessionSaveDelayMs: 150,
    });

    try {
      const controlBackend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: started.baseUrl }),
      });
      const sessionId = await createSession(controlBackend);
      await seedSessionWithCompletedTurn(controlBackend, sessionId, 'matrix seed');

      await controlBackend.sendMessage(sessionId, {
        message: { role: 'user', content: 'matrix live request' },
        configOverrides: {
          stream_chunk_count: 6,
          stream_chunk_delay_ms: 80,
        },
      });

      const profiles = [
        { name: 'baseline', messageDelayMs: 0, eventDelayMs: 0, offsetMs: 0 },
        { name: 'messages_50', messageDelayMs: 50, eventDelayMs: 0, offsetMs: 50 },
        { name: 'events_50', messageDelayMs: 0, eventDelayMs: 50, offsetMs: 100 },
        { name: 'both_50', messageDelayMs: 50, eventDelayMs: 50, offsetMs: 150 },
      ];

      const controllerEntries = await Promise.all(
        profiles.map(async (profile) => {
          const transport = new ResponseLatencyTransport(
            new FetchTransport({ baseUrl: started.baseUrl }),
            [
              {
                method: 'GET',
                pathPrefix: `/sessions/${encodeURIComponent(sessionId)}/messages`,
                delayMs: profile.messageDelayMs,
              },
              {
                method: 'GET',
                pathPrefix: '/events',
                delayMs: profile.eventDelayMs,
              },
            ],
          );
          const backend = new RestAgentBackend({ transport });
          const controller = new ChatController({ backend, sessionId });
          const seen = {
            dirty: false,
            loadingTransitions: 0,
          };
          controller.subscribe(() => {
            const snapshot = controller.getSnapshot();
            if (snapshot.dirty) {
              seen.dirty = true;
            }
            if (snapshot.loading) {
              seen.loadingTransitions += 1;
            }
          });
          await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
          controller.ensureEventStreamingStarted({
            initialSinceId: controller.getSnapshot().eventsCursorId,
          });
          return { profile, controller, seen };
        }),
      );

      await Promise.all(
        controllerEntries.map(async ({ controller, profile }) => {
          await new Promise((resolve) => setTimeout(resolve, profile.offsetMs));
          for (let idx = 0; idx < 4; idx += 1) {
            await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
            controller.ensureEventStreamingStarted({
              initialSinceId: controller.getSnapshot().eventsCursorId,
            });
            await new Promise((resolve) => setTimeout(resolve, 50));
          }
        }),
      );

      await Promise.all(
        controllerEntries.map(async ({ controller, seen, profile }) => {
          await waitFor(() => {
            const snapshot = controller.getSnapshot();
            return (
              snapshot.loading === false &&
              snapshot.dirty === false &&
              snapshot.activeRequestId == null &&
              snapshot.messages.some(
                (m) => m.message.role === 'user' && m.message.content === 'matrix live request',
              ) &&
              countMessagesByRole(snapshot.messages, 'assistant') >= 2
            );
          }, { timeoutMs: 20000, intervalMs: 50 });

          const snapshot = controller.getSnapshot();
          expect(seen.dirty, `${profile.name} should not observe dirty history`).toBe(false);
          expect(snapshot.loading, `${profile.name} should not stay loading`).toBe(false);
          assertMonotonicUniqueIndices(snapshot.messages);
        }),
      );

      controllerEntries.forEach(({ controller }) => controller.dispose());
    } finally {
      await started.stop();
    }
  }, 40000);

  it('O: tool-loop reopen matrix stays aligned across delayed checkpoint publication', async () => {
    const started = await startBackendServer({
      config: toolLoopServerConfig,
      enableTestControl: true,
      checkpointDelayMs: 150,
    });

    try {
      const setupBackend = new RestAgentBackend({
        transport: new FetchTransport({ baseUrl: started.baseUrl }),
      });
      const sessionId = await createSession(setupBackend);
      await seedPendingToolLoopSession(started.baseUrl, sessionId);

      await setupBackend.send(sessionId, {});

      const profiles = [
        { name: 'baseline', messageDelayMs: 0, eventDelayMs: 0, offsetMs: 0 },
        { name: 'messages_50', messageDelayMs: 50, eventDelayMs: 0, offsetMs: 50 },
        { name: 'events_50', messageDelayMs: 0, eventDelayMs: 50, offsetMs: 100 },
        { name: 'both_50', messageDelayMs: 50, eventDelayMs: 50, offsetMs: 150 },
      ];

      const controllerEntries = await Promise.all(
        profiles.map(async (profile) => {
          const transport = new ResponseLatencyTransport(
            new FetchTransport({ baseUrl: started.baseUrl }),
            [
              {
                method: 'GET',
                pathPrefix: `/sessions/${encodeURIComponent(sessionId)}/messages`,
                delayMs: profile.messageDelayMs,
              },
              {
                method: 'GET',
                pathPrefix: '/events',
                delayMs: profile.eventDelayMs,
              },
            ],
          );
          const backend = new RestAgentBackend({ transport });
          const controller = new ChatController({ backend, sessionId });
          const seen = {
            dirty: false,
          };
          controller.subscribe(() => {
            if (controller.getSnapshot().dirty) {
              seen.dirty = true;
            }
          });
          return { profile, controller, seen };
        }),
      );

      await Promise.all(
        controllerEntries.map(async ({ controller, profile }) => {
          await new Promise((resolve) => setTimeout(resolve, profile.offsetMs));
          for (let idx = 0; idx < 4; idx += 1) {
            await controller.loadMessagesFromRangeText({ startText: '-50', endText: '' });
            controller.ensureEventStreamingStarted({
              initialSinceId: controller.getSnapshot().eventsCursorId,
            });
            await new Promise((resolve) => setTimeout(resolve, 75));
          }
        }),
      );

      await Promise.all(
        controllerEntries.map(async ({ controller, seen, profile }) => {
          await waitFor(() => {
            const snapshot = controller.getSnapshot();
            return (
              snapshot.loading === false &&
              snapshot.activeRequestId == null &&
              snapshot.messages.some((m) => m.message.role === 'tool') &&
              snapshot.messages.some((m) => m.message.role === 'assistant')
            );
          }, { timeoutMs: 15000, intervalMs: 50 });

          const snapshot = controller.getSnapshot();
          expect(seen.dirty, `${profile.name} should not observe dirty history`).toBe(false);
          expect(snapshot.dirty, `${profile.name} should settle cleanly`).toBe(false);
          assertMonotonicUniqueIndices(snapshot.messages);
        }),
      );

      controllerEntries.forEach(({ controller }) => controller.dispose());
    } finally {
      await started.stop();
    }
  }, 30000);
});
