import type {
  ApplicationNotification,
  ApplicationNotificationEvent,
} from '../types/applicationNotifications';
import type { Event } from '../types/events';
import { isNewerNotification } from './notificationLifecycle';

export function isApplicationNotificationEvent(
  event: Event,
): event is ApplicationNotificationEvent {
  return (
    (event.type === 'application_notification_created' ||
      event.type === 'application_notification_updated' ||
      event.type === 'application_notification_dismissed' ||
      event.type === 'application_notification_expired') &&
    !!(event as any).notification
  );
}

export function mergeApplicationNotificationEvents(
  current: readonly ApplicationNotification[],
  events: readonly Event[],
): ApplicationNotification[] {
  const byId = new Map(current.map((notification) => [notification.id, notification]));
  for (const event of events) {
    if (!isApplicationNotificationEvent(event)) continue;
    const notification = event.notification;
    if (!notification || typeof notification.id !== 'string' || !notification.id) continue;
    const existing = byId.get(notification.id);
    if (!existing || isNewerNotification(notification, existing)) {
      byId.set(notification.id, notification);
    }
  }
  return [...byId.values()].sort((left, right) =>
    left.updated_at.localeCompare(right.updated_at),
  );
}