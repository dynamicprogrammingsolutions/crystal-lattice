import type { KeyValueStore } from '../storage/keyValueStore';
import type { NotificationExpectedRevision } from '../types/notifications';
import { SimpleSubscribable } from '../util/subscribable';

export type NotificationDismissalScope = 'application' | 'session';

export interface NotificationDismissalCacheEntry {
  connectionId: string;
  scope: NotificationDismissalScope;
  sessionId?: string;
  notificationId: string;
  revision: NotificationExpectedRevision;
  dismissedAt: string;
}

export interface NotificationDismissalObservation {
  id: string;
  status: string;
  revision?: number;
  updated_at: string;
}

export interface NotificationDismissalCacheState {
  loaded: boolean;
  entries: NotificationDismissalCacheEntry[];
}

export interface NotificationDismissalScopeKey {
  connectionId: string;
  scope: NotificationDismissalScope;
  sessionId?: string;
}

export type NotificationDismissalObservationResult = 'none' | 'suppress' | 'obsolete' | 'terminal';

const DEFAULT_STORAGE_KEY = 'clc_notification_dismissals_v1';
const DEFAULT_MAX_ENTRIES = 500;

function entryKey(entry: NotificationDismissalCacheEntry): string {
  return [entry.connectionId, entry.scope, entry.sessionId ?? '', entry.notificationId].join(':');
}

function sameScope(
  entry: NotificationDismissalCacheEntry,
  scope: NotificationDismissalScopeKey
): boolean {
  return (
    entry.connectionId === scope.connectionId &&
    entry.scope === scope.scope &&
    (entry.sessionId ?? '') === (scope.sessionId ?? '')
  );
}

function expectedRevision(
  observation: NotificationDismissalObservation
): NotificationExpectedRevision {
  return typeof observation.revision === 'number' && observation.revision > 0
    ? observation.revision
    : observation.updated_at;
}

function compareRevision(
  current: NotificationExpectedRevision,
  cached: NotificationExpectedRevision
): number | null {
  if (typeof current === 'number' && typeof cached === 'number') {
    return current === cached ? 0 : current > cached ? 1 : -1;
  }
  if (typeof current === 'string' && typeof cached === 'string') {
    return current === cached ? 0 : current > cached ? 1 : -1;
  }
  return null;
}

function isCacheEntry(value: unknown): value is NotificationDismissalCacheEntry {
  const entry = value as any;
  return (
    !!entry &&
    typeof entry === 'object' &&
    typeof entry.connectionId === 'string' &&
    !!entry.connectionId &&
    (entry.scope === 'application' || entry.scope === 'session') &&
    (entry.scope !== 'session' || (typeof entry.sessionId === 'string' && !!entry.sessionId)) &&
    typeof entry.notificationId === 'string' &&
    !!entry.notificationId &&
    ((typeof entry.revision === 'number' && entry.revision > 0) ||
      (typeof entry.revision === 'string' && !!entry.revision)) &&
    typeof entry.dismissedAt === 'string' &&
    !!entry.dismissedAt
  );
}

export function notificationDismissalRevisionKey(options: {
  connectionId: string;
  scope: NotificationDismissalScope;
  sessionId?: string;
  notificationId: string;
  revision: NotificationExpectedRevision;
}): string {
  return [
    options.connectionId,
    options.scope,
    options.sessionId ?? '',
    options.notificationId,
    String(options.revision),
  ].join(':');
}

export class NotificationDismissalCache extends SimpleSubscribable<NotificationDismissalCacheState> {
  private readonly store: KeyValueStore;
  private readonly storageKey: string;
  private readonly maxEntries: number;
  private loadPromise: Promise<void> | null = null;
  private persistPromise: Promise<void> = Promise.resolve();

  constructor(options: { store: KeyValueStore; storageKey?: string; maxEntries?: number }) {
    super({ loaded: false, entries: [] });
    this.store = options.store;
    this.storageKey = options.storageKey ?? DEFAULT_STORAGE_KEY;
    this.maxEntries = Math.max(1, options.maxEntries ?? DEFAULT_MAX_ENTRIES);
  }

  load(): Promise<void> {
    if (this.getSnapshot().loaded) return Promise.resolve();
    if (this.loadPromise) return this.loadPromise;
    this.loadPromise = this.loadFromStore();
    return this.loadPromise;
  }

  record(entry: NotificationDismissalCacheEntry): Promise<void> {
    const key = entryKey(entry);
    const entries = [...this.getSnapshot().entries.filter((item) => entryKey(item) !== key), entry]
      .sort((left, right) => left.dismissedAt.localeCompare(right.dismissedAt))
      .slice(-this.maxEntries);
    return this.replaceEntries(entries);
  }

  remove(entry: NotificationDismissalCacheEntry): Promise<void> {
    const key = entryKey(entry);
    return this.replaceEntries(this.getSnapshot().entries.filter((item) => entryKey(item) !== key));
  }

  find(options: {
    connectionId: string;
    scope: NotificationDismissalScope;
    sessionId?: string;
    notificationId: string;
  }): NotificationDismissalCacheEntry | null {
    return (
      this.getSnapshot().entries.find(
        (entry) =>
          entry.connectionId === options.connectionId &&
          entry.scope === options.scope &&
          (entry.sessionId ?? '') === (options.sessionId ?? '') &&
          entry.notificationId === options.notificationId
      ) ?? null
    );
  }

  observe(
    scope: NotificationDismissalScopeKey,
    notification: NotificationDismissalObservation
  ): NotificationDismissalObservationResult {
    const entry = this.find({
      ...scope,
      notificationId: notification.id,
    });
    if (!entry) return 'none';
    if (notification.status !== 'pending') {
      void this.remove(entry);
      return 'terminal';
    }
    const comparison = compareRevision(expectedRevision(notification), entry.revision);
    if (comparison === 0 || comparison === -1) {
      return 'suppress';
    }
    void this.remove(entry);
    return 'obsolete';
  }

  reconcileSnapshot(
    scope: NotificationDismissalScopeKey,
    notifications: readonly NotificationDismissalObservation[]
  ): Set<string> {
    const byId = new Map(notifications.map((notification) => [notification.id, notification]));
    const suppressed = new Set<string>();
    for (const entry of this.getSnapshot().entries.filter((item) => sameScope(item, scope))) {
      const notification = byId.get(entry.notificationId);
      if (!notification) {
        void this.remove(entry);
        continue;
      }
      const result = this.observe(scope, notification);
      if (result === 'suppress') {
        suppressed.add(
          notificationDismissalRevisionKey({
            ...scope,
            notificationId: notification.id,
            revision: expectedRevision(notification),
          })
        );
      }
    }
    return suppressed;
  }

  private async loadFromStore(): Promise<void> {
    let entries: NotificationDismissalCacheEntry[] = [];
    try {
      const raw = await this.store.get(this.storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          entries = parsed.filter(isCacheEntry).slice(-this.maxEntries);
        }
      }
    } catch {
      entries = [];
    }
    this.setSnapshot({ loaded: true, entries });
  }

  private replaceEntries(entries: NotificationDismissalCacheEntry[]): Promise<void> {
    this.setSnapshot({ loaded: true, entries });
    const serialized = JSON.stringify(entries);
    this.persistPromise = this.persistPromise
      .catch(() => undefined)
      .then(async () => {
        try {
          if (entries.length === 0) {
            await this.store.delete(this.storageKey);
          } else {
            await this.store.set(this.storageKey, serialized);
          }
        } catch {
          // The in-memory suppression remains useful for this frontend lifetime.
        }
      });
    return this.persistPromise;
  }
}
