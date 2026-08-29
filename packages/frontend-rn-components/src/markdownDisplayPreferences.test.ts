import { describe, expect, it } from 'vitest';

import type { Theme } from './theme';
import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  DISPLAY_TYPOGRAPHY_PRESETS,
  applyDisplayTypographyPreset,
  deriveMarkdownTypography,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownDisplayPreferences,
  normalizeMarkdownHeaderSize,
  type MarkdownBaseFontSize,
} from './markdownDisplayPreferences';

const SUPPORTED_SIZES = [14, 15, 16, 17] as const;
const BASE_THEME = {
  typography: DISPLAY_TYPOGRAPHY_PRESETS[15],
  background: '#background',
  primary: '#primary',
} as Theme;

describe('markdown display preference normalization', () => {
  it.each(SUPPORTED_SIZES)('accepts supported base size %s', (value) => {
    expect(normalizeMarkdownBaseFontSize(value)).toBe(value);
  });

  it.each([
    [13, 14],
    [19, 17],
  ] as const)('migrates legacy base size %s to %s', (value, expected) => {
    expect(normalizeMarkdownBaseFontSize(value)).toBe(expected);
  });

  it.each([undefined, null, 12, 18, 15.5, '15', {}, []])(
    'defaults unsupported base size %j',
    (value) => {
      expect(normalizeMarkdownBaseFontSize(value)).toBe(15);
    },
  );

  it.each(['normal', 'small'] as const)('accepts header size %s', (value) => {
    expect(normalizeMarkdownHeaderSize(value)).toBe(value);
  });

  it.each([undefined, null, 'large', 15, {}, []])(
    'defaults unsupported header size %j',
    (value) => {
      expect(normalizeMarkdownHeaderSize(value)).toBe('normal');
    },
  );

  it('normalizes fields independently', () => {
    expect(
      normalizeMarkdownDisplayPreferences({
        baseFontSize: 17,
        headerSize: 'invalid',
      }),
    ).toEqual({ baseFontSize: 17, headerSize: 'normal' });
    expect(
      normalizeMarkdownDisplayPreferences({
        baseFontSize: 12,
        headerSize: 'small',
      }),
    ).toEqual({ baseFontSize: 15, headerSize: 'small' });
    expect(normalizeMarkdownDisplayPreferences(null)).toEqual(
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
    );
  });
});

describe('display typography presets', () => {
  it('defines every responsive font size and line height explicitly', () => {
    expect(DISPLAY_TYPOGRAPHY_PRESETS).toEqual({
      14: {
        fontSize: {
          tiny: 11, small: 12, secondary: 13, normal: 14, message: 14,
          large: 16, title: 18, screenTitle: 24, display: 28, code: 14,
        },
        lineHeight: {
          tiny: 15, small: 17, secondary: 18, normal: 20, message: 20,
          large: 22, title: 24, screenTitle: 30, display: 34, code: 19,
        },
      },
      15: {
        fontSize: {
          tiny: 11, small: 12, secondary: 13, normal: 14, message: 15,
          large: 16, title: 18, screenTitle: 24, display: 28, code: 14,
        },
        lineHeight: {
          tiny: 15, small: 17, secondary: 18, normal: 20, message: 21,
          large: 22, title: 24, screenTitle: 30, display: 34, code: 19,
        },
      },
      16: {
        fontSize: {
          tiny: 12, small: 13, secondary: 14, normal: 15, message: 16,
          large: 16, title: 18, screenTitle: 24, display: 28, code: 15,
        },
        lineHeight: {
          tiny: 17, small: 18, secondary: 20, normal: 21, message: 23,
          large: 22, title: 24, screenTitle: 30, display: 34, code: 21,
        },
      },
      17: {
        fontSize: {
          tiny: 13, small: 14, secondary: 15, normal: 16, message: 17,
          large: 17, title: 18, screenTitle: 24, display: 28, code: 16,
        },
        lineHeight: {
          tiny: 18, small: 20, secondary: 21, normal: 23, message: 24,
          large: 24, title: 24, screenTitle: 30, display: 34, code: 22,
        },
      },
    });
  });

  it.each(SUPPORTED_SIZES)('overlays preset %s without changing colors', (baseFontSize) => {
    const result = applyDisplayTypographyPreset(BASE_THEME, baseFontSize);
    expect(result.typography).toEqual(DISPLAY_TYPOGRAPHY_PRESETS[baseFontSize]);
    expect(result.background).toBe(BASE_THEME.background);
    expect(result.primary).toBe(BASE_THEME.primary);
  });
});

describe('deriveMarkdownTypography', () => {
  const normalExpected: Record<MarkdownBaseFontSize, number[]> = {
    14: [14, 20, 30, 36, 22, 27, 17, 22, 14, 20, 14, 20, 14, 20],
    15: [15, 21, 32, 38, 24, 29, 18, 23, 15, 21, 15, 21, 15, 21],
    16: [16, 23, 34, 41, 26, 32, 19, 24, 16, 23, 16, 23, 16, 23],
    17: [17, 24, 36, 43, 27, 33, 20, 25, 17, 24, 17, 24, 17, 24],
  };

  it.each(SUPPORTED_SIZES)(
    'derives the approved normal hierarchy for base %s',
    (baseFontSize) => {
      expect(
        Object.values(
          deriveMarkdownTypography({
            baseFontSize,
            headerSize: 'normal',
          }),
        ),
      ).toEqual(normalExpected[baseFontSize]);
    },
  );

  it.each(SUPPORTED_SIZES)(
    'uses message metrics for every small heading at base %s',
    (baseFontSize) => {
      const typography = deriveMarkdownTypography({
        baseFontSize,
        headerSize: 'small',
      });
      const preset = DISPLAY_TYPOGRAPHY_PRESETS[baseFontSize];
      expect(typography.body).toBe(baseFontSize);
      expect(typography.bodyLineHeight).toBe(preset.lineHeight.message);
      expect([
        typography.h1,
        typography.h2,
        typography.h3,
        typography.h4,
        typography.h5,
        typography.h6,
      ]).toEqual(Array(6).fill(baseFontSize));
      expect([
        typography.h1LineHeight,
        typography.h2LineHeight,
        typography.h3LineHeight,
        typography.h4LineHeight,
        typography.h5LineHeight,
        typography.h6LineHeight,
      ]).toEqual(Array(6).fill(preset.lineHeight.message));
    },
  );
});