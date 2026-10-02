import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { ScrollView, StyleSheet, Text } from 'react-native';
import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  DISPLAY_TYPOGRAPHY_PRESETS,
  MARKDOWN_BASE_FONT_SIZES,
  MarkdownDisplayPreferencesProvider,
  deriveMarkdownTypography,
} from '@crystal-lattice/frontend-rn-components';

import MarkdownMessageContent, {
  createDesktopMarkdownTypographyStyles,
} from '../src/chat/MarkdownMessageContent';
import SyntaxHighlighter from '../src/chat/NativeSyntaxHighlighter';

describe('desktop markdown typography adapter', () => {
  it('uses the shared mobile-equivalent default', () => {
    const expected = deriveMarkdownTypography(
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
    );
    expect(
      createDesktopMarkdownTypographyStyles(
        DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
      ),
    ).toMatchObject({
      text: {
        fontSize: expected.body,
        lineHeight: expected.bodyLineHeight,
      },
      heading1: {
        fontSize: expected.h1,
        lineHeight: expected.h1LineHeight,
      },
      heading2: {
        fontSize: expected.h2,
        lineHeight: expected.h2LineHeight,
      },
      heading3: {
        fontSize: expected.h3,
        lineHeight: expected.h3LineHeight,
      },
      heading4: {
        fontSize: expected.h4,
        lineHeight: expected.h4LineHeight,
      },
      heading5: {
        fontSize: expected.h5,
        lineHeight: expected.h5LineHeight,
      },
      heading6: {
        fontSize: expected.h6,
        lineHeight: expected.h6LineHeight,
      },
    });
  });

  it.each(MARKDOWN_BASE_FONT_SIZES)(
    'uses body size for all Small headings at base %s',
    (baseFontSize) => {
      const styles = createDesktopMarkdownTypographyStyles({
        baseFontSize,
        headerSize: 'small',
      });
      expect([
        styles.heading1.fontSize,
        styles.heading2.fontSize,
        styles.heading3.fontSize,
        styles.heading4.fontSize,
        styles.heading5.fontSize,
        styles.heading6.fontSize,
      ]).toEqual(Array(6).fill(baseFontSize));
    },
  );

  it.each(['normal', 'small'] as const)(
    'applies the %s heading size at the final markdown renderer boundary',
    (headerSize) => {
      const preferences = {
        ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
        headerSize,
      };
      const expectedFontSize =
        deriveMarkdownTypography(preferences).h1;
      let renderer: ReactTestRenderer.ReactTestRenderer;
      ReactTestRenderer.act(() => {
        renderer = ReactTestRenderer.create(
          <MarkdownDisplayPreferencesProvider
            value={preferences}
          >
            <MarkdownMessageContent text="# Rendered heading" />
          </MarkdownDisplayPreferencesProvider>,
        );
      });
      const headingText = renderer!.root
        .findAllByType(Text)
        .find((node) => node.props.children === 'Rendered heading');
      expect(headingText).toBeDefined();
      expect(StyleSheet.flatten(headingText!.props.style).fontSize).toBe(
        expectedFontSize,
      );
    },
  );

  it('passes the code typography directly to the native syntax highlighter', () => {
    let renderer: ReactTestRenderer.ReactTestRenderer;
    ReactTestRenderer.act(() => {
      renderer = ReactTestRenderer.create(
        <MarkdownMessageContent text={'```typescript\nconst value = 1;\n```'} />,
      );
    });

    const highlighter = renderer!.root.findByType(SyntaxHighlighter);
    const defaultPreset =
      DISPLAY_TYPOGRAPHY_PRESETS[
        DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize
      ];
    expect(highlighter.props.fontFamily).toBe('Menlo');
    expect(highlighter.props.fontSize).toBe(defaultPreset.fontSize.code);
    expect(highlighter.props.lineHeight).toBe(defaultPreset.lineHeight.code);
    const selectableCode = highlighter.props.CodeTag({
      children: 'const value = 1;',
    });
    expect(selectableCode.props.selectable).toBe(true);
    const codeBlock = renderer!.root.findByProps({
      testID: 'desktop-markdown-code-block',
    });
    expect(codeBlock.findAllByType(ScrollView)).toHaveLength(0);

    const tokenStyles = renderer!.root
      .findAllByType(Text)
      .map((node) => StyleSheet.flatten(node.props.style))
      .filter((style) => style?.fontFamily === 'Menlo');
    expect(tokenStyles).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          fontSize: defaultPreset.fontSize.code,
          lineHeight: defaultPreset.lineHeight.code,
          height: defaultPreset.lineHeight.code,
        }),
      ]),
    );
  });
});