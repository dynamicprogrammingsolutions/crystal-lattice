import { expect, it, vi } from 'vitest';

import {
  CloudTransport,
  formatCloudConnectionLink,
  parseCloudConnectionLink,
} from './cloudTransport';

it('round-trips cloud connection links', () => {
  const raw = formatCloudConnectionLink({
    orchestratorUrl: 'https://cloud.example.test',
    instanceId: 'inst_1',
    sessionId: 's1',
    token: 'tok_1',
  });

  expect(parseCloudConnectionLink(raw)).toEqual({
    orchestratorUrl: 'https://cloud.example.test',
    instanceId: 'inst_1',
    sessionId: 's1',
    token: 'tok_1',
  });
});

it('proxies requests through the orchestrator with bearer auth', async () => {
  const fetchImpl = vi.fn(async (_url: string, _init?: RequestInit) => {
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  });
  const transport = new CloudTransport({
    orchestratorUrl: 'https://cloud.example.test/',
    instanceId: 'inst_1',
    token: 'tok_1',
    fetchImpl: fetchImpl as unknown as typeof fetch,
  });

  const result = await transport.request({ method: 'POST', path: '/sessions/s1/messages', body: { text: 'hi' } });

  expect(result).toEqual({ status: 200, data: { ok: true } });
  expect(fetchImpl).toHaveBeenCalledTimes(1);
  const [url, init] = fetchImpl.mock.calls[0];
  expect(url).toBe('https://cloud.example.test/instances/inst_1/proxy/sessions/s1/messages');
  expect((init as RequestInit).method).toBe('POST');
  expect(((init as RequestInit).headers as Record<string, string>).authorization).toBe('Bearer tok_1');
});