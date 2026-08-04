import type { BaseEvent } from './events';
import type { ActionDisplayPayload } from './plugins';

export type NotificationStatus = 'pending' | 'dismissed' | 'resolved' | 'expired';
export type SessionNotificationStatus = NotificationStatus;
export type NotificationExpectedRevision = number | string;
export type NotificationSeverity = 'info' | 'success' | 'warning' | 'error';
export type NotificationRetention =
  | { version?: 1; policy: 'until_resolved' }
  | { version?: 1; policy: 'ttl'; expires_at: string }
  | { version?: 1; policy: 'until_request_complete' }
  | { version?: 1; policy: 'until_server_restart'; owner_epoch?: string };

export interface NotificationOperation {
  version: 1;
  type: string;
  id: string;
  state: string;
  phase?: string;
  started_at?: string;
  elapsed_seconds?: number;
  cancellable?: boolean;
  process_id?: string;
  [key: string]: any;
}

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
  retention?: NotificationRetention;
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
  operation?: NotificationOperation;
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