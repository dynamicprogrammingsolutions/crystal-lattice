import { describe, expect, it } from 'vitest';

import { SdkEventBus } from '../sdkEventBus';

describe('SdkEventBus', () => {
  it('increments sequence and records last event on emit', () => {
    const bus = new SdkEventBus();

    bus.emit({
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });

    expect(bus.getSnapshot()).toEqual({
      seq: 1,
      lastEvent: {
        type: 'session.plugins.changed',
        scopeKey: 'conn-1',
        sessionId: 's1',
      },
    });
  });

  it('notifies subscribers once per emit', () => {
    const bus = new SdkEventBus();
    let calls = 0;

    bus.subscribe(() => {
      calls += 1;
    });

    bus.emit({
      type: 'session.overrides.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });
    bus.emit({
      type: 'session.agent.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });

    expect(calls).toBe(2);
  });

  it('stops notifying after unsubscribe', () => {
    const bus = new SdkEventBus();
    let calls = 0;

    const unsubscribe = bus.subscribe(() => {
      calls += 1;
    });

    bus.emit({
      type: 'session.agent.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });
    unsubscribe();
    bus.emit({
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });

    expect(calls).toBe(1);
  });
});
