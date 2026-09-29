import { describe, expect, it } from 'vitest';

import type { Theme } from './theme';
import {
  CODE_BLOCK_RENDERER_OPTIONS,
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  DISPLAY_TYPOGRAPHY_PRESETS,
  MARKDOWN_BASE_FONT_SIZES,
  MARKDOWN_RENDERER_OPTIONS,
  applyDisplayTypographyPreset,
  deriveMarkdownTypography,
  normalizeCodeBlockRendererId,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownDisplayPreferences,
  normalizeMarkdownHeaderSize,
  normalizeMarkdownRendererId,
  resolveMarkdownRendererPreferences,
} from './markdownDisplayPreferences';

const SUPPORTED_SIZES = MARKDOWN_BASE_FONT_SIZES;
const BASE_THEME = {
  typography:
    DISPLAY_TYPOGRAPHY_PRESETS[
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize
    ],
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

  it.each([
    undefined,
    null,
    Number.MIN_SAFE_INTEGER,
    Number.MAX_SAFE_INTEGER,
    'unsupported',
    {},
    [],
  ])(
    'defaults unsupported base size %j',
    (value) => {
      expect(normalizeMarkdownBaseFontSize(value)).toBe(
        DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize,
      );
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

  it.each([
    'react-native-markdown-display',
    'react-native-enriched-markdown',
  ] as const)('accepts markdown renderer %s', (value) => {
    expect(normalizeMarkdownRendererId(value)).toBe(value);
  });

  it.each([
    undefined,
    null,
    'unsupported',
    15,
    {},
    [],
  ])('defaults unsupported markdown renderer %j', (value) => {
    expect(normalizeMarkdownRendererId(value)).toBe(
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.markdownRenderer,
    );
  });

  it.each([
    'selectable-native',
    'syntax-highlighter',
  ] as const)('accepts code renderer %s', (value) => {
    expect(normalizeCodeBlockRendererId(value)).toBe(value);
  });

  it.each([
    undefined,
    null,
    'unsupported',
    15,
    {},
    [],
  ])('defaults unsupported code renderer %j', (value) => {
    expect(normalizeCodeBlockRendererId(value)).toBe(
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.codeBlockRenderer,
    );
  });

  it('normalizes fields independently', () => {
    expect(
      normalizeMarkdownDisplayPreferences({
        baseFontSize: SUPPORTED_SIZES[SUPPORTED_SIZES.length - 1],
        headerSize: 'invalid',
        markdownRenderer: 'react-native-enriched-markdown',
        codeBlockRenderer: 'invalid',
      }),
    ).toEqual({
      baseFontSize: SUPPORTED_SIZES[SUPPORTED_SIZES.length - 1],
      headerSize: 'normal',
      markdownRenderer: 'react-native-enriched-markdown',
      codeBlockRenderer: 'selectable-native',
    });
    expect(
      normalizeMarkdownDisplayPreferences({
        baseFontSize: Number.MIN_SAFE_INTEGER,
        headerSize: 'small',
        markdownRenderer: 'invalid',
        codeBlockRenderer: 'syntax-highlighter',
      }),
    ).toEqual({
      baseFontSize: DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize,
      headerSize: 'small',
      markdownRenderer: 'react-native-markdown-display',
      codeBlockRenderer: 'syntax-highlighter',
    });
    expect(normalizeMarkdownDisplayPreferences(null)).toEqual(
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
    );
  });

  it('defines stable user-facing renderer labels', () => {
    expect(MARKDOWN_RENDERER_OPTIONS).toEqual([
      {
        value: 'react-native-markdown-display',
        label: 'React Native Markdown Display',
      },
      {
        value: 'react-native-enriched-markdown',
        label: 'Enriched Markdown (experimental)',
      },
    ]);
    expect(CODE_BLOCK_RENDERER_OPTIONS).toEqual([
      {
        value: 'selectable-native',
        label: 'Selectable native code',
      },
      {
        value: 'syntax-highlighter',
        label: 'Syntax highlighter',
      },
    ]);
  });
});

describe('markdown renderer capability resolution', () => {
  it('uses requested renderers when their optional capabilities are present', () => {
    expect(
      resolveMarkdownRendererPreferences(
        {
          ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
          markdownRenderer: 'react-native-enriched-markdown',
        },
        {
          enrichedMarkdown: true,
          selectableNativeCode: true,
        },
      ),
    ).toEqual({
      markdownRenderer: 'react-native-enriched-markdown',
      codeBlockRenderer: 'selectable-native',
      markdownRendererFellBack: false,
      codeBlockRendererFellBack: false,
    });
  });

  it('falls back without changing the requested preferences', () => {
    const requested = {
      ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
      markdownRenderer: 'react-native-enriched-markdown' as const,
      codeBlockRenderer: 'selectable-native' as const,
    };

    expect(
      resolveMarkdownRendererPreferences(requested, {
        enrichedMarkdown: false,
        selectableNativeCode: false,
      }),
    ).toEqual({
      markdownRenderer: 'react-native-markdown-display',
      codeBlockRenderer: 'syntax-highlighter',
      markdownRendererFellBack: true,
      codeBlockRendererFellBack: true,
    });
    expect(requested).toEqual({
      ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
      markdownRenderer: 'react-native-enriched-markdown',
      codeBlockRenderer: 'selectable-native',
    });
  });
});

describe('display typography presets', () => {
  it('defines every responsive font size and line height explicitly', () => {
    expect(Object.keys(DISPLAY_TYPOGRAPHY_PRESETS).map(Number)).toEqual([
      ...SUPPORTED_SIZES,
    ]);
    const reference =
      DISPLAY_TYPOGRAPHY_PRESETS[SUPPORTED_SIZES[0]];
    const fontSizeRoles = Object.keys(reference.fontSize);
    const lineHeightRoles = Object.keys(reference.lineHeight);

    for (const baseFontSize of SUPPORTED_SIZES) {
      const preset = DISPLAY_TYPOGRAPHY_PRESETS[baseFontSize];
      expect(Object.keys(preset.fontSize)).toEqual(fontSizeRoles);
      expect(Object.keys(preset.lineHeight)).toEqual(lineHeightRoles);
      for (const role of fontSizeRoles) {
        const fontSize =
          preset.fontSize[role as keyof typeof preset.fontSize];
        const lineHeight =
          preset.lineHeight[role as keyof typeof preset.lineHeight];
        expect(Number.isFinite(fontSize)).toBe(true);
        expect(Number.isFinite(lineHeight)).toBe(true);
        expect(fontSize).toBeGreaterThan(0);
        expect(lineHeight).toBeGreaterThanOrEqual(fontSize);
      }
    }
  });

  it.each(SUPPORTED_SIZES)('overlays preset %s without changing colors', (baseFontSize) => {
    const result = applyDisplayTypographyPreset(BASE_THEME, baseFontSize);
    expect(result.typography).toEqual(DISPLAY_TYPOGRAPHY_PRESETS[baseFontSize]);
    expect(result.background).toBe(BASE_THEME.background);
    expect(result.primary).toBe(BASE_THEME.primary);
  });
});

describe('deriveMarkdownTypography', () => {
  it.each(SUPPORTED_SIZES)(
    'derives the approved normal hierarchy for base %s',
    (baseFontSize) => {
      const typography = deriveMarkdownTypography({
        baseFontSize,
        headerSize: 'normal',
      });
      expect(typography.body).toBe(baseFontSize);
      expect(typography.bodyLineHeight).toBeGreaterThanOrEqual(typography.body);
      expect(typography.h1).toBeGreaterThan(typography.h2);
      expect(typography.h2).toBeGreaterThan(typography.h3);
      expect(typography.h3).toBeGreaterThanOrEqual(typography.body);
      expect([
        typography.h4,
        typography.h5,
        typography.h6,
      ]).toEqual(Array(3).fill(typography.body));
      const lowerHeadingLineHeights = [
        typography.h4LineHeight,
        typography.h5LineHeight,
        typography.h6LineHeight,
      ];
      expect(lowerHeadingLineHeights).toEqual(
        Array(3).fill(lowerHeadingLineHeights[0]),
      );
      expect(lowerHeadingLineHeights[0]).toBeGreaterThanOrEqual(
        typography.body,
      );
      for (const [fontSize, lineHeight] of [
        [typography.h1, typography.h1LineHeight],
        [typography.h2, typography.h2LineHeight],
        [typography.h3, typography.h3LineHeight],
      ]) {
        expect(lineHeight).toBeGreaterThanOrEqual(fontSize);
      }
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