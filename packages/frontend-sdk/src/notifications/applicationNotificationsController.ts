import type { AgentBackend } from '../backend/backend';
import { PollingEventSource } from '../events/pollingEventSource';
import { emitApplicationActionsInvalidated } from '../plugins/applicationActionsInvalidation';
import { emitDisplayPresentation, normalizeDisplayEnvelope } from '../plugins/displayPresentation';
import type { ApplicationNotification } from '../types/applicationNotifications';
import { SimpleSubscribable } from '../util/subscribable';
import { mergeApplicationNotificationEvents } from './applicationNotifications';

export interface ApplicationNotificationsState {
  notifications: ApplicationNotification[];
  dismissedIds: string[];
  running: boolean;
}

export class ApplicationNotificationsController extends SimpleSubscribable<ApplicationNotificationsState> {
  private readonly backend: AgentBackend;
  private readonly connectionId?: string | null;
  private readonly source: PollingEventSource;

  constructor(options: {
    backend: AgentBackend;
    connectionId?: string | null;
    intervalMs?: number;
    backoffMs?: number;
  }) {
    super({ notifications: [], dismissedIds: [], running: false });
    this.backend = options.backend;
    this.connectionId = options.connectionId;
    this.source = new PollingEventSource(options.backend, {
      applicationScope: true,
      intervalMs: options.intervalMs,
      backoffMs: options.backoffMs,
    });
  }

  start(): void {
    if (this.getSnapshot().running) return;
    this.setSnapshot({ ...this.getSnapshot(), running: true });
    this.source.start({
      sessionId: null,
      initialSinceId: null,
      onEvents: (events) => {
        const current = this.getSnapshot();
        const notifications = mergeApplicationNotificationEvents(
          current.notifications,
          events,
        );
        this.setSnapshot({ ...current, notifications });
        for (const event of events) {
          if (
            event.type === 'application_reload_completed' ||
            event.type === 'application_reload_failed'
          ) {
            emitApplicationActionsInvalidated(this.backend);
            const notification = (event as any).notification;
            if (notification?.display) {
              emitDisplayPresentation(
                this.backend,
                normalizeDisplayEnvelope({
                  id: `${notification.id}:${event.type}`,
                  source: 'action_response',
                  connectionId: this.connectionId,
                  display: notification.display,
                  createdAt: notification.created_at,
                  updatedAt: notification.updated_at,
                }),
              );
            }
          }
        }
      },
    });
  }

  dismiss(notificationId: string): void {
    const current = this.getSnapshot();
    if (current.dismissedIds.includes(notificationId)) return;
    this.setSnapshot({
      ...current,
      dismissedIds: [...current.dismissedIds, notificationId],
    });
  }

  close(): void {
    this.source.stop();
    this.setSnapshot({ ...this.getSnapshot(), running: false });
  }
}