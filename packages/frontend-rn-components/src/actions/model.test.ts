import { describe, expect, it } from 'vitest';

import type { ActionDefinition } from './types';
import { buildActionsMenuModel, togglePinnedKey } from './model';

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

    expect(model.visiblePinned.map((def) => def.key)).toEqual(['c', 'a']);
    expect(model.visibleOverflow.map((def) => def.key)).toEqual(['b']);
  });
});
