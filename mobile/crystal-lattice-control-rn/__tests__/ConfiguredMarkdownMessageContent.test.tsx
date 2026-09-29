import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MarkdownDisplayPreferencesProvider,
  type CodeBlockRendererId,
  type MarkdownRendererId,
} from '@crystal-lattice/frontend-rn-components';

import ConfiguredMarkdownMessageContent from '../src/components/ConfiguredMarkdownMessageContent';
import { ThemeProvider, lightTheme } from '../src/theme';

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
) {
  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ThemeProvider theme={lightTheme}>
        <MarkdownDisplayPreferencesProvider
          value={{
            ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
            markdownRenderer,
            codeBlockRenderer,
          }}
        >
          <ConfiguredMarkdownMessageContent
            text={MARKDOWN_WITH_CODE}
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