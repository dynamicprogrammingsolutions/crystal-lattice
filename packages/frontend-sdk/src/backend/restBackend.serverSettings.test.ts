import { describe, expect, it, vi } from 'vitest';

import { RestAgentBackend } from './restBackend';
import type { Transport } from '../transport/transport';

describe('RestAgentBackend server settings', () => {
  it('maps server settings methods to live HTTP routes', async () => {
    const transport: Transport = {
      request: vi.fn(async (request) => {
        if (request.method === 'GET') {
          return { status: 200, data: { settings: { mode: 'fast' } } };
        }
        return { status: 200, data: {} };
      }),
    };
    const backend = new RestAgentBackend({ transport });

    await expect(backend.getServerSettings()).resolves.toEqual({ mode: 'fast' });
    await backend.patchServerSettings({ mode: 'careful' });
    await backend.deleteServerSetting('mode');

    expect(transport.request).toHaveBeenNthCalledWith(1, {
      method: 'GET',
      path: '/server/settings',
    });
    expect(transport.request).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: 'PATCH',
        path: '/server/settings',
        body: { values: { mode: 'careful' } },
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
    expect(transport.request).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        method: 'DELETE',
        path: '/server/settings/mode',
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
  });
});