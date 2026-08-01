import { describe, expect, it } from 'vitest';

import type { KeyValueStore } from '../storage/keyValueStore';
import {
  NotificationDismissalCache,
  notificationDismissalRevisionKey,
} from './notificationDismissalCache';

function createStore(): KeyValueStore & { values: Map<string, string> } {
  const values = new Map<string, string>();
  return {
    values,
    get: async (key) => values.get(key) ?? null,
    set: async (key, value) => {
      values.set(key, value);
    },
    delete: async (key) => {
      values.delete(key);
    },
  };
}

describe('NotificationDismissalCache', () => {
  it('persists only revision-scoped synchronization metadata', async () => {
    const store = createStore();
    const cache = new NotificationDismissalCache({ store });
    await cache.load();

    await cache.record({
      connectionId: 'connection-1',
      scope: 'session',
      sessionId: 'session-1',
      notificationId: 'notification-1',
      revision: 4,
      dismissedAt: '2026-08-01T00:00:00Z',
    });

    const serialized = [...store.values.values()][0];
    expect(serialized).toContain('"revision":4');
    expect(serialized).not.toContain('title');
    expect(serialized).not.toContain('body');

    const reopened = new NotificationDismissalCache({ store });
    await reopened.load();
    expect(reopened.getSnapshot().entries).toEqual(cache.getSnapshot().entries);
  });

  it('suppresses the exact revision and removes an obsolete older dismissal', async () => {
    const store = createStore();
    const cache = new NotificationDismissalCache({ store });
    await cache.load();
    await cache.record({
      connectionId: 'connection-1',
      scope: 'application',
      notificationId: 'notification-1',
      revision: 4,
      dismissedAt: '2026-08-01T00:00:00Z',
    });
    const scope = {
      connectionId: 'connection-1',
      scope: 'application' as const,
    };

    expect(
      cache.observe(scope, {
        id: 'notification-1',
        status: 'pending',
        revision: 4,
        updated_at: '2026-08-01T00:00:00Z',
      })
    ).toBe('suppress');
    expect(
      cache.observe(scope, {
        id: 'notification-1',
        status: 'pending',
        revision: 5,
        updated_at: '2026-08-01T00:00:01Z',
      })
    ).toBe('obsolete');
    expect(cache.getSnapshot().entries).toEqual([]);
  });

  it('reconciles exact revisions and clears missing records', async () => {
    const store = createStore();
    const cache = new NotificationDismissalCache({ store });
    await cache.load();
    const entry = {
      connectionId: 'connection-1',
      scope: 'session' as const,
      sessionId: 'session-1',
      notificationId: 'notification-1',
      revision: 2,
      dismissedAt: '2026-08-01T00:00:00Z',
    };
    await cache.record(entry);
    const scope = {
      connectionId: entry.connectionId,
      scope: entry.scope,
      sessionId: entry.sessionId,
    };

    expect(
      cache.reconcileSnapshot(scope, [
        {
          id: entry.notificationId,
          status: 'pending',
          revision: entry.revision,
          updated_at: entry.dismissedAt,
        },
      ])
    ).toEqual(
      new Set([
        notificationDismissalRevisionKey({
          ...scope,
          notificationId: entry.notificationId,
          revision: entry.revision,
        }),
      ])
    );

    cache.reconcileSnapshot(scope, []);
    expect(cache.getSnapshot().entries).toEqual([]);
  });
});
