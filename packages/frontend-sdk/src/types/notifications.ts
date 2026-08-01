import type { BaseEvent } from './events';
import type { ActionDisplayPayload } from './plugins';

export type NotificationStatus = 'pending' | 'dismissed' | 'resolved' | 'expired';
export type SessionNotificationStatus = NotificationStatus;
export type NotificationExpectedRevision = number | string;
export type NotificationSeverity = 'info' | 'success' | 'warning' | 'error';

export interface SessionNotification {
  id: string;
  key: string;
  kind: 'notification';
  status: SessionNotificationStatus;
  revision?: number;
  severity: NotificationSeverity;
  title: string;
  body: string;
  created_at: string;
  updated_at: string;
  request_id?: string | null;
  source: { plugin: string; [key: string]: any };
  display: ActionDisplayPayload;
  resolution?: {
    action_id?: string;
    values?: Record<string, any>;
    resolved_at: string;
    [key: string]: any;
  } | null;
  dismissal?: {
    dismissed_at: string;
    reason?: string;
    [key: string]: any;
  } | null;
  expiration?: {
    expired_at: string;
    reason?: string;
    [key: string]: any;
  } | null;
  model_visibility: 'hidden';
}

export interface SessionNotificationEvent extends BaseEvent {
  type:
    | 'session_notification_created'
    | 'session_notification_updated'
    | 'session_notification_resolved'
    | 'session_notification_dismissed'
    | 'session_notification_expired';
  notification: SessionNotification;
}