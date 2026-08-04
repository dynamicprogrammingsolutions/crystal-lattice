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
  revision: 1,
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
      revision: 2,
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

  it('merges background operation progress revisions', () => {
    const running: SessionNotification = {
      ...notification,
      operation: {
        version: 1,
        type: 'openai_responses_native_compaction',
        id: 'operation-1',
        state: 'running',
        phase: 'waiting_for_provider',
        elapsed_seconds: 15,
        cancellable: true,
      },
    };
    const heartbeat: SessionNotification = {
      ...running,
      revision: 2,
      body: 'Waiting for OpenAI native compaction. Elapsed: 30 seconds.',
      display: {
        ...running.display,
        body: 'Waiting for OpenAI native compaction. Elapsed: 30 seconds.',
      },
      operation: {
        ...running.operation!,
        elapsed_seconds: 30,
      },
    };

    expect(
      mergeSessionNotificationEvents([running], [
        {
          event_id: 'event-heartbeat',
          type: 'session_notification_updated',
          session_id: 'session-1',
          notification: heartbeat,
        },
      ]),
    ).toEqual([heartbeat]);
  });

  it('selects terminal records but excludes them from active presentation', () => {
    const dismissed = {
      ...notification,
      status: 'dismissed' as const,
      revision: 2,
      dismissal: {
        dismissed_at: '2026-08-01T00:00:00Z',
      },
    };
    expect(
      selectSessionNotifications({
        notifications: { items: [notification, dismissed] },
      }),
    ).toEqual([notification, dismissed]);
    expect(
      selectPendingSessionNotifications({
        notifications: { items: [notification, dismissed] },
      }),
    ).toEqual([notification]);
  });

  it('dismisses locally without mutating the notification', () => {
    const current = [notification];
    expect(dismissSessionNotificationLocally(current, notification.id)).toEqual([]);
    expect(current).toEqual([notification]);
  });
});