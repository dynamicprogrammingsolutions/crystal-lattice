import { describe, expect, it, vi } from 'vitest';

import { coerceValueForElement, formatValueForElement } from './uiSchema';

describe('formatValueForElement', () => {
  it('formats epoch seconds as a locale datetime string', () => {
    const spy = vi.spyOn(Date.prototype, 'toLocaleString').mockReturnValue('LOCAL');

    const el: any = { ui_type: 'message_footer', metadata: { format: 'datetime' } };
    const out = formatValueForElement(el, 1700000000);

    expect(out).toBe('LOCAL');
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it('formats ISO timestamps as a locale datetime string', () => {
    const spy = vi.spyOn(Date.prototype, 'toLocaleString').mockReturnValue('LOCAL2');

    const el: any = { ui_type: 'message_footer', metadata: { format: 'datetime' } };
    const out = formatValueForElement(el, '2026-02-22T10:11:12.000Z');

    expect(out).toBe('LOCAL2');
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it('leaves invalid ISO timestamps unchanged', () => {
    const el: any = { ui_type: 'message_footer', metadata: { format: 'datetime' } };
    const out = formatValueForElement(el, 'not-a-date');
    expect(out).toBe('not-a-date');
  });
});

describe('coerceValueForElement', () => {
  describe('number type', () => {
    const numberElement = { type: 'number' };

    it('converts string integer to int', () => {
      expect(coerceValueForElement(numberElement, '42')).toBe(42);
      expect(typeof coerceValueForElement(numberElement, '42')).toBe('number');
    });

    it('converts string float to float', () => {
      expect(coerceValueForElement(numberElement, '3.14')).toBe(3.14);
      expect(typeof coerceValueForElement(numberElement, '3.14')).toBe('number');
    });

    it('converts negative string integers', () => {
      expect(coerceValueForElement(numberElement, '-42')).toBe(-42);
    });

    it('converts negative string floats', () => {
      expect(coerceValueForElement(numberElement, '-0.5')).toBe(-0.5);
    });

    it('returns number values unchanged', () => {
      expect(coerceValueForElement(numberElement, 42)).toBe(42);
      expect(coerceValueForElement(numberElement, 3.14)).toBe(3.14);
    });

    it('converts boolean to float', () => {
      expect(coerceValueForElement(numberElement, true)).toBe(1.0);
      expect(coerceValueForElement(numberElement, false)).toBe(0.0);
    });

    it('returns empty string unchanged', () => {
      expect(coerceValueForElement(numberElement, '')).toBe('');
    });

    it('returns whitespace string unchanged', () => {
      expect(coerceValueForElement(numberElement, '   ')).toBe('   ');
    });

    it('returns invalid number string unchanged', () => {
      expect(coerceValueForElement(numberElement, 'not-a-number')).toBe('not-a-number');
    });

    it('trims whitespace before parsing', () => {
      expect(coerceValueForElement(numberElement, '  42  ')).toBe(42);
      expect(coerceValueForElement(numberElement, '  3.14  ')).toBe(3.14);
    });
  });

  describe('boolean type', () => {
    const booleanElement = { type: 'boolean' };
    const checkboxElement = { type: 'checkbox' };

    it('returns boolean values unchanged', () => {
      expect(coerceValueForElement(booleanElement, true)).toBe(true);
      expect(coerceValueForElement(booleanElement, false)).toBe(false);
    });

    it('converts string "true" to true', () => {
      expect(coerceValueForElement(booleanElement, 'true')).toBe(true);
      expect(coerceValueForElement(booleanElement, 'True')).toBe(true);
      expect(coerceValueForElement(booleanElement, 'TRUE')).toBe(true);
    });

    it('converts string "false" to false', () => {
      expect(coerceValueForElement(booleanElement, 'false')).toBe(false);
      expect(coerceValueForElement(booleanElement, 'False')).toBe(false);
      expect(coerceValueForElement(booleanElement, 'FALSE')).toBe(false);
    });

    it('converts "1"/"0" to true/false', () => {
      expect(coerceValueForElement(booleanElement, '1')).toBe(true);
      expect(coerceValueForElement(booleanElement, '0')).toBe(false);
    });

    it('converts "yes"/"no" to true/false', () => {
      expect(coerceValueForElement(booleanElement, 'yes')).toBe(true);
      expect(coerceValueForElement(booleanElement, 'no')).toBe(false);
    });

    it('converts "on"/"off" to true/false', () => {
      expect(coerceValueForElement(booleanElement, 'on')).toBe(true);
      expect(coerceValueForElement(booleanElement, 'off')).toBe(false);
    });

    it('converts empty string to false', () => {
      expect(coerceValueForElement(booleanElement, '')).toBe(false);
    });

    it('converts number to boolean', () => {
      expect(coerceValueForElement(booleanElement, 1)).toBe(true);
      expect(coerceValueForElement(booleanElement, 0)).toBe(false);
      expect(coerceValueForElement(booleanElement, 42)).toBe(true);
    });

    it('returns unknown string unchanged', () => {
      expect(coerceValueForElement(booleanElement, 'maybe')).toBe('maybe');
    });

    it('works with checkbox type same as boolean', () => {
      expect(coerceValueForElement(checkboxElement, 'true')).toBe(true);
      expect(coerceValueForElement(checkboxElement, 'false')).toBe(false);
    });
  });

  describe('text/string type', () => {
    const textElement = { type: 'text' };
    const stringElement = { type: 'string' };

    it('stringifies numbers', () => {
      expect(coerceValueForElement(textElement, 42)).toBe('42');
      expect(coerceValueForElement(stringElement, 42)).toBe('42');
    });

    it('stringifies booleans', () => {
      expect(coerceValueForElement(textElement, true)).toBe('true');
      expect(coerceValueForElement(stringElement, false)).toBe('false');
    });

    it('returns strings unchanged', () => {
      expect(coerceValueForElement(textElement, 'hello')).toBe('hello');
    });

    it('returns null/undefined unchanged', () => {
      expect(coerceValueForElement(textElement, null)).toBe(null);
      expect(coerceValueForElement(textElement, undefined)).toBe(undefined);
    });
  });

  describe('select/dropdown type', () => {
    const selectElement = { type: 'select' };
    const dropdownElement = { type: 'dropdown' };

    it('returns strings unchanged', () => {
      expect(coerceValueForElement(selectElement, '42')).toBe('42');
      expect(coerceValueForElement(dropdownElement, 'option1')).toBe('option1');
    });

    it('returns numbers unchanged', () => {
      expect(coerceValueForElement(selectElement, 42)).toBe(42);
    });
  });

  describe('unknown/missing type', () => {
    const unknownElement = { type: 'unknown' };
    const noTypeElement = {};

    it('returns values unchanged for unknown type', () => {
      expect(coerceValueForElement(unknownElement, '42')).toBe('42');
      expect(coerceValueForElement(unknownElement, 42)).toBe(42);
    });

    it('returns values unchanged for missing type', () => {
      expect(coerceValueForElement(noTypeElement, '42')).toBe('42');
      expect(coerceValueForElement(noTypeElement, 42)).toBe(42);
    });
  });
});
