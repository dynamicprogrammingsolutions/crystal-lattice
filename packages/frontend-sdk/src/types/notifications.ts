import type { BaseEvent } from './events';
import type { ActionDisplayPayload } from './plugins';

export type SessionNotificationStatus = 'pending' | 'resolved';
export type NotificationSeverity = 'info' | 'success' | 'warning' | 'error';

export interface SessionNotification {
  id: string;
  key: string;
  kind: 'notification';
  status: SessionNotificationStatus;
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
  model_visibility: 'hidden';
}

export interface SessionNotificationEvent extends BaseEvent {
  type:
    | 'session_notification_created'
    | 'session_notification_updated'
    | 'session_notification_resolved';
  notification: SessionNotification;
}