import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import WS from 'ws';

import { BridgeTransport } from '../../transport/bridgeTransport';
import type { WebSocketLike } from '../../transport/bridgeTransport';
import { startBackendServer, startBridgeForE2E, waitForAsync, waitForStdoutMatch } from '../harness';

const IS_AWS_E2E = (process.env.BRIDGE_E2E_MODE || '').startsWith('aws-');
const TEST_TIMEOUT_MS = IS_AWS_E2E ? 2_700_000 : 600_000;
const HOOK_TIMEOUT_MS = IS_AWS_E2E ? 900_000 : 10_000;

class NodeWebSocketWrapper implements WebSocketLike {
  private sock: WS;

  onopen: ((ev?: any) => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: ((ev: any) => void) | null = null;
  onclose: ((ev: { code?: number; reason?: string; wasClean?: boolean }) => void) | null = null;

  constructor(url: string) {
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
    this.sock.send(data);
  }

  close(code?: number, reason?: string): void {
    this.sock.close(code, reason);
  }
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
      await waitForAsync(async () => {
        const servers = await transport.listServers();
        return servers.some((s) => s.server_id === serverId);
      }, { timeoutMs: 30_000, intervalMs: 250 });

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

      await waitForAsync(async () => {
        const servers = await transport.listServers();
        return servers.some((s) => s.server_id === serverId);
      }, { timeoutMs: 30_000, intervalMs: 250 });

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

      await waitForAsync(async () => {
        try {
          const servers = await transport.listServers();
          return servers.some((s) => s.server_id === serverId);
        } catch {
          return false;
        }
      }, { timeoutMs: 60_000, intervalMs: 500 });

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

      await waitForAsync(async () => {
        const servers = await transport.listServers();
        return servers.some((s) => s.server_id === serverId);
      }, { timeoutMs: 30_000, intervalMs: 250 });

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
