import { describe, expect, it } from 'vitest';

import { mergeApplicationNotificationEvents } from './applicationNotifications';

describe('application notifications', () => {
  it('merges created and updated global events by notification id', () => {
    const created = {
      id: 'notification-1',
      key: 'application:reload',
      kind: 'notification',
      status: 'pending',
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
});