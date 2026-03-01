import { describe, expect, it } from 'vitest';

import { BusAwareController } from '../busAwareController';
import { SdkEventBus } from '../sdkEventBus';

interface TestState {
  handledCount: number;
}

class TestController extends BusAwareController<TestState> {
  constructor(options: { scopeKey: string; bus: SdkEventBus }) {
    super({
      initialSnapshot: { handledCount: 0 },
      scopeKey: options.scopeKey,
      bus: options.bus,
    });
  }

  start(): void {
    this.subscribeToBus(() => {
      const snapshot = this.getSnapshot();
      this.setSnapshot({ handledCount: snapshot.handledCount + 1 });
    });
  }
}

describe('BusAwareController', () => {
  it('does not replay old bus events when a controller starts listening', () => {
    const bus = new SdkEventBus();

    bus.emit({
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });

    const controller = new TestController({ scopeKey: 'conn-1', bus });
    controller.start();

    expect(controller.getSnapshot().handledCount).toBe(0);

    bus.emit({
      type: 'session.agent.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });

    expect(controller.getSnapshot().handledCount).toBe(1);
  });

  it('unsubscribes from the bus on dispose', () => {
    const bus = new SdkEventBus();
    const controller = new TestController({ scopeKey: 'conn-1', bus });

    controller.start();
    bus.emit({
      type: 'session.plugins.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });
    controller.dispose();
    bus.emit({
      type: 'session.overrides.changed',
      scopeKey: 'conn-1',
      sessionId: 's1',
    });

    expect(controller.getSnapshot().handledCount).toBe(1);
  });
});
