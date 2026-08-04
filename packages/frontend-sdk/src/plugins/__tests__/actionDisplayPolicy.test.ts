import { describe, expect, it } from 'vitest';

import { normalizeActionDisplayForSurface } from '../actionDisplayPolicy';

const DISPLAY = { format: 'markdown' as const, body: 'Hello' };

describe('normalizeActionDisplayForSurface', () => {
  it.each([
    ['application_action', 'mobile'],
    ['session_action', 'desktop'],
    ['session_list_action', 'mobile'],
    ['message_action', 'desktop'],
  ] as const)('preserves explicit presentation for %s on %s', (surface, host) => {
    expect(
      normalizeActionDisplayForSurface({
        display: { ...DISPLAY, presentation: 'banner' },
        surface,
        host,
      }),
    ).toEqual({ ...DISPLAY, presentation: 'banner' });
  });

  it('defaults mobile direct action responses to modal', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: DISPLAY,
        surface: 'session_list_action',
        host: 'mobile',
      }),
    ).toEqual({ ...DISPLAY, presentation: 'modal' });
  });

  it('normalizes desktop modal action responses to inline', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: { ...DISPLAY, presentation: 'modal' },
        surface: 'session_action',
        host: 'desktop',
      }),
    ).toEqual({ ...DISPLAY, presentation: 'inline' });
  });

  it('returns null when no display exists', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: undefined,
        surface: 'application_action',
        host: 'mobile',
      }),
    ).toBeNull();
  });
});