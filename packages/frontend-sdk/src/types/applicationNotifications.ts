import type { ActionDisplayPayload } from './plugins';
import type {
  NotificationRetention,
  NotificationSeverity,
  NotificationStatus,
} from './notifications';

export interface ApplicationNotification {
  id: string;
  key: string;
  kind: 'notification';
  status: NotificationStatus;
  revision?: number;
  severity: NotificationSeverity;
  title: string;
  body: string;
  created_at: string;
  updated_at: string;
  request_id?: string | null;
  retention?: NotificationRetention;
  source: {
    plugin: string;
    [key: string]: any;
  };
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

export interface ApplicationNotificationEvent {
  event_id: string;
  type:
    | 'application_notification_created'
    | 'application_notification_updated'
    | 'application_notification_dismissed'
    | 'application_notification_expired';
  notification: ApplicationNotification;
  [key: string]: any;
}