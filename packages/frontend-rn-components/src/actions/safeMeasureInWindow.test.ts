import { describe, expect, it, vi } from 'vitest';

import { safeMeasureInWindow } from './safeMeasureInWindow';

describe('safeMeasureInWindow', () => {
  it('returns false when ref is missing measureInWindow', () => {
    const cb = vi.fn();
    expect(safeMeasureInWindow({}, cb)).toBe(false);
    expect(cb).not.toHaveBeenCalled();
  });

  it('returns false when measureInWindow throws', () => {
    const cb = vi.fn();
    const current = {
      measureInWindow: () => {
        throw new Error('boom');
      },
    };
    expect(safeMeasureInWindow(current, cb)).toBe(false);
    expect(cb).not.toHaveBeenCalled();
  });

  it('invokes callback and returns true when measure works', () => {
    const cb = vi.fn();
    const current = {
      measureInWindow: (fn: (x: number, y: number, w: number, h: number) => void) => {
        fn(1, 2, 3, 4);
      },
    };
    expect(safeMeasureInWindow(current, cb)).toBe(true);
    expect(cb).toHaveBeenCalledWith({ x: 1, y: 2, width: 3, height: 4 });
  });
});
