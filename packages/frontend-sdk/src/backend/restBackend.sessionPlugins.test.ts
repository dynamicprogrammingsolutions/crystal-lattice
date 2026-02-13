import { describe, expect, it, vi } from 'vitest';

import { RestAgentBackend } from './restBackend';
import type { Transport } from '../transport/transport';

describe('RestAgentBackend session plugins', () => {
  it('lists session plugins from {plugins}', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: { plugins: [{ id: 'p1', kind: 'tools', enabled: true }] },
      })),
    };

    const backend = new RestAgentBackend({ transport });
    const plugins = await backend.listSessionPlugins('s1');

    expect(plugins).toEqual([{ id: 'p1', kind: 'tools', enabled: true }]);
    expect(transport.request).toHaveBeenCalledWith({
      method: 'GET',
      path: '/sessions/s1/plugins',
    });
  });

  it('lists session plugins from raw array response', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: [{ id: 'p1', kind: 'tools', enabled: true }],
      })),
    };

    const backend = new RestAgentBackend({ transport });
    const plugins = await backend.listSessionPlugins('s1');

    expect(plugins).toEqual([{ id: 'p1', kind: 'tools', enabled: true }]);
  });

  it('sets session plugins', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: {} })),
    };

    const backend = new RestAgentBackend({ transport });
    await backend.setSessionPlugins('s1', ['p1', 'p2']);

    expect(transport.request).toHaveBeenCalledWith({
      method: 'PUT',
      path: '/sessions/s1/plugins',
      body: { enabled: ['p1', 'p2'] },
    });
  });

  it('clears session plugins', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: {} })),
    };

    const backend = new RestAgentBackend({ transport });
    await backend.clearSessionPlugins('s1');

    expect(transport.request).toHaveBeenCalledWith({
      method: 'DELETE',
      path: '/sessions/s1/plugins',
    });
  });
});
