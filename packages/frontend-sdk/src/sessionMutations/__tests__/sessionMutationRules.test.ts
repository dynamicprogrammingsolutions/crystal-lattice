import { describe, expect, it } from 'vitest';

import { isEventForSession } from '../sessionMutationRules';

describe('session mutation rules', () => {
  it('matches events by scope and session id', () => {
    const event = {
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    };

    expect(isEventForSession(event, 'conn-1', 's1')).toBe(true);
    expect(isEventForSession(event, 'conn-2', 's1')).toBe(false);
    expect(isEventForSession(event, 'conn-1', 's2')).toBe(false);
  });
});
