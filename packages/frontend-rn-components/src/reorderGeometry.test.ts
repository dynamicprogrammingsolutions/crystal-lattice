import { describe, expect, it } from 'vitest';

import {
  buildReorderRenderSlots,
  moveReorderValues,
  resolveReorderDropTarget,
  resolveReorderDropTranslation,
  type ReorderItemFrame,
} from './reorderGeometry';

const frames: ReorderItemFrame[] = [
  { x: 0, y: 0, width: 100, height: 60 },
  { x: 110, y: 0, width: 100, height: 60 },
  { x: 0, y: 70, width: 100, height: 80 },
];

describe('portable reorder geometry', () => {
  it('resolves measured targets and target translations', () => {
    expect(resolveReorderDropTarget(frames, 0, 0, 90)).toBe(2);
    expect(resolveReorderDropTranslation(frames, 0, 2)).toEqual({
      x: 0,
      y: 70,
    });
  });

  it('keeps the responder-owning child stable while previewing', () => {
    const items = ['a', 'b', 'c'];
    expect(moveReorderValues(items, 0, 2)).toEqual(['b', 'c', 'a']);
    expect(buildReorderRenderSlots(items, 0, 2)).toEqual([
      { kind: 'dragged', item: 'a' },
      { kind: 'item', item: 'b' },
      { kind: 'item', item: 'c' },
      { kind: 'placeholder' },
    ]);
  });
});
