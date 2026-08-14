import { describe, expect, it, vi } from 'vitest';

import {
  acknowledgeApplicationActionsInvalidated,
  emitApplicationActionsInvalidated,
  subscribeApplicationActionsInvalidated,
} from './applicationActionsInvalidation';

describe('application action invalidation', () => {
  it('replays to a late registry until a successful refresh acknowledges it', () => {
    const backend = {} as any;
    emitApplicationActionsInvalidated(backend);
    const late = vi.fn();

    subscribeApplicationActionsInvalidated(backend, late);

    expect(late).toHaveBeenCalledWith(1);
    acknowledgeApplicationActionsInvalidated(backend, 1);
    const later = vi.fn();
    subscribeApplicationActionsInvalidated(backend, later);
    expect(later).not.toHaveBeenCalled();
  });
});