import { describe, expect, it, vi } from 'vitest';

import { RestAgentBackend } from './restBackend';
import type { Transport } from '../transport/transport';
import { subscribeServerSettingsInvalidated } from '../serverSettings/serverSettingsInvalidation';

describe('RestAgentBackend server settings', () => {
  it('maps server settings methods to live HTTP routes', async () => {
    const transport: Transport = {
      request: vi.fn(async (request) => {
        if (request.method === 'GET' && request.path === '/server/settings') {
          return { status: 200, data: { settings: { mode: 'fast' } } };
        }
        if (request.method === 'GET' && request.path === '/server/settings/ui-schema') {
          return { status: 200, data: { elements: [{ key: 'mode' }] } };
        }
        return { status: 200, data: {} };
      }),
    };
    const backend = new RestAgentBackend({ transport });

    await expect(backend.getServerSettings()).resolves.toEqual({ mode: 'fast' });
    await expect(backend.listServerSettingsUiSchema()).resolves.toEqual([{ key: 'mode' }]);
    await backend.patchServerSettings({ mode: 'careful' });
    await backend.deleteServerSetting('mode');

    expect(transport.request).toHaveBeenNthCalledWith(1, {
      method: 'GET',
      path: '/server/settings',
    });
    expect(transport.request).toHaveBeenNthCalledWith(
      2,
      {
        method: 'GET',
        path: '/server/settings/ui-schema',
      },
    );
    expect(transport.request).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        method: 'PATCH',
        path: '/server/settings',
        body: { values: { mode: 'careful' } },
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
    expect(transport.request).toHaveBeenNthCalledWith(
      4,
      expect.objectContaining({
        method: 'DELETE',
        path: '/server/settings/mode',
        headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      }),
    );
  });

  it('emits server settings invalidation after successful mutations', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: {} })),
    };
    const backend = new RestAgentBackend({ transport });
    const onInvalidate = vi.fn();

    const unsubscribe = subscribeServerSettingsInvalidated(backend, onInvalidate);
    try {
      await backend.patchServerSettings({ mode: 'careful' });
      await backend.deleteServerSetting('mode');
    } finally {
      unsubscribe();
    }

    expect(onInvalidate).toHaveBeenCalledTimes(2);
    expect(onInvalidate).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({ reason: 'server_settings_updated' }),
    );
    expect(onInvalidate).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ reason: 'server_settings_updated' }),
    );
  });
});