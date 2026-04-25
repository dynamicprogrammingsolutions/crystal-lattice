import { describe, expect, it } from 'vitest';

import type { ActionDisplayPayload } from '../../types/plugins';
import { normalizeActionDisplayForSurface } from '../actionDisplayPolicy';

const DISPLAY: ActionDisplayPayload = {
  format: 'markdown',
  body: 'Hello',
  presentation: 'modal',
};

describe('normalizeActionDisplayForSurface', () => {
  it('drops displays for session list actions on mobile', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: DISPLAY,
        surface: 'session_list_action',
        host: 'mobile',
      }),
    ).toBeNull();
  });

  it('drops displays for session list actions on desktop', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: DISPLAY,
        surface: 'session_list_action',
        host: 'desktop',
      }),
    ).toBeNull();
  });

  it('forces desktop session action displays inline', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: DISPLAY,
        surface: 'session_action',
        host: 'desktop',
      }),
    ).toEqual({
      ...DISPLAY,
      presentation: 'inline',
    });
  });

  it('keeps mobile modal session action displays modal', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: DISPLAY,
        surface: 'session_action',
        host: 'mobile',
      }),
    ).toEqual(DISPLAY);
  });

  it('coerces mobile banner session action displays inline', () => {
    expect(
      normalizeActionDisplayForSurface({
        display: {
          ...DISPLAY,
          presentation: 'banner',
        },
        surface: 'session_action',
        host: 'mobile',
      }),
    ).toEqual({
      ...DISPLAY,
      presentation: 'inline',
    });
  });
});