import {
  type AgentBackend,
  type ConnectionRecord,
} from '@crystal-lattice/frontend-sdk';

import { MobileConnectionSessionStatusReader } from '../connectionSessionStatusReader';

const SNAPSHOT = {
  version: 1 as const,
  authority: 'derived_transient' as const,
  statuses: [
    {
      session_id: 'session',
      request_id: null,
      state: 'succeeded' as const,
      basis: 'session_tail' as const,
      session_modified: 10,
    },
  ],
  missing_session_ids: [],
};

describe('MobileConnectionSessionStatusReader', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('uses the active backend without constructing another connection', async () => {
    const getSessionRequestStatuses = jest.fn(async () => SNAPSHOT);
    const backend = { getSessionRequestStatuses } as unknown as AgentBackend;
    const record: ConnectionRecord = {
      id: 'active',
      kind: 'cloud',
      name: 'Cloud',
      orchestratorUrl: 'https://cloud.test',
      connectionId: 'connection',
      token: 'token',
      lastUsedAt: 1,
    };

    const result = await new MobileConnectionSessionStatusReader(
      'active',
      backend,
    ).getSessionRequestStatuses(record, ['session']);

    expect(result).toEqual({ status: 'ok', snapshot: SNAPSHOT });
    expect(getSessionRequestStatuses).toHaveBeenCalledWith(
      ['session'],
      { signal: undefined },
    );
  });

  it('performs one direct HTTP query for a closed manual connection', async () => {
    const fetchMock = jest
      .spyOn(global, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify(SNAPSHOT), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        }),
      );
    const record: ConnectionRecord = {
      id: 'manual',
      kind: 'manual',
      name: 'Manual',
      host: 'server.test',
      port: 9000,
      lastUsedAt: 1,
    };

    const result = await new MobileConnectionSessionStatusReader(
      null,
      null,
    ).getSessionRequestStatuses(record, ['session']);

    expect(result).toEqual({ status: 'ok', snapshot: SNAPSHOT });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toBe(
      'http://server.test:9000/sessions/request-statuses',
    );
    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({ session_ids: ['session'] }),
    );
  });

  it('uses the bridge HTTP proxy without opening a WebSocket', async () => {
    const fetchMock = jest
      .spyOn(global, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify(SNAPSHOT), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        }),
      );
    const record: ConnectionRecord = {
      id: 'bridge',
      kind: 'bridge',
      name: 'Bridge',
      bridgeUrl: 'wss://bridge.test/ws/websocket',
      serverId: 'server',
      serverName: 'Server',
      pairingToken: 'pairing-token',
      transportMode: 'websocket',
      lastUsedAt: 1,
    };

    const result = await new MobileConnectionSessionStatusReader(
      null,
      null,
    ).getSessionRequestStatuses(record, ['session']);

    expect(result).toEqual({ status: 'ok', snapshot: SNAPSHOT });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toBe(
      'https://bridge.test/bridge/v1/proxy/sessions/request-statuses',
    );
    expect(
      (fetchMock.mock.calls[0][1]?.headers as Record<string, string>)[
        'X-Crystal-Bridge-Token'
      ],
    ).toBe('pairing-token');
  });

  it('reports unsupported legacy endpoints, repair-required bridge records, and closed cloud', async () => {
    jest.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'not found' }), {
        status: 404,
        headers: { 'content-type': 'application/json' },
      }),
    );
    const reader = new MobileConnectionSessionStatusReader(null, null);
    const manual: ConnectionRecord = {
      id: 'manual',
      kind: 'manual',
      name: 'Manual',
      host: 'server.test',
      port: 9000,
      lastUsedAt: 1,
    };
    const bridge: ConnectionRecord = {
      id: 'bridge',
      kind: 'bridge',
      name: 'Bridge',
      bridgeUrl: 'wss://bridge.test/ws',
      serverId: 'server',
      serverName: 'Server',
      pairingToken: null,
      lastUsedAt: 1,
    };
    const cloud: ConnectionRecord = {
      id: 'cloud',
      kind: 'cloud',
      name: 'Cloud',
      orchestratorUrl: 'https://cloud.test',
      instanceId: 'instance',
      token: 'token',
      lastUsedAt: 1,
    };

    await expect(
      reader.getSessionRequestStatuses(manual, ['session']),
    ).resolves.toEqual({ status: 'unsupported' });
    await expect(
      reader.getSessionRequestStatuses(bridge, ['session']),
    ).resolves.toEqual({ status: 'repair_required' });
    await expect(
      reader.getSessionRequestStatuses(cloud, ['session']),
    ).resolves.toEqual({ status: 'unsupported' });
  });

  it('aborts a stateless direct request through the supplied signal', async () => {
    const fetchMock = jest.spyOn(global, 'fetch').mockImplementation(
      async (_input, init) =>
        await new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => {
            reject(new Error('aborted'));
          });
        }),
    );
    const controller = new AbortController();
    const record: ConnectionRecord = {
      id: 'manual',
      kind: 'manual',
      name: 'Manual',
      host: 'server.test',
      port: 9000,
      lastUsedAt: 1,
    };
    const resultPromise = new MobileConnectionSessionStatusReader(
      null,
      null,
    ).getSessionRequestStatuses(record, ['session'], {
      signal: controller.signal,
    });

    controller.abort();

    await expect(resultPromise).resolves.toEqual({
      status: 'unavailable',
      message: 'aborted',
    });
    expect(fetchMock.mock.calls[0][1]?.signal?.aborted).toBe(true);
  });
});