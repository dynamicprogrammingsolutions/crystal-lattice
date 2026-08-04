import { describe, expect, it } from 'vitest';

import { mergeApplicationNotificationEvents } from './applicationNotifications';

describe('application notifications', () => {
  it('merges created and updated global events by notification id', () => {
    const created = {
      id: 'notification-1',
      key: 'application:reload',
      kind: 'notification',
      status: 'pending',
      revision: 1,
      severity: 'info',
      title: 'Requested',
      body: 'Waiting',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      source: { plugin: 'application_owner' },
      display: { format: 'text', body: 'Waiting' },
      model_visibility: 'hidden',
    } as const;
    const updated = {
      ...created,
      status: 'resolved',
      revision: 2,
      severity: 'success',
      title: 'Completed',
      updated_at: '2026-01-01T00:00:01Z',
    } as const;

    const merged = mergeApplicationNotificationEvents([], [
      {
        event_id: '1',
        type: 'application_notification_created',
        notification: created,
      },
      {
        event_id: '2',
        type: 'application_notification_updated',
        notification: updated,
      },
    ]);

    expect(merged).toEqual([updated]);
  });

  it('does not replace a newer snapshot record with a stale event', () => {
    const current = {
      id: 'notification-1',
      key: 'application:reload',
      kind: 'notification',
      status: 'dismissed',
      revision: 3,
      severity: 'info',
      title: 'Dismissed',
      body: 'Done',
      created_at: '2026-08-01T00:00:00Z',
      updated_at: '2026-08-01T00:00:03Z',
      source: { plugin: 'application_owner' },
      display: { format: 'text', body: 'Done' },
      model_visibility: 'hidden',
    } as const;
    const stale = {
      ...current,
      status: 'pending',
      revision: 2,
      updated_at: '2026-08-01T00:00:02Z',
    } as const;

    expect(
      mergeApplicationNotificationEvents([current], [
        {
          event_id: '2',
          type: 'application_notification_updated',
          notification: stale,
        },
      ]),
    ).toEqual([current]);
  });
});