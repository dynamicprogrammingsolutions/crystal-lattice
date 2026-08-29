import { describe, expect, it } from 'vitest';

import type { ActionDefinition } from './types';
import {
  buildActionsMenuModel,
  limitPinnedActionsForBar,
  togglePinnedKey,
} from './model';

describe('togglePinnedKey', () => {
  it('adds missing key', () => {
    expect(togglePinnedKey(['a'], 'b')).toEqual(['a', 'b']);
  });

  it('removes existing key', () => {
    expect(togglePinnedKey(['a', 'b'], 'b')).toEqual(['a']);
  });
});

describe('buildActionsMenuModel', () => {
  it('filters base actions by availableActions but keeps extraActions', () => {
    const base: ActionDefinition[] = [
      { key: 'a', label: 'A' },
      { key: 'b', label: 'B' },
    ];
    const extra: ActionDefinition[] = [{ key: 'x', label: 'X' }];
    const model = buildActionsMenuModel({
      baseActions: base,
      extraActions: extra,
      availableActions: ['b'],
      pinned: [],
    });

    expect(model.orderedActions.map((def) => def.key)).toEqual(['b', 'x']);
  });

  it('computes pinned and overflow lists', () => {
    const base: ActionDefinition[] = [
      { key: 'a', label: 'A' },
      { key: 'b', label: 'B' },
      { key: 'c', label: 'C' },
    ];

    const model = buildActionsMenuModel({
      baseActions: base,
      pinned: ['c', 'missing', 'a'],
    });

    expect(model.visiblePinned.map((def) => def.key)).toEqual(['a', 'c']);
    expect(model.visibleOverflow.map((def) => def.key)).toEqual(['b']);
  });
});

describe('limitPinnedActionsForBar', () => {
  it('limits only the compact representation without changing the source set', () => {
    const pinned = ['one', 'two', 'three', 'four'];
    const visible = limitPinnedActionsForBar(pinned, 2);

    expect(visible).toEqual(['one', 'two']);
    expect(pinned).toEqual(['one', 'two', 'three', 'four']);
  });

  it('normalizes fractional and negative limits and preserves an unlimited set', () => {
    const pinned = ['one', 'two', 'three'];

    expect(limitPinnedActionsForBar(pinned, 2.9)).toEqual(['one', 'two']);
    expect(limitPinnedActionsForBar(pinned, -1)).toEqual([]);
    expect(limitPinnedActionsForBar(pinned, undefined)).toBe(pinned);
  });
});
