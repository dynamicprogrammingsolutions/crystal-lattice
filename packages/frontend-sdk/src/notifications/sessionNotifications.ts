import type { Event } from '../types/events';
import type { SessionNotification, SessionNotificationEvent } from '../types/notifications';
import type { SessionSummary } from '../types/sessions';

const SEVERITIES = new Set(['info', 'success', 'warning', 'error']);

export function isSessionNotification(value: unknown): value is SessionNotification {
  const item = value as any;
  return (
    !!item &&
    typeof item === 'object' &&
    typeof item.id === 'string' &&
    !!item.id &&
    typeof item.key === 'string' &&
    !!item.key &&
    item.kind === 'notification' &&
    (item.status === 'pending' || item.status === 'resolved') &&
    SEVERITIES.has(item.severity) &&
    typeof item.title === 'string' &&
    typeof item.body === 'string' &&
    !!item.display &&
    typeof item.display === 'object' &&
    item.model_visibility === 'hidden'
  );
}

export function isSessionNotificationEvent(
  event: Event,
): event is SessionNotificationEvent {
  return (
    (event.type === 'session_notification_created' ||
      event.type === 'session_notification_updated' ||
      event.type === 'session_notification_resolved') &&
    isSessionNotification((event as any).notification)
  );
}

export function selectSessionNotifications(
  input: SessionSummary | Record<string, any> | null | undefined,
): SessionNotification[] {
  const metadata =
    input && typeof input === 'object' && 'session_id' in input
      ? (input as SessionSummary).metadata
      : input;
  const container =
    metadata && typeof metadata === 'object' ? (metadata as any).notifications : null;
  const items = container && Array.isArray(container.items) ? container.items : [];
  return items
    .filter(isSessionNotification)
    .sort((left: SessionNotification, right: SessionNotification) =>
      left.updated_at.localeCompare(right.updated_at),
    );
}

export function selectPendingSessionNotifications(
  input: SessionSummary | Record<string, any> | null | undefined,
): SessionNotification[] {
  return selectSessionNotifications(input).filter((item) => item.status === 'pending');
}

export function mergeSessionNotificationEvents(
  current: readonly SessionNotification[],
  events: readonly Event[],
): SessionNotification[] {
  const byId = new Map(current.map((notification) => [notification.id, notification]));
  for (const event of events) {
    if (!isSessionNotificationEvent(event)) continue;
    byId.set(event.notification.id, event.notification);
  }
  return [...byId.values()].sort((left, right) =>
    left.updated_at.localeCompare(right.updated_at),
  );
}

export function dismissSessionNotificationLocally(
  current: readonly SessionNotification[],
  notificationId: string,
): SessionNotification[] {
  return current.filter((notification) => notification.id !== notificationId);
}