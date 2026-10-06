import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { StyleSheet } from 'react-native';
import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MarkdownDisplayPreferencesProvider,
  type CodeBlockRendererId,
  type MarkdownRendererId,
  type Theme,
} from '@crystal-lattice/frontend-rn-components';

import ConfiguredMarkdownMessageContent from '../src/components/ConfiguredMarkdownMessageContent';
import { darkTheme, ThemeProvider, lightTheme } from '../src/theme';

const MARKDOWN_WITH_CODE = [
  'Intro paragraph.',
  '',
  '```typescript',
  'const configured = true;',
  '```',
].join('\n');

function renderConfiguredMarkdown(
  markdownRenderer: MarkdownRendererId,
  codeBlockRenderer: CodeBlockRendererId,
  options: {
    theme?: Theme;
    variant?: 'assistant' | 'user';
    text?: string;
  } = {},
) {
  const theme = options.theme ?? lightTheme;
  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ThemeProvider theme={theme}>
        <MarkdownDisplayPreferencesProvider
          value={{
            ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
            markdownRenderer,
            codeBlockRenderer,
          }}
        >
          <ConfiguredMarkdownMessageContent
            text={options.text ?? MARKDOWN_WITH_CODE}
            variant={options.variant}
            testID="configured-markdown"
          />
        </MarkdownDisplayPreferencesProvider>
      </ThemeProvider>,
    );
  });
  return renderer!;
}

test.each([
  ['react-native-markdown-display', 'selectable-native'],
  ['react-native-markdown-display', 'syntax-highlighter'],
  ['react-native-enriched-markdown', 'selectable-native'],
  ['react-native-enriched-markdown', 'syntax-highlighter'],
] as const)(
  'uses markdown renderer %s with code renderer %s',
  (markdownRenderer, codeBlockRenderer) => {
    const renderer = renderConfiguredMarkdown(
      markdownRenderer,
      codeBlockRenderer,
    );

    expect(
      renderer.root.findByProps({
        testID: `configured-markdown-${markdownRenderer}`,
      }),
    ).toBeTruthy();

    const enrichedMarkdown = renderer.root.findAll(
      (node) => String(node.type) === 'EnrichedMarkdownText',
    );
    const selectableCode = renderer.root.findAll(
      (node) => String(node.type) === 'SelectableCodeBlockView',
    );
    const syntaxHighlighters = renderer.root.findAll(
      (node) => String(node.type) === 'SyntaxHighlighter',
    );

    expect(enrichedMarkdown.length > 0).toBe(
      markdownRenderer === 'react-native-enriched-markdown',
    );
    if (markdownRenderer === 'react-native-markdown-display') {
      const markdownDisplay = renderer.root.find(
        (node) => typeof node.props.rules?.fence === 'function',
      );
      const configuredCodeElement = markdownDisplay.props.rules.fence({
        key: 'code',
        lang: 'typescript',
        content: 'const configured = true;\n',
      });
      expect(configuredCodeElement.props.renderer).toBe(codeBlockRenderer);
      expect(selectableCode).toHaveLength(0);
      expect(syntaxHighlighters).toHaveLength(0);
    } else {
      expect(selectableCode.length > 0).toBe(
        codeBlockRenderer === 'selectable-native',
      );
      expect(syntaxHighlighters.length > 0).toBe(
        codeBlockRenderer === 'syntax-highlighter',
      );
    }
  },
);

test.each([
  ['light', lightTheme],
  ['dark', darkTheme],
] as const)(
  'uses bubbleUserText for both user markdown renderers in %s theme',
  (_name, theme) => {
    const text = 'User **text** with `inline code` and [link](https://example.com).';
    const classic = renderConfiguredMarkdown(
      'react-native-markdown-display',
      'syntax-highlighter',
      { theme, variant: 'user', text },
    );
    const classicMarkdown = classic.root.find(
      node => typeof node.props.rules?.code_inline === 'function',
    );
    expect(classicMarkdown.props.style.body.color).toBe(theme.bubbleUserText);
    expect(classicMarkdown.props.style.text.color).toBe(theme.bubbleUserText);
    const inlineCode = classicMarkdown.props.rules.code_inline(
      { key: 'inline', content: 'inline code' },
      [],
    );
    expect(StyleSheet.flatten(inlineCode.props.style).color).toBe(
      theme.bubbleUserText,
    );

    const selectable = renderConfiguredMarkdown(
      'react-native-enriched-markdown',
      'selectable-native',
      { theme, variant: 'user', text },
    );
    const enrichedMarkdown = selectable.root.find(
      node => String(node.type) === 'EnrichedMarkdownText',
    );
    expect(enrichedMarkdown.props.markdownStyle.paragraph.color).toBe(
      theme.bubbleUserText,
    );
    expect(enrichedMarkdown.props.markdownStyle.list.bulletColor).toBe(
      theme.bubbleUserText,
    );
    expect(enrichedMarkdown.props.markdownStyle.list.markerColor).toBe(
      theme.bubbleUserText,
    );
    expect(enrichedMarkdown.props.markdownStyle.code.color).toBe(
      theme.bubbleUserText,
    );
    expect(enrichedMarkdown.props.markdownStyle.link.color).toBe(
      theme.bubbleUserText,
    );
  },
);