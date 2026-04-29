import { afterAll, describe, expect, it } from 'vitest';
import WS from 'ws';

import { BridgeTransport } from '../../transport/bridgeTransport';
import type { WebSocketLike } from '../../transport/bridgeTransport';
import { startBackendServer, startBridgeForE2E, waitForAsync, waitForStdoutMatch } from '../harness';

const RUN = process.env.RUN_BRIDGE_E2E_INTEGRATION === '1';
const describeIf = RUN ? describe : describe.skip;
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

describeIf('bridge e2e (TS BridgeTransport -> Elixir bridge -> Python BridgeClient -> FastAPI)', () => {
  let stopAll: Array<() => Promise<void>> = [];

  afterAll(async () => {
    for (const stop of stopAll.reverse()) {
      await stop();
    }
    stopAll = [];
  }, HOOK_TIMEOUT_MS);

  it(
    'supports large request + large response bodies',
    async () => {
      const bridge = await startBridgeForE2E();
      stopAll.push(bridge.stop);

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
      const bridge = await startBridgeForE2E();
      stopAll.push(bridge.stop);

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
});
