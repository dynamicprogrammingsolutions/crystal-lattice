import { SimpleSubscribable } from '../util/subscribable';
import type { SdkEvent } from './sdkEvent';

export interface SdkEventBusSnapshot {
  seq: number;
  lastEvent: SdkEvent | null;
}

const INITIAL_SNAPSHOT: SdkEventBusSnapshot = {
  seq: 0,
  lastEvent: null,
};

export class SdkEventBus extends SimpleSubscribable<SdkEventBusSnapshot> {
  constructor(initial: SdkEventBusSnapshot = INITIAL_SNAPSHOT) {
    super(initial);
  }

  emit(ev: SdkEvent): void {
    const current = this.getSnapshot();
    this.setSnapshot({
      seq: current.seq + 1,
      lastEvent: ev,
    });
  }
}
