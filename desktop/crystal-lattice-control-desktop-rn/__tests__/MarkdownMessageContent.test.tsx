import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { StyleSheet, Text } from 'react-native';
import {
  MarkdownDisplayPreferencesProvider,
} from '@crystal-lattice/frontend-rn-components';

import MarkdownMessageContent, {
  createDesktopMarkdownTypographyStyles,
} from '../src/chat/MarkdownMessageContent';

describe('desktop markdown typography adapter', () => {
  it('uses the shared mobile-equivalent default', () => {
    expect(
      createDesktopMarkdownTypographyStyles({
        baseFontSize: 15,
        headerSize: 'normal',
      }),
    ).toMatchObject({
      text: { fontSize: 15, lineHeight: 21 },
      heading1: { fontSize: 32, lineHeight: 38 },
      heading2: { fontSize: 24, lineHeight: 29 },
      heading3: { fontSize: 18, lineHeight: 23 },
      heading4: { fontSize: 15, lineHeight: 21 },
      heading5: { fontSize: 15, lineHeight: 21 },
      heading6: { fontSize: 15, lineHeight: 21 },
    });
  });

  it.each([14, 15, 16, 17] as const)(
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

  it.each([
    ['normal', 32],
    ['small', 15],
  ] as const)(
    'applies the %s heading size at the final markdown renderer boundary',
    (headerSize, expectedFontSize) => {
      let renderer: ReactTestRenderer.ReactTestRenderer;
      ReactTestRenderer.act(() => {
        renderer = ReactTestRenderer.create(
          <MarkdownDisplayPreferencesProvider
            value={{ baseFontSize: 15, headerSize }}
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
});