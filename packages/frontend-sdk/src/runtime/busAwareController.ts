import { SimpleSubscribable, type Unsubscribe } from '../util/subscribable';
import type { SdkEvent } from './sdkEvent';
import type { SdkEventBus } from './sdkEventBus';

export abstract class BusAwareController<T> extends SimpleSubscribable<T> {
  protected readonly scopeKey: string;
  protected readonly bus: SdkEventBus | null;
  protected disposeBusSub?: Unsubscribe;
  protected lastHandledBusSeq: number;

  constructor(options: {
    initialSnapshot: T;
    scopeKey: string;
    bus?: SdkEventBus | null;
  }) {
    super(options.initialSnapshot);
    this.scopeKey = options.scopeKey;
    this.bus = options.bus ?? null;
    this.lastHandledBusSeq = this.bus?.getSnapshot().seq ?? 0;
  }

  protected subscribeToBus(handler: (event: SdkEvent, seq: number) => void): void {
    const bus = this.bus;
    if (!bus) {
      return;
    }

    this.disposeBusSub?.();
    this.disposeBusSub = bus.subscribe(() => {
      const snapshot = bus.getSnapshot();
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
