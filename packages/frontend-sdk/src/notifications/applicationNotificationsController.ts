import type { AgentBackend } from '../backend/backend';
import { PollingEventSource } from '../events/pollingEventSource';
import { emitApplicationActionsInvalidated } from '../plugins/applicationActionsInvalidation';
import { emitDisplayPresentation, normalizeDisplayEnvelope } from '../plugins/displayPresentation';
import type { ApplicationNotification } from '../types/applicationNotifications';
import { SimpleSubscribable } from '../util/subscribable';
import { mergeApplicationNotificationEvents } from './applicationNotifications';
import {
  isNewerNotification,
  notificationExpectedRevision,
} from './notificationLifecycle';

export interface ApplicationNotificationsState {
  notifications: ApplicationNotification[];
  running: boolean;
  loading: boolean;
  error: string | null;
}

export class ApplicationNotificationsController extends SimpleSubscribable<ApplicationNotificationsState> {
  private readonly backend: AgentBackend;
  private readonly connectionId?: string | null;
  private readonly source: PollingEventSource;
  private readonly hydrateSnapshot: boolean;
  private generation = 0;

  constructor(options: {
    backend: AgentBackend;
    connectionId?: string | null;
    intervalMs?: number;
    backoffMs?: number;
    hydrateSnapshot?: boolean;
  }) {
    super({
      notifications: [],
      running: false,
      loading: false,
      error: null,
    });
    this.backend = options.backend;
    this.connectionId = options.connectionId;
    this.hydrateSnapshot = options.hydrateSnapshot === true;
    this.source = new PollingEventSource(options.backend, {
      applicationScope: true,
      intervalMs: options.intervalMs,
      backoffMs: options.backoffMs,
    });
  }

  start(): void {
    if (this.getSnapshot().running) return;
    const generation = ++this.generation;
    this.setSnapshot({
      ...this.getSnapshot(),
      running: true,
      loading: true,
      error: null,
    });
    void this.initialize(generation);
  }

  private async initialize(generation: number): Promise<void> {
    let initialSinceId = '0';
    try {
      initialSinceId = (await this.backend.getLatestEventId()) ?? '0';
    } catch {
      initialSinceId = '0';
    }

    let notifications = this.getSnapshot().notifications;
    let error: string | null = null;
    if (!this.hydrateSnapshot) {
      notifications = this.getSnapshot().notifications;
    } else if (this.backend.listApplicationNotifications) {
      try {
        notifications = await this.backend.listApplicationNotifications();
      } catch (caught) {
        error =
          caught instanceof Error
            ? caught.message || 'Failed to load application notifications.'
            : 'Failed to load application notifications.';
      }
    } else {
      error = 'Backend does not support application notification snapshots.';
    }

    if (generation !== this.generation || !this.getSnapshot().running) {
      return;
    }

    this.setSnapshot({
      ...this.getSnapshot(),
      notifications,
      loading: false,
      error,
    });
    this.source.start({
      sessionId: null,
      initialSinceId,
      onEvents: (events) => {
        const current = this.getSnapshot();
        const notifications = mergeApplicationNotificationEvents(
          current.notifications,
          events.filter(
            (event) => event.type !== 'application_notification_dismissed',
          ),
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
      onCursorExpired: () => {
        if (!this.getSnapshot().running) return;
        const nextGeneration = ++this.generation;
        this.setSnapshot({
          ...this.getSnapshot(),
          loading: true,
          error: null,
        });
        void this.initialize(nextGeneration);
      },
    });
  }

  async dismiss(notificationId: string): Promise<ApplicationNotification> {
    const current = this.getSnapshot();
    const notification = current.notifications.find(
      (item) => item.id === notificationId,
    );
    if (!notification) {
      throw new Error(`Application notification ${notificationId} is not loaded.`);
    }
    if (!this.backend.dismissApplicationNotification) {
      throw new Error('Backend does not support application notification dismissal.');
    }
    const dismissed = await this.backend.dismissApplicationNotification(
      notificationId,
      {
        expectedRevision: notificationExpectedRevision(notification),
        reason: 'user',
      },
    );
    const byId = new Map(
      current.notifications.map((item) => [item.id, item]),
    );
    const existing = byId.get(dismissed.id);
    if (!existing || isNewerNotification(dismissed, existing)) {
      byId.set(dismissed.id, dismissed);
    }
    this.setSnapshot({
      ...this.getSnapshot(),
      notifications: [...byId.values()].sort((left, right) =>
        left.updated_at.localeCompare(right.updated_at),
      ),
    });
    return dismissed;
  }

  close(): void {
    this.generation += 1;
    this.source.stop();
    this.setSnapshot({
      ...this.getSnapshot(),
      running: false,
      loading: false,
    });
  }
}