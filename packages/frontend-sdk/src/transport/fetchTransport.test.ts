import { afterEach, expect, it, vi } from 'vitest';

import { FetchTransport } from './fetchTransport';

afterEach(() => {
  vi.useRealTimers();
});

function createNeverResolvingFetch() {
  let aborted = false;
  const fetchImpl = vi.fn((_url: string, init?: RequestInit) => {
    return new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => {
        aborted = true;
        reject(new Error('aborted'));
      });
    });
  });

  return {
    fetchImpl: fetchImpl as unknown as typeof fetch,
    wasAborted: () => aborted,
  };
}

it('FetchTransport aborts a stalled request on timeout', async () => {
  vi.useFakeTimers();

  const pending = createNeverResolvingFetch();
  const transport = new FetchTransport({
    baseUrl: 'http://example.test',
    defaultRequestTimeoutMs: 50,
    fetchImpl: pending.fetchImpl,
  });

  const promise = transport.request({ method: 'GET', path: '/slow' });
  const settled = promise.then(
    () => null,
    (err) => err,
  );

  await vi.advanceTimersByTimeAsync(60);
  const err = await settled;

  expect(err).toBeInstanceOf(Error);
  expect((err as Error).message).toContain('Request timeout after 50ms');
  expect(pending.wasAborted()).toBe(true);
});

it('FetchTransport clears its timeout after a successful response', async () => {
  vi.useFakeTimers();

  let aborted = false;
  const fetchImpl = vi.fn((_url: string, init?: RequestInit) => {
    return new Promise<Response>((resolve, reject) => {
      init?.signal?.addEventListener('abort', () => {
        aborted = true;
        reject(new Error('aborted'));
      });
      setTimeout(() => {
        resolve(
          new Response(JSON.stringify({ ok: true }), {
            status: 200,
            headers: { 'content-type': 'application/json' },
          }),
        );
      }, 10);
    });
  });

  const transport = new FetchTransport({
    baseUrl: 'http://example.test',
    defaultRequestTimeoutMs: 50,
    fetchImpl: fetchImpl as unknown as typeof fetch,
  });

  const promise = transport.request<{ ok: boolean }>({ method: 'GET', path: '/fast' });
  await vi.advanceTimersByTimeAsync(10);
  const result = await promise;

  expect(result.data.ok).toBe(true);

  await vi.advanceTimersByTimeAsync(100);
  expect(aborted).toBe(false);
});

it('FetchTransport gives explicit request timeout precedence over transport rules', async () => {
  vi.useFakeTimers();

  const pending = createNeverResolvingFetch();
  const transport = new FetchTransport({
    baseUrl: 'http://example.test',
    defaultRequestTimeoutMs: 100,
    timeoutRules: [{ method: 'GET', pathPrefix: '/slow', timeoutMs: 80 }],
    fetchImpl: pending.fetchImpl,
  });

  const promise = transport.request({ method: 'GET', path: '/slow', timeoutMs: 15 });
  const settled = promise.then(
    () => null,
    (err) => err,
  );

  await vi.advanceTimersByTimeAsync(20);
  const err = await settled;

  expect((err as Error).message).toContain('Request timeout after 15ms');
});

it('FetchTransport matches timeout rules by method and regex before falling back to the default', async () => {
  vi.useFakeTimers();

  const pending = createNeverResolvingFetch();
  const transport = new FetchTransport({
    baseUrl: 'http://example.test',
    defaultRequestTimeoutMs: 100,
    timeoutRules: [
      {
        method: 'POST',
        pathRegex: /^\/sessions\/[^/]+\/messages(?:\?|$)/,
        timeoutMs: 25,
      },
    ],
    fetchImpl: pending.fetchImpl,
  });

  let postSettled = false;
  const postPromise = transport
    .request({ method: 'POST', path: '/sessions/s1/messages' })
    .finally(() => {
      postSettled = true;
    });
  const postError = postPromise.then(
    () => null,
    (err) => err,
  );

  await vi.advanceTimersByTimeAsync(30);
  expect(postSettled).toBe(true);
  expect((await postError as Error).message).toContain('Request timeout after 25ms');

  let getSettled = false;
  const getPromise = transport
    .request({ method: 'GET', path: '/sessions/s1/messages' })
    .finally(() => {
      getSettled = true;
    });
  const getError = getPromise.then(
    () => null,
    (err) => err,
  );

  await vi.advanceTimersByTimeAsync(30);
  expect(getSettled).toBe(false);

  await vi.advanceTimersByTimeAsync(80);
  expect((await getError as Error).message).toContain('Request timeout after 100ms');
});