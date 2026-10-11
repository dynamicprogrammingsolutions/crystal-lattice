import { describe, expect, it, vi } from 'vitest';

import { BridgeTransport } from './bridgeTransport';
import {
  createBridgeConnectionTransport,
  type BridgeConnectionTransport,
} from './bridgeConnectionTransport';
import { deriveBridgeHttpBaseUrl, HttpBridgeTransport } from './httpBridgeTransport';
import { HybridBridgeTransport, isLegacyEventRequest } from './hybridBridgeTransport';

function jsonResponse(data: any, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

describe('HttpBridgeTransport', () => {
  it.each([404, 405])('explains HTTP capability incompatibility on HTTP %s without fallback', async (status) => {
    const wsFactory = vi.fn(() => { throw new Error('Unexpected socket'); });
    const transport = createBridgeConnectionTransport({
      bridgeUrl: 'wss://old.test/ws/websocket',
      fetchImpl: vi.fn(async () => jsonResponse({ error: 'not_found' }, status)),
      wsFactory,
    });
    await expect(transport.connect()).rejects.toThrow('does not support HTTP transport protocol v1');
    expect(wsFactory).not.toHaveBeenCalled();
  });
  it('derives an HTTP origin from supported bridge URLs', () => {
    expect(deriveBridgeHttpBaseUrl('ws://bridge.test:4000/ws/websocket')).toBe(
      'http://bridge.test:4000',
    );
    expect(deriveBridgeHttpBaseUrl('wss://bridge.test/prefix/ws/websocket?type=app')).toBe(
      'https://bridge.test/prefix',
    );
    expect(deriveBridgeHttpBaseUrl('https://bridge.test/base/')).toBe('https://bridge.test/base');
  });

  it('supports HTTP discovery, pairing, resume, and proxied JSON requests', async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    const fetchImpl = vi.fn(async (url: string | URL | Request, init?: RequestInit) => {
      const value = String(url);
      calls.push({ url: value, init: init ?? {} });
      if (value.endsWith('/bridge/v1/capabilities')) {
        return jsonResponse({ protocol_version: 1 });
      }
      if (value.endsWith('/bridge/v1/servers')) {
        return jsonResponse({
          servers: [
            {
              server_id: 'server-1',
              display_name: 'Server',
              computer_name: 'host',
            },
          ],
        });
      }
      if (value.endsWith('/bridge/v1/pairings/request')) {
        return jsonResponse({ pairing_request_token: 'request-token' });
      }
      if (value.endsWith('/bridge/v1/pairings/confirm')) {
        return jsonResponse({
          server_id: 'server-1',
          pairing_token: 'pairing-token',
        });
      }
      if (value.endsWith('/bridge/v1/pairings/resume')) {
        return jsonResponse({ server_id: 'server-1' });
      }
      if (value.endsWith('/bridge/v1/proxy/api/hello')) {
        return jsonResponse({ message: 'hello' });
      }
      throw new Error(`Unexpected URL ${value}`);
    });

    const transport = new HttpBridgeTransport({
      bridgeUrl: 'wss://bridge.test/ws/websocket',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    await transport.connect();
    expect((await transport.listServers())[0].server_id).toBe('server-1');
    await transport.requestPairing('server-1');
    await transport.submitPairingCode('server-1', '123456');
    const response = await transport.request<{ message: string }>({
      method: 'GET',
      path: '/api/hello',
    });
    expect(response).toEqual({ status: 200, data: { message: 'hello' } });
    expect(transport.getPairingToken()).toBe('pairing-token');

    transport.prepareForResume();
    await transport.request({ method: 'GET', path: '/api/hello' });

    const proxyCalls = calls.filter((call) => call.url.endsWith('/bridge/v1/proxy/api/hello'));
    expect(proxyCalls).toHaveLength(2);
    expect((proxyCalls[0].init.headers as Record<string, string>)['X-Crystal-Bridge-Token']).toBe(
      'pairing-token',
    );
    expect(calls.filter((call) => call.url.endsWith('/bridge/v1/pairings/resume'))).toHaveLength(1);
  });

  it('sends and receives binary bodies without JSON or base64 conversion', async () => {
    const input = new Uint8Array([0, 1, 2, 255]);
    let uploadedBody: any;
    const fetchImpl = vi.fn(async (_url: string | URL | Request, init?: RequestInit) => {
      uploadedBody = init?.body;
      return new Response(new Uint8Array([255, 2, 1, 0]), {
        status: 200,
        headers: { 'content-type': 'application/octet-stream' },
      });
    });
    const transport = new HttpBridgeTransport({
      bridgeUrl: 'https://bridge.test',
      serverId: 'server-1',
      pairingToken: 'pairing-token',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    const response = await transport.request<ArrayBuffer>({
      method: 'PUT',
      path: '/binary',
      headers: { 'Content-Type': 'application/octet-stream' },
      body: input,
    });

    expect(uploadedBody).toBe(input);
    expect(Array.from(new Uint8Array(response.data))).toEqual([255, 2, 1, 0]);
  });

  it('aborts an HTTP request at its resolved timeout', async () => {
    const fetchImpl = vi.fn(
      async (_url: string | URL | Request, init?: RequestInit) =>
        await new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => {
            reject(new Error('aborted'));
          });
        }),
    );
    const transport = new HttpBridgeTransport({
      bridgeUrl: 'https://bridge.test',
      serverId: 'server-1',
      pairingToken: 'pairing-token',
      fetchImpl: fetchImpl as unknown as typeof fetch,
      defaultRequestTimeoutMs: 5,
    });

    await expect(transport.request({ method: 'GET', path: '/slow' })).rejects.toThrow(
      'Request timeout after 5ms',
    );
  });

  it('fails capability negotiation clearly against a bridge without HTTP v1', async () => {
    const transport = new HttpBridgeTransport({
      bridgeUrl: 'https://legacy-bridge.test',
      fetchImpl: vi.fn(
        async () => jsonResponse({ protocol_version: 0 }),
      ) as unknown as typeof fetch,
    });

    await expect(transport.connect()).rejects.toThrow(
      'Bridge does not support HTTP transport protocol v1',
    );
  });

  it('never invokes the WebSocket factory in HTTP-only mode', async () => {
    const wsFactory = vi.fn(() => {
      throw new Error('HTTP-only mode opened a WebSocket');
    });
    const fetchImpl = vi.fn(async (url: string | URL | Request) => {
      const value = String(url);
      if (value.endsWith('/bridge/v1/capabilities')) {
        return jsonResponse({ protocol_version: 1 });
      }
      if (value.endsWith('/bridge/v1/pairings/resume')) {
        return jsonResponse({ server_id: 'server-1' });
      }
      if (value.endsWith('/bridge/v1/proxy/events')) {
        return jsonResponse({ events: [] });
      }
      throw new Error(`Unexpected URL ${value}`);
    });
    const transport = createBridgeConnectionTransport({
      bridgeUrl: 'wss://bridge.test/ws/websocket',
      serverId: 'server-1',
      pairingToken: 'pairing-token',
      fetchImpl: fetchImpl as unknown as typeof fetch,
      wsFactory,
    });

    await transport.connect();
    await transport.request({ method: 'GET', path: '/events' });

    expect(wsFactory).not.toHaveBeenCalled();
  });

  it('preserves an HTTP server-mismatch error during saved-token validation', async () => {
    const fetchImpl = vi.fn(async (url: string | URL | Request) => {
      const value = String(url);
      if (value.endsWith('/bridge/v1/capabilities')) {
        return jsonResponse({ protocol_version: 1 });
      }
      if (value.endsWith('/bridge/v1/pairings/resume')) {
        return jsonResponse({ error: 'server_mismatch' }, 409);
      }
      throw new Error(`Unexpected URL ${value}`);
    });
    const transport = new HttpBridgeTransport({
      bridgeUrl: 'https://bridge.test',
      serverId: 'server-1',
      pairingToken: 'pairing-token',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    await expect(transport.connect()).rejects.toThrow(
      'HTTP 409 POST /bridge/v1/pairings/resume: server_mismatch',
    );
  });
});

describe('HybridBridgeTransport', () => {
  it('routes only exact GET /events requests to the legacy transport', async () => {
    const httpPaths: string[] = [];
    const fetchImpl = vi.fn(async (url: string | URL | Request) => {
      const value = String(url);
      if (value.endsWith('/bridge/v1/capabilities')) {
        return jsonResponse({ protocol_version: 1 });
      }
      if (value.endsWith('/bridge/v1/pairings/resume')) {
        return jsonResponse({ server_id: 'server-1' });
      }
      const marker = '/bridge/v1/proxy';
      const markerIndex = value.indexOf(marker);
      if (markerIndex >= 0) {
        httpPaths.push(value.slice(markerIndex + marker.length));
        return jsonResponse({ source: 'http' });
      }
      throw new Error(`Unexpected URL ${value}`);
    });

    const legacyRequests: string[] = [];
    const fakeLegacy: BridgeConnectionTransport = {
      connect: async () => {},
      disconnect: () => {},
      prepareForResume: () => {},
      getPairingToken: () => 'pairing-token',
      getServerId: () => 'server-1',
      isPaired: () => true,
      listServers: async () => [],
      requestPairing: async () => {},
      submitPairingCode: async () => {},
      request: async <T = any>(request: { method: any; path: string }) => {
        legacyRequests.push(request.path);
        return { status: 200, data: { source: 'websocket' } as T };
      },
    };
    const transport = new HybridBridgeTransport({
      bridgeUrl: 'wss://bridge.test/ws/websocket',
      serverId: 'server-1',
      pairingToken: 'pairing-token',
      fetchImpl: fetchImpl as unknown as typeof fetch,
      legacyTransportFactory: () => fakeLegacy,
    });

    await transport.connect();
    await transport.request({ method: 'GET', path: '/events?since_id=1' });
    await transport.request({ method: 'POST', path: '/events' });
    await transport.request({ method: 'GET', path: '/events/archive' });
    await transport.request({ method: 'GET', path: '/sessions' });

    expect(legacyRequests).toEqual(['/events?since_id=1']);
    expect(httpPaths).toEqual(['/events', '/events/archive', '/sessions']);
  });

  it('defaults to HTTP and retains explicit legacy constructors', () => {
    expect(
      createBridgeConnectionTransport({
        bridgeUrl: 'ws://bridge.test/ws/websocket',
        wsFactory: () => {
          throw new Error('not connected in this test');
        },
      }),
    ).toBeInstanceOf(HttpBridgeTransport);
    expect(
      createBridgeConnectionTransport({
        bridgeUrl: 'ws://bridge.test/ws/websocket',
        mode: 'websocket',
      }),
    ).toBeInstanceOf(BridgeTransport);
    expect(
      createBridgeConnectionTransport({
        bridgeUrl: 'https://bridge.test',
        mode: 'http',
      }),
    ).toBeInstanceOf(HttpBridgeTransport);
    expect(
      createBridgeConnectionTransport({
        bridgeUrl: 'wss://bridge.test/ws/websocket',
        mode: 'hybrid',
      }),
    ).toBeInstanceOf(HybridBridgeTransport);
  });

  it('does not fall back to legacy WebSocket when an HTTP request fails', async () => {
    const fetchImpl = vi.fn(async (url: string | URL | Request) => {
      const value = String(url);
      if (value.endsWith('/bridge/v1/capabilities')) {
        return jsonResponse({ protocol_version: 1 });
      }
      if (value.endsWith('/bridge/v1/pairings/resume')) {
        return jsonResponse({ server_id: 'server-1' });
      }
      return jsonResponse({ error: 'http_failed' }, 503);
    });
    let legacyRequestCount = 0;
    const fakeLegacy: BridgeConnectionTransport = {
      connect: async () => {},
      disconnect: () => {},
      prepareForResume: () => {},
      getPairingToken: () => 'pairing-token',
      getServerId: () => 'server-1',
      isPaired: () => true,
      listServers: async () => [],
      requestPairing: async () => {},
      submitPairingCode: async () => {},
      request: async <T = any>() => {
        legacyRequestCount += 1;
        return { status: 200, data: {} as T };
      },
    };
    const transport = new HybridBridgeTransport({
      bridgeUrl: 'wss://bridge.test/ws/websocket',
      serverId: 'server-1',
      pairingToken: 'pairing-token',
      fetchImpl: fetchImpl as unknown as typeof fetch,
      legacyTransportFactory: () => fakeLegacy,
    });
    await transport.connect();

    await expect(transport.request({ method: 'POST', path: '/actions/run' })).rejects.toThrow(
      'http_failed',
    );
    expect(legacyRequestCount).toBe(0);
  });

  it('matches only GET /events and its query form', () => {
    expect(isLegacyEventRequest('GET', '/events')).toBe(true);
    expect(isLegacyEventRequest('GET', '/events?session_id=s1')).toBe(true);
    expect(isLegacyEventRequest('POST', '/events')).toBe(false);
    expect(isLegacyEventRequest('GET', '/events/archive')).toBe(false);
  });
});
