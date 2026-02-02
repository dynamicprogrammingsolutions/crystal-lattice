export type Unsubscribe = () => void;

export interface Subscribable<T> {
  getSnapshot(): T;
  subscribe(listener: () => void): Unsubscribe;
}

export class SimpleSubscribable<T> implements Subscribable<T> {
  private snapshot: T;
  private listeners: Set<() => void> = new Set();

  constructor(initial: T) {
    this.snapshot = initial;
  }

  getSnapshot(): T {
    return this.snapshot;
  }

  subscribe(listener: () => void): Unsubscribe {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  protected setSnapshot(next: T): void {
    this.snapshot = next;
    for (const listener of this.listeners) {
      listener();
    }
  }
}
