import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../backend/backend';
import type { KeyValueStore } from '../storage/keyValueStore';
import type { ApplicationNotification } from '../types/applicationNotifications';
import { ApplicationNotificationsController } from './applicationNotificationsController';
import { NotificationDismissalCache } from './notificationDismissalCache';
import { subscribeRefreshUiEffects } from '../plugins/uiEffects';

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

function createStore(): KeyValueStore {
  const values = new Map<string, string>();
  return {
    get: async (key) => values.get(key) ?? null,
    set: async (key, value) => {
      values.set(key, value);
    },
    delete: async (key) => {
      values.delete(key);
    },
  };
}

function createBackend(options: {
  notification?: ApplicationNotification;
  dismiss: AgentBackend['dismissApplicationNotification'];
}): AgentBackend {
  return {
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
    getLatestEventId: async () => '0',
    listApplicationNotifications: async () =>
      options.notification ? [options.notification] : [],
    dismissApplicationNotification: options.dismiss,
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

describe('ApplicationNotificationsController', () => {
  it('dispatches hydrated application-notification effects once', async () => {
    const notification = {
      ...pending,
      ui_effects: {
        reload_sessions_list: true,
        reload_application_actions: true,
      },
    };
    const backend = createBackend({
      notification,
      dismiss: vi.fn(),
    });
    const effects: string[] = [];
    subscribeRefreshUiEffects(backend, (effect) => effects.push(effect.type));
    const controller = new ApplicationNotificationsController({
      backend,
      hydrateSnapshot: true,
      intervalMs: 60_000,
    });

    controller.start();
    await vi.waitFor(() => {
      expect(controller.getSnapshot().loading).toBe(false);
    });
    expect(effects).toEqual(['reloadSessionsList', 'reloadApplicationActions']);
    controller.close();
  });

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

  it('keeps a failed dismissal hidden in the revision-scoped cache', async () => {
    const dismissalCache = new NotificationDismissalCache({
      store: createStore(),
    });
    const dismissApplicationNotification = vi.fn(async () => {
      throw new Error('server unavailable');
    });
    const controller = new ApplicationNotificationsController({
      backend: createBackend({
        notification: pending,
        dismiss: dismissApplicationNotification,
      }),
      connectionId: 'connection-1',
      hydrateSnapshot: true,
      intervalMs: 60_000,
      dismissalCache,
    });

    controller.start();
    await vi.waitFor(() => {
      expect(controller.getSnapshot().notifications).toEqual([pending]);
    });
    await controller.dismiss(pending.id);

    expect(controller.getSnapshot().notifications).toEqual([]);
    expect(dismissalCache.getSnapshot().entries).toMatchObject([
      {
        connectionId: 'connection-1',
        scope: 'application',
        notificationId: pending.id,
        revision: pending.revision,
      },
    ]);
    controller.close();
  });

  it('rehydrates a cached exact dismissal and retries it without presenting', async () => {
    const store = createStore();
    const firstCache = new NotificationDismissalCache({ store });
    await firstCache.load();
    await firstCache.record({
      connectionId: 'connection-1',
      scope: 'application',
      notificationId: pending.id,
      revision: pending.revision!,
      dismissedAt: '2026-08-01T00:00:02Z',
    });
    const dismissalCache = new NotificationDismissalCache({ store });
    const dismissApplicationNotification = vi.fn(async () => {
      throw new Error('still unavailable');
    });
    const controller = new ApplicationNotificationsController({
      backend: createBackend({
        notification: pending,
        dismiss: dismissApplicationNotification,
      }),
      connectionId: 'connection-1',
      hydrateSnapshot: true,
      intervalMs: 60_000,
      dismissalCache,
    });

    controller.start();
    await vi.waitFor(() => {
      expect(controller.getSnapshot().loading).toBe(false);
      expect(controller.getSnapshot().notifications).toEqual([]);
      expect(dismissApplicationNotification).toHaveBeenCalledWith(pending.id, {
        expectedRevision: pending.revision,
        reason: 'user',
      });
    });
    controller.close();
  });

  it('removes an obsolete cached dismissal and presents the newer revision', async () => {
    const store = createStore();
    const dismissalCache = new NotificationDismissalCache({ store });
    await dismissalCache.load();
    await dismissalCache.record({
      connectionId: 'connection-1',
      scope: 'application',
      notificationId: pending.id,
      revision: pending.revision!,
      dismissedAt: '2026-08-01T00:00:02Z',
    });
    const newer = {
      ...pending,
      revision: pending.revision! + 1,
      body: 'New body',
      updated_at: '2026-08-01T00:00:03Z',
    };
    const dismissApplicationNotification = vi.fn();
    const controller = new ApplicationNotificationsController({
      backend: createBackend({
        notification: newer,
        dismiss: dismissApplicationNotification,
      }),
      connectionId: 'connection-1',
      hydrateSnapshot: true,
      intervalMs: 60_000,
      dismissalCache,
    });

    controller.start();
    await vi.waitFor(() => {
      expect(controller.getSnapshot().notifications).toEqual([newer]);
      expect(dismissalCache.getSnapshot().entries).toEqual([]);
    });
    expect(dismissApplicationNotification).not.toHaveBeenCalled();
    controller.close();
  });

  it('keeps accepted TTL notifications until reconstruction and suppresses them afterward', async () => {
    let now = new Date('2026-08-02T11:59:00Z');
    const ttlNotification: ApplicationNotification = {
      ...pending,
      retention: {
        version: 1,
        policy: 'ttl',
        expires_at: '2026-08-02T12:00:00Z',
      },
    };
    const backend = createBackend({
      notification: ttlNotification,
      dismiss: vi.fn(),
    });
    const first = new ApplicationNotificationsController({
      backend,
      hydrateSnapshot: true,
      intervalMs: 60_000,
      now: () => now,
    });

    first.start();
    await vi.waitFor(() => {
      expect(first.getSnapshot().notifications).toEqual([ttlNotification]);
    });
    now = new Date('2026-08-02T12:01:00Z');
    expect(first.getSnapshot().notifications).toEqual([ttlNotification]);
    first.close();

    const reopened = new ApplicationNotificationsController({
      backend,
      hydrateSnapshot: true,
      intervalMs: 60_000,
      now: () => now,
    });
    reopened.start();
    await vi.waitFor(() => {
      expect(reopened.getSnapshot().loading).toBe(false);
      expect(reopened.getSnapshot().notifications).toEqual([]);
    });
    reopened.close();
  });
});
