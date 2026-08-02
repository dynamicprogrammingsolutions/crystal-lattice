import type { NotificationRetention } from '../types/notifications';

export interface RetentionAwareNotification {
  retention?: NotificationRetention;
}

export function isNotificationTtlElapsed(
  notification: RetentionAwareNotification,
  now: Date = new Date(),
): boolean {
  const retention = notification.retention;
  if (!retention || retention.policy !== 'ttl') return false;
  const expiresAt = Date.parse(retention.expires_at);
  if (!Number.isFinite(expiresAt)) return false;
  return now.getTime() >= expiresAt;
}