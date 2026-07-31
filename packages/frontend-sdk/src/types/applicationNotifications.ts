import type { ActionDisplayPayload } from './plugins';

export interface ApplicationNotification {
  id: string;
  key: string;
  kind: 'notification';
  status: 'pending' | 'resolved';
  severity: 'info' | 'success' | 'warning' | 'error';
  title: string;
  body: string;
  created_at: string;
  updated_at: string;
  source: {
    plugin: string;
    [key: string]: any;
  };
  display: ActionDisplayPayload;
  model_visibility: 'hidden';
}

export interface ApplicationNotificationEvent {
  event_id: string;
  type: 'application_notification_created' | 'application_notification_updated';
  notification: ApplicationNotification;
  [key: string]: any;
}