import { describe, expect, it } from 'vitest';

import type { WebSocketLike } from './bridgeTransport';
import { BridgeTransport } from './bridgeTransport';

class FakeWebSocket implements WebSocketLike {
  readonly readyState = 1;
  onopen: ((ev?: any) => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: ((ev: any) => void) | null = null;
  onclose: ((ev: { code?: number; reason?: string; wasClean?: boolean }) => void) | null = null;

  sent: any[] = [];

  constructor() {
    setTimeout(() => this.onopen?.(), 0);
  }

  send(data: string): void {
    const msg = JSON.parse(data);
    this.sent.push(msg);

    // Minimal Phoenix replies.
    const reply = (response: any) => {
      const out = {
        topic: msg.topic,
        event: 'phx_reply',
        ref: msg.ref,
        payload: { status: 'ok', response },
      };
      this.onmessage?.({ data: JSON.stringify(out) });
    };

    if (msg.event === 'phx_join') {
      reply({});
      return;
    }

    if (msg.event === 'http_request') {
      const requestId = msg.payload.request_id;
      const body = JSON.stringify({ ok: true, echo: msg.payload.body ? JSON.parse(msg.payload.body) : null });
      reply({ request_id: requestId, status: 200, headers: { 'content-type': 'application/json' }, body });
      return;
    }

    if (msg.event === 'http_request_init' || msg.event === 'http_request_chunk') {
      reply({ status: 'accepted' });
      return;
    }

    if (msg.event === 'http_request_end') {
      const requestId = msg.payload.request_id;
      const responseObj = { ok: true, big: 'x'.repeat(600_000) };
      const responseBody = JSON.stringify(responseObj);

      // Push chunked response.
      const chunkSize = 32_000;
      const chunks: string[] = [];
      for (let i = 0; i < responseBody.length; i += chunkSize) {
        chunks.push(responseBody.slice(i, i + chunkSize));
      }

      const push = (event: string, payload: any) => {
        this.onmessage?.({
          data: JSON.stringify({ topic: msg.topic, event, payload, ref: null }),
        });
      };

      push('http_response_init', {
        request_id: requestId,
        status: 200,
        headers: { 'content-type': 'application/json' },
        body_length_bytes: responseBody.length,
        chunk_size_bytes: chunkSize,
      });

      chunks.forEach((chunk, idx) => {
        push('http_response_chunk', { request_id: requestId, seq: idx, chunk });
      });

      push('http_response_end', { request_id: requestId, final_seq: chunks.length - 1 });

      reply({ type: 'http_response_chunked', request_id: requestId });
    }
  }

  close(): void {
    this.onclose?.({ code: 1000, wasClean: true });
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
