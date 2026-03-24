import { describe, expect, it, vi } from 'vitest';

import { RestAgentBackend } from './restBackend';
import type { Transport } from '../transport/transport';

function createTransport(responseData: unknown, status = 200) {
  const requestMock = vi.fn(async () => ({ status, data: responseData }));
  const transport: Transport = {
    request: requestMock as unknown as Transport['request'],
  };
  return { transport, requestMock };
}

describe('RestAgentBackend session plugins', () => {
  it('lists session plugins from {plugins}', async () => {
    const { transport, requestMock } = createTransport({
      plugins: [{ id: 'p1', kind: 'tools', enabled: true }],
    });

    const backend = new RestAgentBackend({ transport });
    const plugins = await backend.listSessionPlugins('s1');

    expect(plugins).toEqual([{ id: 'p1', kind: 'tools', enabled: true }]);
    expect(requestMock).toHaveBeenCalledWith({
      method: 'GET',
      path: '/sessions/s1/plugins',
    });
  });

  it('lists session plugins from raw array response', async () => {
    const { transport } = createTransport([{ id: 'p1', kind: 'tools', enabled: true }]);

    const backend = new RestAgentBackend({ transport });
    const plugins = await backend.listSessionPlugins('s1');

    expect(plugins).toEqual([{ id: 'p1', kind: 'tools', enabled: true }]);
  });

  it('sets session plugins', async () => {
    const { transport, requestMock } = createTransport({});

    const backend = new RestAgentBackend({ transport });
    await backend.setSessionPlugins('s1', ['p1', 'p2']);

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'PUT',
        path: '/sessions/s1/plugins',
        body: { enabled: ['p1', 'p2'] },
        headers: expect.objectContaining({
          'Idempotency-Key': expect.any(String),
        }),
      }),
    );
  });

  it('clears session plugins', async () => {
    const { transport, requestMock } = createTransport({});

    const backend = new RestAgentBackend({ transport });
    await backend.clearSessionPlugins('s1');

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'DELETE',
        path: '/sessions/s1/plugins',
        headers: expect.objectContaining({
          'Idempotency-Key': expect.any(String),
        }),
      }),
    );
  });
});
