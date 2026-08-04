import type { NotificationExpectedRevision } from '../types/notifications';

export interface RevisionedNotification {
  revision?: number;
  updated_at: string;
  status: string;
}

export function notificationExpectedRevision(
  notification: RevisionedNotification,
): NotificationExpectedRevision {
  return typeof notification.revision === 'number' && notification.revision > 0
    ? notification.revision
    : notification.updated_at;
}

export function isActiveNotification(
  notification: Pick<RevisionedNotification, 'status'>,
): boolean {
  return notification.status === 'pending';
}

export function isNewerNotification(
  candidate: RevisionedNotification,
  current: RevisionedNotification,
): boolean {
  if (
    typeof candidate.revision === 'number' &&
    candidate.revision > 0 &&
    typeof current.revision === 'number' &&
    current.revision > 0
  ) {
    return candidate.revision > current.revision;
  }
  return candidate.updated_at > current.updated_at;
}