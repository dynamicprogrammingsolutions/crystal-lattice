import { describe, expect, it, vi } from 'vitest';

import {
  emitRefreshUiEffects,
  NotificationUiEffectObserver,
  parseRefreshUiEffects,
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

  it('ignores notification navigation fields', () => {
    const backend = {} as any;
    const listener = vi.fn();
    subscribeRefreshUiEffects(backend, listener);

    emitRefreshUiEffects(backend, { navigate_to_session_id: 's2' });

    expect(listener).not.toHaveBeenCalled();
  });
});
