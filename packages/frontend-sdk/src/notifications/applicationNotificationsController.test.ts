import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../backend/backend';
import type { ApplicationNotification } from '../types/applicationNotifications';
import { ApplicationNotificationsController } from './applicationNotificationsController';

const pending: ApplicationNotification = {
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
};

describe('ApplicationNotificationsController', () => {
  it('hydrates from a snapshot before polling and applies server dismissal', async () => {
    const calls: string[] = [];
    const dismissApplicationNotification = vi.fn(async () => ({
      ...pending,
      status: 'dismissed' as const,
      revision: 3,
      updated_at: '2026-08-01T00:00:02Z',
      dismissal: {
        dismissed_at: '2026-08-01T00:00:02Z',
        reason: 'user',
      },
    }));
    const backend = {
      kind: 'inProcess',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: false,
        applicationConfig: false,
        notificationLifecycle: true,
      }),
      getLatestEventId: async () => {
        calls.push('cursor');
        return '7';
      },
      listApplicationNotifications: async () => {
        calls.push('snapshot');
        return [pending];
      },
      dismissApplicationNotification,
      listEvents: async () => {
        calls.push('events');
        return {
          events: [
            {
              event_id: '8',
              type: 'application_notification_dismissed',
              notification: {
                ...pending,
                status: 'dismissed',
                revision: 3,
                updated_at: '2026-08-01T00:00:02Z',
                dismissal: {
                  dismissed_at: '2026-08-01T00:00:02Z',
                },
              },
            },
          ],
          latestEventId: '8',
          cursorExpired: false,
        };
      },
    } as unknown as AgentBackend;
    const controller = new ApplicationNotificationsController({
      backend,
      intervalMs: 60_000,
      hydrateSnapshot: true,
    });

    controller.start();
    await vi.waitFor(() => {
      expect(controller.getSnapshot().loading).toBe(false);
    });
    expect(calls.slice(0, 2)).toEqual(['cursor', 'snapshot']);
    expect(controller.getSnapshot().notifications).toEqual([pending]);
    await vi.waitFor(() => {
      expect(calls).toContain('events');
    });
    expect(controller.getSnapshot().notifications).toEqual([pending]);

    const dismissed = await controller.dismiss(pending.id);
    expect(dismissApplicationNotification).toHaveBeenCalledWith(pending.id, {
      expectedRevision: 2,
      reason: 'user',
    });
    expect(dismissed.status).toBe('dismissed');
    expect(controller.getSnapshot().notifications).toEqual([dismissed]);

    controller.close();
  });
});