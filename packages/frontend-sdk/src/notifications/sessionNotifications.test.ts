import { describe, expect, it } from 'vitest';

import type { SessionNotification } from '../types/notifications';
import {
  dismissSessionNotificationLocally,
  mergeSessionNotificationEvents,
  selectPendingSessionNotifications,
  selectSessionNotifications,
} from './sessionNotifications';

const notification: SessionNotification = {
  id: 'notification-1',
  key: 'dummy:notification',
  kind: 'notification',
  status: 'pending',
  severity: 'success',
  title: 'Demo',
  body: 'Body',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  source: { plugin: 'dummy' },
  display: { format: 'text', body: 'Body', presentation: 'inline' },
  model_visibility: 'hidden',
};

describe('session notifications', () => {
  it('selects valid items and skips malformed metadata', () => {
    const selected = selectSessionNotifications({
      notifications: { items: [{ nope: true }, notification] },
    });
    expect(selected).toEqual([notification]);
    expect(selectPendingSessionNotifications({ notifications: { items: selected } })).toEqual([
      notification,
    ]);
  });

  it('merges lifecycle events by id', () => {
    const resolved = {
      ...notification,
      status: 'resolved' as const,
      updated_at: '2026-01-02T00:00:00Z',
      resolution: { action_id: 'resolve', resolved_at: '2026-01-02T00:00:00Z' },
    };
    expect(
      mergeSessionNotificationEvents([notification], [
        {
          event_id: 'event-2',
          type: 'session_notification_resolved',
          session_id: 'session-1',
          notification: resolved,
        },
      ]),
    ).toEqual([resolved]);
  });

  it('dismisses locally without mutating the notification', () => {
    const current = [notification];
    expect(dismissSessionNotificationLocally(current, notification.id)).toEqual([]);
    expect(current).toEqual([notification]);
  });
});