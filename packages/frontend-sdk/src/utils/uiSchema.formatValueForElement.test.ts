import { describe, expect, it, vi } from 'vitest';

import { formatValueForElement } from './uiSchema';

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
