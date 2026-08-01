import { describe, expect, it, vi } from 'vitest';

import type { Transport } from '../transport/transport';
import { RestAgentBackend } from './restBackend';

const notification = {
  id: 'notification-1',
  key: 'demo',
  kind: 'notification',
  status: 'pending',
  revision: 2,
  severity: 'info',
  title: 'Demo',
  body: 'Body',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:01Z',
  source: { plugin: 'dummy' },
  display: { format: 'text', body: 'Body', presentation: 'banner' },
  model_visibility: 'hidden',
} as const;

describe('RestAgentBackend notifications', () => {
  it('maps application and session snapshot/dismiss operations', async () => {
    const transport: Transport = {
      request: vi.fn(async (request) => {
        if (request.method === 'GET') {
          return {
            status: 200,
            data: { notifications: [notification] },
          };
        }
        return {
          status: 200,
          data: {
            notification: {
              ...notification,
              status: 'dismissed',
              revision: 3,
            },
          },
        };
      }),
    };
    const backend = new RestAgentBackend({ transport });

    await backend.listApplicationNotifications({ includeTerminal: true });
    await backend.dismissApplicationNotification('notification-1', {
      expectedRevision: 2,
      reason: 'user',
    });
    await backend.listSessionNotifications('session one', {
      includeTerminal: true,
    });
    await backend.dismissSessionNotification('session one', 'notification-1', {
      expectedRevision: 2,
      reason: 'user',
    });

    expect(transport.request).toHaveBeenNthCalledWith(1, {
      method: 'GET',
      path: '/application/notifications?include_terminal=true',
    });
    expect(transport.request).toHaveBeenNthCalledWith(2, {
      method: 'POST',
      path: '/application/notifications/notification-1/dismiss',
      body: {
        expected_revision: 2,
        reason: 'user',
      },
    });
    expect(transport.request).toHaveBeenNthCalledWith(3, {
      method: 'GET',
      path: '/sessions/session%20one/notifications?include_terminal=true',
    });
    expect(transport.request).toHaveBeenNthCalledWith(4, {
      method: 'POST',
      path: '/sessions/session%20one/notifications/notification-1/dismiss',
      body: {
        expected_revision: 2,
        reason: 'user',
      },
    });
  });
});