import { SimpleSubscribable, type Unsubscribe } from '../util/subscribable';
import type { SdkEvent } from './sdkEvent';
import type { SdkEventBus } from './sdkEventBus';

export abstract class BusAwareController<T> extends SimpleSubscribable<T> {
  protected readonly scopeKey: string;
  protected readonly bus: SdkEventBus;
  protected disposeBusSub?: Unsubscribe;
  protected lastHandledBusSeq: number;

  constructor(options: {
    initialSnapshot: T;
    scopeKey: string;
    bus: SdkEventBus;
  }) {
    super(options.initialSnapshot);
    this.scopeKey = options.scopeKey;
    this.bus = options.bus;
    this.lastHandledBusSeq = this.bus.getSnapshot().seq;
  }

  protected subscribeToBus(handler: (event: SdkEvent, seq: number) => void): void {
    this.disposeBusSub?.();
    this.disposeBusSub = this.bus.subscribe(() => {
      const snapshot = this.bus.getSnapshot();
      if (!snapshot.lastEvent || snapshot.seq <= this.lastHandledBusSeq) {
        return;
      }

      this.lastHandledBusSeq = snapshot.seq;
      handler(snapshot.lastEvent, snapshot.seq);
    });
  }

  dispose(): void {
    this.disposeBusSub?.();
    this.disposeBusSub = undefined;
  }
}
