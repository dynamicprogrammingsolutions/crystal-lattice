import { expect, it, vi } from 'vitest';

import type { WebSocketLike } from './bridgeTransport';
import { BridgeTransport } from './bridgeTransport';

async function flushFakeTimers(): Promise<void> {
  await vi.advanceTimersByTimeAsync(0);
}

class FakeWebSocket implements WebSocketLike {
  onopen: ((ev?: any) => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: ((ev: any) => void) | null = null;
  onclose: ((ev: { code?: number; reason?: string; wasClean?: boolean }) => void) | null = null;

  sent: any[] = [];
  respondToHeartbeat = true;
  replyToHttpRequest = true;
  closeOnHttpRequestMs: number | null = null;
  resumeSessionId = 'sess-1';

  private state = 1;

  constructor(options: Partial<Pick<FakeWebSocket, 'respondToHeartbeat' | 'replyToHttpRequest' | 'closeOnHttpRequestMs' | 'resumeSessionId'>> = {}) {
    Object.assign(this, options);
    setTimeout(() => this.onopen?.(), 0);
  }

  get readyState(): number {
    return this.state;
  }

  send(data: string): void {
    const msg = JSON.parse(data);
    this.sent.push(msg);

    if (msg.event === 'phx_join') {
      this.reply(msg, {});
      return;
    }

    if (msg.event === 'resume_session') {
      this.reply(msg, { session_id: this.resumeSessionId });
      return;
    }

    if (msg.event === 'heartbeat') {
      if (this.respondToHeartbeat) {
        this.reply(msg, {});
      }
      return;
    }

    if (msg.event === 'http_request') {
      if (typeof this.closeOnHttpRequestMs === 'number') {
        setTimeout(() => this.close(1006, 'simulated close'), this.closeOnHttpRequestMs);
        return;
      }
      if (!this.replyToHttpRequest) {
        return;
      }
      const requestId = msg.payload.request_id;
      const body = JSON.stringify({ ok: true, echo: msg.payload.body ? JSON.parse(msg.payload.body) : null });
      this.reply(msg, {
        request_id: requestId,
        status: 200,
        headers: { 'content-type': 'application/json' },
        body,
      });
      return;
    }

    if (msg.event === 'http_request_init' || msg.event === 'http_request_chunk') {
      this.reply(msg, { status: 'accepted' });
      return;
    }

    if (msg.event === 'http_request_end') {
      const requestId = msg.payload.request_id;
      const responseObj = { ok: true, big: 'x'.repeat(600_000) };
      const responseBody = JSON.stringify(responseObj);
      const chunkSize = 32_000;
      const chunks: string[] = [];
      for (let i = 0; i < responseBody.length; i += chunkSize) {
        chunks.push(responseBody.slice(i, i + chunkSize));
      }

      this.push('http_response_init', {
        request_id: requestId,
        status: 200,
        headers: { 'content-type': 'application/json' },
        body_length_bytes: responseBody.length,
        chunk_size_bytes: chunkSize,
      });

      chunks.forEach((chunk, idx) => {
        this.push('http_response_chunk', { request_id: requestId, seq: idx, chunk });
      });

      this.push('http_response_end', { request_id: requestId, final_seq: chunks.length - 1 });
      this.reply(msg, { type: 'http_response_chunked', request_id: requestId });
      return;
    }

    this.reply(msg, { status: 'accepted' });
  }

  close(code?: number, reason?: string): void {
    if (this.state === 3) {
      return;
    }
    this.state = 3;
    this.onclose?.({ code: code ?? 1000, reason, wasClean: (code ?? 1000) === 1000 });
  }

  private reply(msg: any, response: any): void {
    this.onmessage?.({
      data: JSON.stringify({
        topic: msg.topic,
        event: 'phx_reply',
        ref: msg.ref,
        payload: { status: 'ok', response },
      }),
    });
  }

  private push(event: string, payload: any): void {
    this.onmessage?.({
      data: JSON.stringify({ topic: 'server', event, payload, ref: null }),
    });
  }
}

class FakeWebSocketResumeError extends FakeWebSocket {
  override send(data: string): void {
    const msg = JSON.parse(data);
    this.sent.push(msg);

    if (msg.event === 'phx_join') {
      (this as any).reply(msg, {});
      return;
    }

    if (msg.event === 'resume_session') {
      this.onmessage?.({
        data: JSON.stringify({
          topic: msg.topic,
          event: 'phx_reply',
          ref: msg.ref,
          payload: { status: 'error', response: { reason: 'invalid_pairing_token' } },
        }),
      });
      return;
    }

    super.send(data);
  }
}

it('BridgeTransport uses legacy http_request for small payloads', async () => {
  const ws = new FakeWebSocket();
  const transport = new BridgeTransport({ bridgeUrl: 'ws://example.test/ws', wsFactory: () => ws });
  (transport as any).sessionId = 'sess-1';

  const result = await transport.request({
    method: 'POST',
    path: '/api/test',
    body: { hello: 'world' },
    timeoutMs: 5000,
  });

  expect(result.status).toBe(200);
  expect(result.data.ok).toBe(true);
  expect(result.data.echo).toEqual({ hello: 'world' });

  const events = ws.sent.map((m) => m.event);
  expect(events).toContain('http_request');
  expect(events).not.toContain('http_request_init');
});

it('BridgeTransport chunks large request bodies and reassembles a chunked response', async () => {
  const ws = new FakeWebSocket();
  const transport = new BridgeTransport({
    bridgeUrl: 'ws://example.test/ws',
    wsFactory: () => ws,
    chunkingThresholdBytes: 8_000,
    chunkSizeBytes: 4_000,
  });
  (transport as any).sessionId = 'sess-1';

  const bigBody = { big: 'a'.repeat(50_000) };
  const result = await transport.request({ method: 'PUT', path: '/api/data', body: bigBody, timeoutMs: 5000 });

  expect(result.status).toBe(200);
  expect(result.data.ok).toBe(true);
  expect(result.data.big.length).toBe(600_000);

  const events = ws.sent.map((m) => m.event);
  expect(events).toContain('http_request_init');
  expect(events).toContain('http_request_chunk');
  expect(events).toContain('http_request_end');
});

it('BridgeTransport does not emit unhandledRejection when an /events request times out', async () => {
  vi.useFakeTimers();

  const unhandled: any[] = [];
  const onUnhandled = (reason: any) => {
    unhandled.push(reason);
  };
  process.on('unhandledRejection', onUnhandled);

  try {
    const ws = new FakeWebSocket({ replyToHttpRequest: false });
    const transport = new BridgeTransport({ bridgeUrl: 'ws://example.test/ws', wsFactory: () => ws });
    (transport as any).sessionId = 'sess-1';

    const promise = transport.request({ method: 'GET', path: '/events', timeoutMs: 10 });
    const settled = promise.then(
      () => null,
      (err) => err,
    );
    await vi.advanceTimersByTimeAsync(20);
    const err = await settled;
    expect(err).toBeInstanceOf(Error);
    expect((err as Error).message).toMatch(/timeout/i);
    await vi.advanceTimersByTimeAsync(0);
  } finally {
    process.off('unhandledRejection', onUnhandled);
    vi.useRealTimers();
  }

  expect(unhandled).toEqual([]);
});

it('BridgeTransport rejects in-flight requests immediately when the WebSocket closes', async () => {
  vi.useFakeTimers();
  try {
    const ws = new FakeWebSocket({ closeOnHttpRequestMs: 1 });
    const transport = new BridgeTransport({ bridgeUrl: 'ws://example.test/ws', wsFactory: () => ws });
    (transport as any).sessionId = 'sess-1';

    const start = Date.now();
    const promise = transport.request({ method: 'GET', path: '/api/data', timeoutMs: 60_000 });
    const settled = promise.then(
      () => null,
      (err) => err,
    );
    await vi.advanceTimersByTimeAsync(10);
    const err = await settled;
    expect(err).toBeInstanceOf(Error);
    expect((err as Error).message).toMatch(/Connection closed|closed/i);
    expect(Date.now() - start).toBeLessThan(500);
  } finally {
    vi.useRealTimers();
  }
});

it('BridgeTransport sends heartbeats and keeps a healthy socket alive', async () => {
  vi.useFakeTimers();
  try {
    const ws = new FakeWebSocket();
    const transport = new BridgeTransport({
      bridgeUrl: 'ws://example.test/ws',
      wsFactory: () => ws,
      heartbeatIntervalMs: 10,
      heartbeatTimeoutMs: 5,
    });

    const connectPromise = transport.connect();
    await flushFakeTimers();
    await connectPromise;
    await vi.advanceTimersByTimeAsync(35);

    expect(ws.sent.some((msg) => msg.event === 'heartbeat')).toBe(true);
    expect((transport as any).ws).toBe(ws);
  } finally {
    vi.useRealTimers();
  }
});

it('BridgeTransport resets the socket after a missed heartbeat reply', async () => {
  vi.useFakeTimers();
  try {
    const ws = new FakeWebSocket({ respondToHeartbeat: false });
    const transport = new BridgeTransport({
      bridgeUrl: 'ws://example.test/ws',
      wsFactory: () => ws,
      heartbeatIntervalMs: 10,
      heartbeatTimeoutMs: 5,
    });
    (transport as any).sessionId = 'sess-1';

    const connectPromise = transport.connect();
    await flushFakeTimers();
    await connectPromise;
    await vi.advanceTimersByTimeAsync(20);

    expect((transport as any).ws).toBe(null);
    expect((transport as any).sessionId).toBe(null);
  } finally {
    vi.useRealTimers();
  }
});

it('BridgeTransport reconnects and resumes after a non-poll request timeout', async () => {
  const createdSockets: FakeWebSocket[] = [];
  const transport = new BridgeTransport({
    bridgeUrl: 'ws://example.test/ws',
    serverId: 'server-1',
    pairingToken: 'pairing-token',
    wsFactory: () => {
      const next =
        createdSockets.length === 0
          ? new FakeWebSocket({ replyToHttpRequest: false })
          : new FakeWebSocket({ resumeSessionId: 'sess-1' });
      createdSockets.push(next);
      return next;
    },
    heartbeatIntervalMs: 1_000,
    heartbeatTimeoutMs: 1_000,
  });

  const firstError = await transport.request({ method: 'GET', path: '/api/data', timeoutMs: 20 }).then(
    () => null,
    (err) => err,
  );
  expect((firstError as Error).message).toMatch(/timeout/i);
  expect((transport as any).ws).toBe(null);
  expect((transport as any).sessionId).toBe(null);

  const secondResult = await transport.request({ method: 'GET', path: '/api/data', timeoutMs: 100 });

  expect(secondResult.status).toBe(200);
  expect(secondResult.data.ok).toBe(true);
  expect(createdSockets[1].sent.some((msg) => msg.event === 'resume_session')).toBe(true);
});

it('BridgeTransport keeps the socket after an /events timeout when heartbeats remain healthy', async () => {
  vi.useFakeTimers();
  try {
    const ws = new FakeWebSocket({ replyToHttpRequest: false });
    const transport = new BridgeTransport({
      bridgeUrl: 'ws://example.test/ws',
      serverId: 'server-1',
      pairingToken: 'pairing-token',
      wsFactory: () => ws,
      heartbeatIntervalMs: 10,
      heartbeatTimeoutMs: 5,
    });

    const eventsPromise = transport.request({ method: 'GET', path: '/events', timeoutMs: 10 });
    await flushFakeTimers();
    const eventsError = eventsPromise.then(
      () => null,
      (err) => err,
    );
    await vi.advanceTimersByTimeAsync(20);

    const pollErr = (await eventsError) as Error;
    expect(pollErr.message).toMatch(/timeout/i);
    expect((transport as any).ws).toBe(ws);
    expect((transport as any).sessionId).toBe('sess-1');

    ws.replyToHttpRequest = true;
    const dataPromise = transport.request({ method: 'GET', path: '/api/data', timeoutMs: 20 });
    await flushFakeTimers();
    await vi.advanceTimersByTimeAsync(10);
    const dataResult = await dataPromise;

    expect(dataResult.status).toBe(200);
    expect(dataResult.data.ok).toBe(true);
  } finally {
    vi.useRealTimers();
  }
});

it('BridgeTransport surfaces Phoenix error reasons for resume_session failures', async () => {
  const ws = new FakeWebSocketResumeError();
  const transport = new BridgeTransport({
    bridgeUrl: 'ws://example.test/ws',
    serverId: 'server-1',
    pairingToken: 'bad-token',
    wsFactory: () => ws,
  });

  const err = await transport.connect().then(
    () => null,
    (error) => error,
  );
  expect(err).toBeInstanceOf(Error);
  expect((err as Error).message).toMatch(/invalid_pairing_token/);
  expect((err as Error).message).toMatch(/phase=resume_session/);
});