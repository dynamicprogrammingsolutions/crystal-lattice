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

  it('stable-sorts combined base and extra actions by numeric order', () => {
    const model = buildActionsMenuModel({
      baseActions: [
        { key: 'reload', label: 'Reload', order: 0 },
        { key: 'settings', label: 'Settings', order: 90 },
        { key: 'unordered-base', label: 'Unordered base' },
      ],
      extraActions: [
        { key: 'copy', label: 'Copy session', order: 10 },
        { key: 'edit', label: 'Edit title', order: 15 },
        { key: 'same-a', label: 'Same A', order: 40 },
        { key: 'same-b', label: 'Same B', order: 40 },
        { key: 'unordered-extra', label: 'Unordered extra' },
      ],
      pinned: [],
    });

    expect(model.orderedActions.map((def) => def.key)).toEqual([
      'reload',
      'copy',
      'edit',
      'same-a',
      'same-b',
      'settings',
      'unordered-base',
      'unordered-extra',
    ]);
  });

  it('uses an overriding action definition order without moving equal-order ties', () => {
    const model = buildActionsMenuModel({
      baseActions: [
        { key: 'first', label: 'First', order: 10 },
        { key: 'overridden', label: 'Base', order: 20 },
      ],
      extraActions: [
        { key: 'overridden', label: 'Extra', order: 5 },
        { key: 'last', label: 'Last', order: 10 },
      ],
      pinned: [],
    });

    expect(model.orderedActions.map((def) => `${def.key}:${def.label}`)).toEqual([
      'overridden:Extra',
      'first:First',
      'last:Last',
    ]);
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
