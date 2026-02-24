import { describe, expect, it } from 'vitest';

import type { ConfigSchemaEntry, UiSchemaElement } from '@crystal-lattice/frontend-sdk';

import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  filterConfigUiSchemaElements,
} from './logic';

describe('filterConfigUiSchemaElements', () => {
  it('keeps only config (or missing ui_type) with non-empty key', () => {
    const elements = [
      { key: 'a', ui_type: 'config' },
      { key: 'b' },
      { key: 'c', ui_type: '' },
      { key: 'd', ui_type: 'other' },
      { key: '' },
      { ui_type: 'config' },
    ] as UiSchemaElement[];

    const filtered = filterConfigUiSchemaElements(elements);
    const keys = filtered.map((element: any) => element.key);
    expect(keys).toEqual(['a', 'b', 'c']);
  });
});

describe('buildConfigSchemaByKey', () => {
  it('indexes entries by key (first wins)', () => {
    const schema = [
      { key: 'a', default: 1 },
      { key: 'a', default: 2 },
      { key: 'b', default: 3 },
      { key: '' },
      {} as any,
    ] as ConfigSchemaEntry[];

    const byKey = buildConfigSchemaByKey(schema);
    expect(byKey.a.default).toBe(1);
    expect(byKey.b.default).toBe(3);
    expect((byKey as any)['']).toBeUndefined();
  });
});

describe('buildSessionSettingItems', () => {
  it('resolves effective values and tag labels with correct precedence', () => {
    const elements = [
      { key: 'a', label: 'A', type: 'checkbox' },
      { key: 'b' },
      { key: 'c', type: 'select' },
      { key: 'd', type: 'text' },
    ] as UiSchemaElement[];

    const schemaByKey = buildConfigSchemaByKey([
      { key: 'b', default: 'bDefault' },
      { key: 'c', default: 'cDefault' },
    ] as ConfigSchemaEntry[]);

    const items = buildSessionSettingItems({
      elements,
      overrides: { a: true },
      baseConfig: { c: 'cBase' },
      schemaByKey,
    });

    expect(items.map((item) => item.key)).toEqual(['a', 'b', 'c', 'd']);

    const itemA = items[0];
    expect(itemA.type).toBe('checkbox');
    expect(itemA.label).toBe('A');
    expect(itemA.source).toBe('override');
    expect(itemA.tagLabel).toBeNull();
    expect(itemA.effectiveValue).toBe(true);

    const itemB = items[1];
    expect(itemB.type).toBe('text');
    expect(itemB.label).toBe('b');
    expect(itemB.source).toBe('schema_default');
    expect(itemB.tagLabel).toBe('default');
    expect(itemB.effectiveValue).toBe('bDefault');

    const itemC = items[2];
    expect(itemC.type).toBe('select');
    expect(itemC.source).toBe('config');
    expect(itemC.tagLabel).toBe('config');
    expect(itemC.effectiveValue).toBe('cBase');

    const itemD = items[3];
    expect(itemD.type).toBe('text');
    expect(itemD.source).toBe('none');
    expect(itemD.tagLabel).toBeNull();
    expect(itemD.effectiveValue).toBeUndefined();
  });
});
