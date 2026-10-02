import { describe, expect, it, vi } from 'vitest';

import {
  acknowledgeRefreshUiEffect,
  emitRefreshUiEffects,
  NotificationUiEffectObserver,
  parseRefreshUiEffects,
  subscribeSessionRefreshInvalidations,
  subscribeSessionsListRefreshInvalidations,
  subscribeRefreshUiEffects,
} from './uiEffects';

describe('refresh UI effects', () => {
  it('parses and deduplicates the shared refresh fields', () => {
    expect(
      parseRefreshUiEffects({
        reload_session_ids: ['s1', 's1', '', 3],
        reload_sessions_list: true,
        reload_application_actions: true,
        unknown: 'ignored',
      }),
    ).toEqual([
      { type: 'reloadSession', sessionId: 's1' },
      { type: 'reloadSessionsList' },
      { type: 'reloadApplicationActions' },
    ]);
  });

  it('dispatches once per notification revision and isolates backends', () => {
    const firstBackend = {} as any;
    const secondBackend = {} as any;
    const first = vi.fn();
    const second = vi.fn();
    subscribeRefreshUiEffects(firstBackend, first);
    subscribeRefreshUiEffects(secondBackend, second);
    const observer = new NotificationUiEffectObserver(firstBackend);
    const notification = {
      id: 'n1',
      status: 'pending',
      revision: 2,
      updated_at: 'now',
      ui_effects: { reload_session_ids: ['s1'] },
    };

    observer.observe('session', notification);
    observer.observe('session', notification);

    expect(first).toHaveBeenCalledTimes(1);
    expect(second).not.toHaveBeenCalled();
    observer.observe('session', { ...notification, revision: 3 });
    expect(first).toHaveBeenCalledTimes(2);
  });

  it('replays pending invalidations to late consumers until acknowledged', () => {
    const backend = {} as any;
    emitRefreshUiEffects(backend, { reload_session_ids: ['s1'] });
    const late = vi.fn();

    subscribeRefreshUiEffects(backend, late);

    expect(late).toHaveBeenCalledTimes(1);
    const invalidation = late.mock.calls[0][0];
    acknowledgeRefreshUiEffect(backend, invalidation);
    const later = vi.fn();
    subscribeRefreshUiEffects(backend, later);
    expect(later).not.toHaveBeenCalled();
  });

  it('does not execute effects carried by terminal legacy revisions', () => {
    const backend = {} as any;
    const listener = vi.fn();
    subscribeRefreshUiEffects(backend, listener);
    const observer = new NotificationUiEffectObserver(backend);

    observer.observe('session', {
      id: 'n1',
      status: 'dismissed',
      revision: 3,
      updated_at: 'later',
      ui_effects: { reload_session_ids: ['s1'] },
    });

    expect(listener).not.toHaveBeenCalled();
  });

  it('consumes an invalidation after one failed reload attempt', async () => {
    const backend = {} as any;
    emitRefreshUiEffects(backend, { reload_session_ids: ['s1'] });
    const failingReload = vi.fn(async () => false);
    const unsubscribeFailing = subscribeSessionRefreshInvalidations(
      backend,
      's1',
      failingReload,
    );
    await vi.waitFor(() => {
      expect(failingReload).toHaveBeenCalledTimes(1);
    });
    // Let the acknowledge/consume chain settle.
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    unsubscribeFailing();

    // A resubscribed consumer must not replay the failed invalidation:
    // replaying persistently failing invalidations to every new
    // subscriber creates an infinite retry + error-alert loop.
    const retriedReload = vi.fn(async () => true);
    subscribeSessionRefreshInvalidations(backend, 's1', retriedReload);
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    expect(retriedReload).not.toHaveBeenCalled();
  });

  it('consumes an invalidation after a rejected reload attempt', async () => {
    const backend = {} as any;
    emitRefreshUiEffects(backend, { reload_sessions_list: true });
    const rejectedReload = vi.fn(async () => {
      throw new Error('network down');
    });
    subscribeSessionsListRefreshInvalidations(backend, rejectedReload);
    await vi.waitFor(() => {
      expect(rejectedReload).toHaveBeenCalledTimes(1);
    });
    await new Promise<void>((resolve) => setTimeout(resolve, 0));

    const laterReload = vi.fn(async () => true);
    subscribeSessionsListRefreshInvalidations(backend, laterReload);
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    expect(laterReload).not.toHaveBeenCalled();
  });

  it('acknowledges after a successful reload and does not replay it', async () => {
    const backend = {} as any;
    emitRefreshUiEffects(backend, { reload_session_ids: ['s1'] });
    const activeReload = vi.fn(async () => true);
    subscribeSessionRefreshInvalidations(backend, 's1', activeReload);
    await vi.waitFor(() => {
      expect(activeReload).toHaveBeenCalledTimes(1);
    });
    await Promise.resolve();
    await Promise.resolve();

    const afterAcknowledgement = vi.fn(async () => true);
    subscribeSessionRefreshInvalidations(
      backend,
      's1',
      afterAcknowledgement,
    );
    expect(afterAcknowledgement).not.toHaveBeenCalled();
  });

  it('does not replay an in-flight invalidation when a consumer resubscribes', async () => {
    const backend = {} as any;
    emitRefreshUiEffects(backend, { reload_session_ids: ['s1'] });
    let resolveReload: ((value: boolean) => void) | null = null;
    const reload = vi.fn(
      () =>
        new Promise<boolean>((resolve) => {
          resolveReload = resolve;
        }),
    );
    const unsubscribe = subscribeSessionRefreshInvalidations(
      backend,
      's1',
      reload,
    );
    expect(reload).toHaveBeenCalledTimes(1);

    unsubscribe();
    const resubscribedReload = vi.fn(async () => true);
    subscribeSessionRefreshInvalidations(
      backend,
      's1',
      resubscribedReload,
    );
    expect(resubscribedReload).not.toHaveBeenCalled();

    resolveReload?.(true);
    await Promise.resolve();
    await Promise.resolve();
    const afterAcknowledgement = vi.fn(async () => true);
    subscribeSessionRefreshInvalidations(
      backend,
      's1',
      afterAcknowledgement,
    );
    expect(afterAcknowledgement).not.toHaveBeenCalled();
  });

  it('ignores notification navigation fields', () => {
    const backend = {} as any;
    const listener = vi.fn();
    subscribeRefreshUiEffects(backend, listener);

    emitRefreshUiEffects(backend, { navigate_to_session_id: 's2' });

    expect(listener).not.toHaveBeenCalled();
  });
});
