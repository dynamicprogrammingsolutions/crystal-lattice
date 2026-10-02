import { afterAll, describe, expect, it } from 'vitest';
import WS from 'ws';

import { BridgeTransport } from '../../transport/bridgeTransport';
import type { WebSocketLike } from '../../transport/bridgeTransport';
import {
  startBackendViaCLI,
  startBridgeForE2E,
  waitForAsync,
  waitForStdoutMatch,
} from '../harness';

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

const TEST_TIMEOUT_MS = 600_000;
const HOOK_TIMEOUT_MS = 10_000;

describe('bridge CLI e2e (real CLI entrypoint + BridgeTransport -> Elixir bridge -> Python BridgeClient)', () => {
  let stopAll: Array<() => Promise<void>> = [];

  afterAll(async () => {
    for (const stop of stopAll.reverse()) {
      await stop();
    }
    stopAll = [];
  }, HOOK_TIMEOUT_MS);

  it(
    'registers with bridge and serves a proxied HTTP request via the real CLI',
    async () => {
      // Start the Elixir bridge via Docker.
      const bridge = await startBridgeForE2E();
      stopAll.push(bridge.stop);

      const serverId = `cli-e2e-server-${Date.now()}`;

      // Start the CLI with --enable-bridge --no-tty.
      const started = await startBackendViaCLI({
        bridgeUrl: bridge.bridgeUrl,
        serverId,
        displayName: 'CLI E2E Test Server',
        config: {
          application: {
            bridge: {
              http_timeout_seconds: 90,
            },
          },
        },
        startupTimeoutMs: 180_000,
      });
      stopAll.push(started.stop);

      // Connect via BridgeTransport.
      const transport = new BridgeTransport({
        bridgeUrl: bridge.bridgeUrl,
        serverId,
        wsFactory: (url: string): WebSocketLike => new NodeWebSocketWrapper(url),
      });
      await transport.connect();

      // Wait until the server is visible via the bridge registry.
      await waitForAsync(
        async () => {
          const servers = await transport.listServers();
          return servers.some((s) => s.server_id === serverId);
        },
        { timeoutMs: 30_000, intervalMs: 250 },
      );

      // Request pairing.
      await transport.requestPairing(serverId);

      // Read the pairing code from the CLI's stdout.
      const match = await waitForStdoutMatch({
        stdout: started.stdout,
        pattern: /PAIRING CODE:\s*(\d{6})/,
        timeoutMs: 30_000,
      });
      const code = match[1];

      await transport.submitPairingCode(serverId, code);

      // Send a proxied HTTP request through the bridge.
      const resp = await transport.request({
        method: 'GET',
        path: '/api/hello',
        timeoutMs: 30_000,
      });

      expect(resp.status).toBe(200);
      expect(resp.data.message).toBe('Hello from Bonjour Server!');
    },
    TEST_TIMEOUT_MS,
  );
});