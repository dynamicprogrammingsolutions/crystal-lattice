import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import WS from 'ws';

import { BridgeTransport } from '../../transport/bridgeTransport';
import type { WebSocketLike } from '../../transport/bridgeTransport';
import type { BridgeConnectionTransport } from '../../transport/bridgeConnectionTransport';
import { HttpBridgeTransport } from '../../transport/httpBridgeTransport';
import { HybridBridgeTransport } from '../../transport/hybridBridgeTransport';
import {
  startBackendServer,
  startBridgeForE2E,
  waitForAsync,
  waitForStdoutMatch,
} from '../harness';

const IS_AWS_E2E = (process.env.BRIDGE_E2E_MODE || '').startsWith('aws-');
const TEST_TIMEOUT_MS = IS_AWS_E2E ? 2_700_000 : 600_000;
const HOOK_TIMEOUT_MS = IS_AWS_E2E ? 900_000 : 10_000;

class NodeWebSocketWrapper implements WebSocketLike {
  private sock: WS;
  private sentMessages?: any[];

  onopen: ((ev?: any) => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: ((ev: any) => void) | null = null;
  onclose: ((ev: { code?: number; reason?: string; wasClean?: boolean }) => void) | null = null;

  constructor(url: string, sentMessages?: any[]) {
    this.sentMessages = sentMessages;
    this.sock = new WS(url);
    this.sock.on('open', () => this.onopen?.());
    this.sock.on('message', (data) => this.onmessage?.({ data: String(data) }));
    this.sock.on('error', (err) => this.onerror?.(err));
    this.sock.on('close', (code, reason) => this.onclose?.({ code, reason: String(reason) }));
  }

  get readyState(): number {
    return this.sock.readyState;
  }

  send(data: string): void {
    if (this.sentMessages) {
      this.sentMessages.push(JSON.parse(data));
    }
    this.sock.send(data);
  }

  close(code?: number, reason?: string): void {
    this.sock.close(code, reason);
  }
}

async function pairTransport(options: {
  transport: BridgeConnectionTransport;
  serverId: string;
  stdout: string[];
}): Promise<void> {
  await options.transport.connect();
  await waitForAsync(
    async () => {
      const servers = await options.transport.listServers();
      return servers.some((server) => server.server_id === options.serverId);
    },
    { timeoutMs: 30_000, intervalMs: 250 },
  );
  await options.transport.requestPairing(options.serverId);
  const match = await waitForStdoutMatch({
    stdout: options.stdout,
    pattern: /PAIRING CODE:\s*(\d{6})/,
    timeoutMs: 30_000,
  });
  await options.transport.submitPairingCode(options.serverId, match[1]);
}

describe('bridge e2e (TS BridgeTransport -> Elixir bridge -> Python BridgeClient -> FastAPI)', () => {
  let stopAll: Array<() => Promise<void>> = [];
  let sharedAwsBridge: Awaited<ReturnType<typeof startBridgeForE2E>> | null = null;

  beforeAll(async () => {
    if (IS_AWS_E2E) {
      sharedAwsBridge = await startBridgeForE2E();
      stopAll.push(sharedAwsBridge.stop);
    }
  }, HOOK_TIMEOUT_MS);

  afterAll(async () => {
    for (const stop of stopAll.reverse()) {
      await stop();
    }
    stopAll = [];
  }, HOOK_TIMEOUT_MS);

  it(
    'supports large request + large response bodies',
    async () => {
      const bridge = sharedAwsBridge ?? (await startBridgeForE2E());
      if (!sharedAwsBridge) {
        stopAll.push(bridge.stop);
      }

      const serverId = `e2e-server-${Date.now()}`;

      const started = await startBackendServer({
        config: {
          providers: {
            test_provider: {
              provider: 'deterministic_stream',
              model: 'test-model',
              timeout: 60,
              stream_chunk_count: 1,
              stream_chunk_delay_ms: 0,
            },
          },
          plugins: ['plugins.deterministic_stream_provider.DeterministicStreamProvider'],
          agents: {
            default: {
              provider: 'test_provider',
            },
          },
        },
        env: {
          BRIDGE_URL: bridge.bridgeUrl,
          BRIDGE_SERVER_ID: serverId,
          BRIDGE_DISPLAY_NAME: 'E2E Test Server',
          BRIDGE_HTTP_TIMEOUT_SECONDS: '120.0',
        },
      });
      stopAll.push(started.stop);

      const transport = new BridgeTransport({
        bridgeUrl: bridge.bridgeUrl,
        serverId,
        wsFactory: (url: string): WebSocketLike => new NodeWebSocketWrapper(url),
      });
      await transport.connect();

      // Wait until server is visible via bridge registry.
      await waitForAsync(
        async () => {
          const servers = await transport.listServers();
          return servers.some((s) => s.server_id === serverId);
        },
        { timeoutMs: 30_000, intervalMs: 250 },
      );

      await transport.requestPairing(serverId);
      const match = await waitForStdoutMatch({
        stdout: started.stdout,
        pattern: /PAIRING CODE:\s*(\d{6})/,
        timeoutMs: 30_000,
      });
      const code = match[1];

      await transport.submitPairingCode(serverId, code);

      const big = 'x'.repeat(900_000);

      const putResp = await transport.request({
        method: 'PUT',
        path: '/api/data',
        body: { blob: big },
        timeoutMs: 120_000,
      });

      expect(putResp.status).toBe(200);
      expect(putResp.data.success).toBe(true);
      expect(putResp.data.updated.blob.length).toBe(big.length);

      const getResp = await transport.request({
        method: 'GET',
        path: '/api/data',
        timeoutMs: 120_000,
      });

      expect(getResp.status).toBe(200);
      expect(getResp.data.success).toBe(true);
      expect(getResp.data.data.blob.length).toBe(big.length);
    },
    TEST_TIMEOUT_MS,
  );

  it(
    'supports HTTP-only large JSON and raw binary request/response bodies',
    async () => {
      const bridge = sharedAwsBridge ?? (await startBridgeForE2E());
      if (!sharedAwsBridge) {
        stopAll.push(bridge.stop);
      }
      const serverId = `e2e-http-server-${Date.now()}`;
      const started = await startBackendServer({
        config: {
          providers: {
            test_provider: {
              provider: 'deterministic_stream',
              model: 'test-model',
            },
          },
          plugins: ['plugins.deterministic_stream_provider.DeterministicStreamProvider'],
          agents: { default: { provider: 'test_provider' } },
        },
        enableTestControl: true,
        env: {
          BRIDGE_URL: bridge.bridgeUrl,
          BRIDGE_SERVER_ID: serverId,
          BRIDGE_DISPLAY_NAME: 'HTTP E2E Test Server',
          BRIDGE_HTTP_TIMEOUT_SECONDS: '120.0',
        },
      });
      stopAll.push(started.stop);

      let compressedProxyResponseSeen = false;
      const transport = new HttpBridgeTransport({
        bridgeUrl: bridge.bridgeUrl,
        defaultRequestTimeoutMs: 120_000,
        fetchImpl: (async (input: any, init?: RequestInit) => {
          const response = await fetch(input, init);
          if (
            String(input).includes('/bridge/v1/proxy/') &&
            response.headers.get('content-encoding') === 'gzip'
          ) {
            compressedProxyResponseSeen = true;
          }
          return response;
        }) as typeof fetch,
      });
      await pairTransport({ transport, serverId, stdout: started.stdout });

      const big = 'h'.repeat(1_200_000);
      const putJson = await transport.request<any>({
        method: 'PUT',
        path: '/api/data',
        body: { blob: big },
      });
      expect(putJson.status).toBe(200);
      expect(putJson.data.updated.blob).toHaveLength(big.length);

      const binary = new Uint8Array(512 * 1024);
      for (let index = 0; index < binary.length; index += 1) {
        binary[index] = index % 251;
      }
      const putBinary = await transport.request<ArrayBuffer>({
        method: 'PUT',
        path: '/__test/binary',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: binary,
      });
      expect(Array.from(new Uint8Array(putBinary.data))).toEqual(Array.from(binary));

      const getBinary = await transport.request<ArrayBuffer>({
        method: 'GET',
        path: '/__test/binary?size=524288',
      });
      expect(new Uint8Array(getBinary.data)).toEqual(binary);
      expect(compressedProxyResponseSeen).toBe(true);

      transport.prepareForResume();
      const resumed = await transport.request<any>({
        method: 'GET',
        path: '/api/hello',
      });
      expect(resumed.data.message).toMatch(/Hello from Bonjour Server!/);

      const events = await transport.request<any>({
        method: 'GET',
        path: '/events',
      });
      expect(events.data.events).toEqual([]);
    },
    TEST_TIMEOUT_MS,
  );

  it(
    'uses HTTP for normal hybrid requests and legacy WebSocket only for events',
    async () => {
      const bridge = sharedAwsBridge ?? (await startBridgeForE2E());
      if (!sharedAwsBridge) {
        stopAll.push(bridge.stop);
      }
      const serverId = `e2e-hybrid-server-${Date.now()}`;
      const started = await startBackendServer({
        config: {
          providers: {
            test_provider: {
              provider: 'deterministic_stream',
              model: 'test-model',
            },
          },
          plugins: ['plugins.deterministic_stream_provider.DeterministicStreamProvider'],
          agents: { default: { provider: 'test_provider' } },
        },
        env: {
          BRIDGE_URL: bridge.bridgeUrl,
          BRIDGE_SERVER_ID: serverId,
          BRIDGE_DISPLAY_NAME: 'Hybrid E2E Test Server',
        },
      });
      stopAll.push(started.stop);

      const fetchedUrls: string[] = [];
      const sentWebSocketMessages: any[] = [];
      const transport = new HybridBridgeTransport({
        bridgeUrl: bridge.bridgeUrl,
        fetchImpl: (async (input: any, init?: RequestInit) => {
          fetchedUrls.push(String(input));
          return await fetch(input, init);
        }) as typeof fetch,
        wsFactory: (url: string): WebSocketLike =>
          new NodeWebSocketWrapper(url, sentWebSocketMessages),
        defaultRequestTimeoutMs: 30_000,
      });
      await pairTransport({ transport, serverId, stdout: started.stdout });

      const hello = await transport.request<any>({
        method: 'GET',
        path: '/api/hello',
      });
      expect(hello.data.message).toMatch(/Hello from Bonjour Server!/);

      const events = await transport.request<any>({
        method: 'GET',
        path: '/events',
      });
      expect(events.data.events).toEqual([]);

      expect(fetchedUrls.some((url) => url.includes('/bridge/v1/proxy/api/hello'))).toBe(true);
      expect(fetchedUrls.some((url) => url.includes('/bridge/v1/proxy/events'))).toBe(false);
      expect(
        sentWebSocketMessages.some(
          (message) => message.event === 'http_request' && message.payload?.path === '/events',
        ),
      ).toBe(true);
    },
    TEST_TIMEOUT_MS,
  );

  it(
    'reconnects and resumes after the bridge restarts',
    async () => {
      const bridge = sharedAwsBridge ?? (await startBridgeForE2E());
      if (!sharedAwsBridge) {
        stopAll.push(bridge.stop);
      }

      const serverId = `e2e-recovery-server-${Date.now()}`;

      const started = await startBackendServer({
        config: {
          providers: {
            test_provider: {
              provider: 'deterministic_stream',
              model: 'test-model',
              timeout: 60,
              stream_chunk_count: 1,
              stream_chunk_delay_ms: 0,
            },
          },
          plugins: ['plugins.deterministic_stream_provider.DeterministicStreamProvider'],
          agents: {
            default: {
              provider: 'test_provider',
            },
          },
        },
        env: {
          BRIDGE_URL: bridge.bridgeUrl,
          BRIDGE_SERVER_ID: serverId,
          BRIDGE_DISPLAY_NAME: 'E2E Recovery Test Server',
          BRIDGE_HTTP_TIMEOUT_SECONDS: '120.0',
        },
      });
      stopAll.push(started.stop);

      const transport = new BridgeTransport({
        bridgeUrl: bridge.bridgeUrl,
        serverId,
        wsFactory: (url: string): WebSocketLike => new NodeWebSocketWrapper(url),
        connectTimeoutMs: 5_000,
        heartbeatIntervalMs: 1_000,
        heartbeatTimeoutMs: 500,
        defaultRequestTimeoutMs: 5_000,
      });
      await transport.connect();

      await waitForAsync(
        async () => {
          const servers = await transport.listServers();
          return servers.some((s) => s.server_id === serverId);
        },
        { timeoutMs: 30_000, intervalMs: 250 },
      );

      await transport.requestPairing(serverId);
      const match = await waitForStdoutMatch({
        stdout: started.stdout,
        pattern: /PAIRING CODE:\s*(\d{6})/,
        timeoutMs: 30_000,
      });
      const code = match[1];

      await transport.submitPairingCode(serverId, code);

      const initial = await transport.request({
        method: 'GET',
        path: '/api/hello',
        timeoutMs: 5_000,
      });
      expect(initial.status).toBe(200);
      expect(initial.data.message).toMatch(/Hello from Bonjour Server!/);

      if (bridge.suspend) {
        await bridge.suspend();
      } else {
        await bridge.stop();
      }

      await expect(
        transport.request({
          method: 'GET',
          path: '/api/hello',
          timeoutMs: 1_500,
        }),
      ).rejects.toThrow();

      if (bridge.resume) {
        await bridge.resume();
      } else {
        const restartedBridge = await startBridgeForE2E();
        stopAll.push(restartedBridge.stop);
      }

      await waitForAsync(
        async () => {
          try {
            const servers = await transport.listServers();
            return servers.some((s) => s.server_id === serverId);
          } catch {
            return false;
          }
        },
        { timeoutMs: 60_000, intervalMs: 500 },
      );

      const resumed = await transport.request({
        method: 'GET',
        path: '/api/hello',
        timeoutMs: 5_000,
      });

      expect(resumed.status).toBe(200);
      expect(resumed.data.message).toMatch(/Hello from Bonjour Server!/);
    },
    TEST_TIMEOUT_MS,
  );

  it(
    'allows a fast proxied request to complete while an earlier slow request is pending',
    async () => {
      const bridge = sharedAwsBridge ?? (await startBridgeForE2E());
      if (!sharedAwsBridge) {
        stopAll.push(bridge.stop);
      }

      const serverId = `e2e-concurrent-server-${Date.now()}`;

      const started = await startBackendServer({
        config: {
          providers: {
            test_provider: {
              provider: 'deterministic_stream',
              model: 'test-model',
              timeout: 60,
              stream_chunk_count: 1,
              stream_chunk_delay_ms: 0,
            },
          },
          plugins: ['plugins.deterministic_stream_provider.DeterministicStreamProvider'],
          agents: {
            default: {
              provider: 'test_provider',
            },
          },
        },
        enableTestControl: true,
        env: {
          BRIDGE_URL: bridge.bridgeUrl,
          BRIDGE_SERVER_ID: serverId,
          BRIDGE_DISPLAY_NAME: 'E2E Concurrent Test Server',
          BRIDGE_HTTP_TIMEOUT_SECONDS: '120.0',
        },
      });
      stopAll.push(started.stop);

      const sleepPreflight = await fetch(`${started.baseUrl}/__test/sleep?ms=1`);
      expect(sleepPreflight.status).toBe(200);

      const transport = new BridgeTransport({
        bridgeUrl: bridge.bridgeUrl,
        serverId,
        wsFactory: (url: string): WebSocketLike => new NodeWebSocketWrapper(url),
        defaultRequestTimeoutMs: 10_000,
      });
      await transport.connect();

      await waitForAsync(
        async () => {
          const servers = await transport.listServers();
          return servers.some((s) => s.server_id === serverId);
        },
        { timeoutMs: 30_000, intervalMs: 250 },
      );

      await transport.requestPairing(serverId);
      const match = await waitForStdoutMatch({
        stdout: started.stdout,
        pattern: /PAIRING CODE:\s*(\d{6})/,
        timeoutMs: 30_000,
      });
      const code = match[1];

      await transport.submitPairingCode(serverId, code);

      const completions: string[] = [];
      const slowPromise = transport
        .request<{ slept_ms: number }>({
          method: 'GET',
          path: '/__test/sleep?ms=2000',
          timeoutMs: 10_000,
        })
        .then((resp) => {
          completions.push('slow');
          return resp;
        });
      slowPromise.catch(() => {
        // The assertion below awaits this promise; this prevents a transient
        // unhandled-rejection report while the fast request is being checked.
      });

      const fastPromise = transport
        .request<{ message: string }>({
          method: 'GET',
          path: '/api/hello',
          timeoutMs: 10_000,
        })
        .then((resp) => {
          completions.push('fast');
          return resp;
        });

      const fastResp = await fastPromise.catch((err: any) => {
        throw new Error(`fast request failed: ${err?.message ?? String(err)}`);
      });
      expect(fastResp.status).toBe(200);
      expect(fastResp.data.message).toMatch(/Hello from Bonjour Server!/);
      expect(completions).toEqual(['fast']);

      const slowResp = await slowPromise.catch((err: any) => {
        throw new Error(`slow request failed: ${err?.message ?? String(err)}`);
      });
      expect(slowResp.status).toBe(200);
      expect(slowResp.data.slept_ms).toBe(2000);
      expect(completions).toEqual(['fast', 'slow']);
    },
    TEST_TIMEOUT_MS,
  );
});
