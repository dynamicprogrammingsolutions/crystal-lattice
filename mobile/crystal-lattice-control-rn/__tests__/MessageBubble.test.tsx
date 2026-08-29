import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { StyleSheet } from 'react-native';
import { applyDisplayTypographyPreset } from '@crystal-lattice/frontend-rn-components';

import MessageBubble, {
  createMessageBubbleStyles,
} from '../src/components/MessageBubble';
import { AttachmentThumbnailStrip } from '../src/components/AttachmentThumbnailStrip';
import SelectablePlainText from '../src/components/SelectablePlainText';
import { ThemeProvider, lightTheme } from '../src/theme';


jest.mock('../src/theme', () => {
  const actual = jest.requireActual('../src/theme');
  return {
    ...actual,
    ThemeProvider: ({ children }: any) => <>{children}</>,
    useTheme: () => actual.lightTheme,
  };
});


function renderMessageBubble(message: any, extraProps: Record<string, any> = {}) {
  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ThemeProvider theme={lightTheme}>
        <MessageBubble
          index={0}
          message={message}
          {...extraProps}
        />
      </ThemeProvider>
    );
  });
  return renderer!;
}

function updateMessageBubble(
  renderer: ReactTestRenderer.ReactTestRenderer,
  message: any,
) {
  ReactTestRenderer.act(() => {
    renderer.update(
      <ThemeProvider theme={lightTheme}>
        <MessageBubble
          index={0}
          message={message}
        />
      </ThemeProvider>
    );
  });
}

test.each([
  [14, 11, 15],
  [15, 11, 15],
  [16, 12, 17],
  [17, 13, 18],
] as const)(
  'base size %s gives message footers explicit %s/%s metrics',
  (baseFontSize, footerFontSize, footerLineHeight) => {
    const theme = applyDisplayTypographyPreset(lightTheme, baseFontSize);
    const styles = createMessageBubbleStyles(theme);
    expect(StyleSheet.flatten(styles.footerText)).toMatchObject({
      fontSize: footerFontSize,
      lineHeight: footerLineHeight,
    });
    expect(StyleSheet.flatten(styles.contentText)).toMatchObject({
      fontSize: baseFontSize,
      lineHeight: theme.typography.lineHeight.message,
    });
  },
);


test('system message hides compiled content panel when metadata is absent', () => {
  const renderer = renderMessageBubble({
    role: 'system',
    content: 'Template content',
    metadata: {},
  });

  const toggleButtons = renderer.root.findAllByProps({ testID: 'system-compiled-toggle' });
  const compiledContent = renderer.root.findAllByProps({ testID: 'system-compiled-content' });

  expect(toggleButtons).toHaveLength(0);
  expect(compiledContent).toHaveLength(0);
});


test('system message shows collapsible compiled content when metadata is present', () => {
  const renderer = renderMessageBubble({
    role: 'system',
    content: 'Template {{NAME}}',
    metadata: { compiled_content: 'Template Alice' },
  });

  const toggle = renderer.root.findByProps({ testID: 'system-compiled-toggle' });
  const hiddenHint = renderer.root.findAllByType(SelectablePlainText).filter((node) => {
    return node.props.text === 'Compiled system prompt hidden (tap chevron to expand).';
  });
  expect(hiddenHint.length).toBeGreaterThan(0);

  ReactTestRenderer.act(() => {
    toggle.props.onPress();
  });

  const compiledContent = renderer.root.findAllByProps({ testID: 'system-compiled-content' });
  expect(
    compiledContent.some((node) => node.props.text === 'Template Alice' || node.props.value === 'Template Alice'),
  ).toBe(true);
});


test('message attachment rendering keeps hook order when multipart parts appear and disappear', () => {
  const plainUserMessage = {
    role: 'user',
    content: 'Plain text',
    metadata: {},
  };
  const imageUserMessage = {
    role: 'user',
    content: 'Image text',
    metadata: {},
    multipartContent: [
      {
        type: 'image',
        content: {
          filename: 'red.png',
          mime_type: 'image/png',
          preview_url: 'data:image/png;base64,QUJDRA==',
        },
        metadata: {},
      },
    ],
  };

  const renderer = renderMessageBubble(plainUserMessage);

  expect(() => updateMessageBubble(renderer, imageUserMessage)).not.toThrow();
  expect(() => updateMessageBubble(renderer, plainUserMessage)).not.toThrow();
});


test('message attachment preview opens a stable attachment snapshot', () => {
  const onOpenAttachment = jest.fn();
  const renderer = renderMessageBubble(
    {
      role: 'user',
      content: 'Image text',
      metadata: {},
      multipartContent: [
        {
          type: 'image',
          content: {
            filename: 'red.png',
            mime_type: 'image/png',
            preview_url: 'data:image/png;base64,QUJDRA==',
          },
          metadata: { download_plugin_id: 'plugin.image' },
        },
      ],
    },
    { onOpenAttachment },
  );

  const strip = renderer.root.findByType(AttachmentThumbnailStrip);
  ReactTestRenderer.act(() => {
    strip.props.onPress(strip.props.attachments[0]);
  });

  expect(onOpenAttachment).toHaveBeenCalledTimes(1);
  expect(onOpenAttachment).toHaveBeenCalledWith(
    expect.objectContaining({
      id: '0',
      type: 'image',
      messageIndex: 0,
      partIndex: 0,
      cacheKey: '0:0',
      metadata: { download_plugin_id: 'plugin.image' },
    }),
  );
});


test('user markdown mode renders selectable enriched markdown prose by default', () => {
  const renderer = renderMessageBubble({
    role: 'user',
    content: 'Hello **selectable** user.',
    metadata: {},
  });

  const enrichedMarkdown = renderer.root.find((node) => String(node.type) === 'EnrichedMarkdownText');

  expect(enrichedMarkdown.props.markdown).toBe('Hello **selectable** user.');
  expect(enrichedMarkdown.props.selectable).toBe(true);
  expect(enrichedMarkdown.props.markdownStyle.paragraph).toEqual(
    expect.objectContaining({
      fontSize: lightTheme.typography.fontSize.message,
      color: lightTheme.text,
    }),
  );
});


test('user raw mode renders selectable plain text', () => {
  const renderer = renderMessageBubble(
    {
      role: 'user',
      content: 'Raw user text',
      metadata: {},
    },
    { renderMode: 'raw' },
  );

  const selectableText = renderer.root.findByType(SelectablePlainText);

  expect(selectableText.props.text).toBe('Raw user text');
});


test('assistant raw mode renders selectable plain text', () => {
  const renderer = renderMessageBubble(
    {
      role: 'assistant',
      content: 'Raw assistant text',
      metadata: {},
    },
    { renderMode: 'raw' },
  );

  const selectableText = renderer.root.findByType(SelectablePlainText);

  expect(selectableText.props.text).toBe('Raw assistant text');
});


test('assistant markdown mode renders selectable enriched markdown prose', () => {
  const renderer = renderMessageBubble({
    role: 'assistant',
    content: 'Hello **selectable** [world](https://example.com).',
    metadata: {},
  });

  const enrichedMarkdown = renderer.root.find((node) => String(node.type) === 'EnrichedMarkdownText');

  expect(enrichedMarkdown.props.markdown).toBe('Hello **selectable** [world](https://example.com).');
  expect(enrichedMarkdown.props.selectable).toBe(true);
  expect(enrichedMarkdown.props.flavor).toBe('github');
  expect(enrichedMarkdown.props.onLinkPress).toEqual(expect.any(Function));
  expect(enrichedMarkdown.props.markdownStyle.paragraph).toEqual(
    expect.objectContaining({
      fontSize: lightTheme.typography.fontSize.message,
      lineHeight: lightTheme.typography.lineHeight.message,
      color: lightTheme.text,
      marginTop: 10,
      marginBottom: 10,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.h1).toEqual(
    expect.objectContaining({
      fontSize: 32,
      lineHeight: 38,
      fontWeight: '700',
      marginTop: 4,
      marginBottom: 2,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.h2).toEqual(
    expect.objectContaining({
      fontSize: 24,
      lineHeight: 29,
      fontWeight: '700',
      marginTop: 4,
      marginBottom: 2,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.h6).toEqual(
    expect.objectContaining({
      fontSize: lightTheme.typography.fontSize.message,
      lineHeight: lightTheme.typography.lineHeight.message,
      fontWeight: '700',
      marginTop: 4,
      marginBottom: 2,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.list).toEqual(
    expect.objectContaining({
      fontSize: lightTheme.typography.fontSize.message,
      lineHeight: lightTheme.typography.lineHeight.message,
      marginTop: 2,
      marginBottom: 2,
      bulletSize: 3,
      markerFontWeight: 'normal',
      gapWidth: 10,
      marginLeft: 37,
      unorderedGapWidth: 15,
      unorderedMarginLeft: 30,
      unorderedMarkerMarginBefore: 10,
      orderedGapWidth: 10,
      orderedMarginLeft: 27,
      orderedMarkerMarginBefore: 0,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.taskList).toEqual(
    expect.objectContaining({
      checkedColor: lightTheme.primary,
      borderColor: lightTheme.border,
      checkmarkColor: lightTheme.textOnPrimary,
      checkedTextColor: lightTheme.text,
      checkedStrikethrough: false,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.table).toEqual(
    expect.objectContaining({
      fontSize: lightTheme.typography.fontSize.message,
      lineHeight: lightTheme.typography.lineHeight.message,
      color: lightTheme.text,
      marginTop: 8,
      marginBottom: 12,
      headerBackgroundColor: lightTheme.surfaceAlt,
      headerTextColor: lightTheme.text,
      rowEvenBackgroundColor: lightTheme.surface,
      rowOddBackgroundColor: lightTheme.surfaceAlt,
      borderColor: lightTheme.border,
      borderWidth: 1,
      borderRadius: 6,
      cellPaddingHorizontal: 10,
      cellPaddingVertical: 7,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.codeBlock).toEqual(
    expect.objectContaining({
      fontFamily: 'Courier',
      fontSize: lightTheme.typography.fontSize.code,
      lineHeight: lightTheme.typography.lineHeight.code,
      color: lightTheme.text,
      marginTop: 4,
      marginBottom: 4,
      backgroundColor: lightTheme.codeBlockBg,
      borderColor: lightTheme.border,
      borderRadius: 6,
      borderWidth: 1,
      padding: 8,
    }),
  );
});


test('assistant markdown mode can render fenced code blocks through selectable native code blocks', () => {
  const renderer = renderMessageBubble({
    role: 'assistant',
    content: [
      'Intro paragraph.',
      '',
      '```ts',
      'const value = 1;',
      '```',
      '',
      'Outro paragraph.',
    ].join('\n'),
    metadata: {},
  });

  const enrichedMarkdown = renderer.root.findAll((node) => String(node.type) === 'EnrichedMarkdownText');
  const selectableCodeBlocks = renderer.root.findAll((node) => (
    String(node.type) === 'View' && node.props.testID === 'selectable-markdown-code-block'
  ));
  const selectableCodeBlockViews = renderer.root.findAll((node) => String(node.type) === 'SelectableCodeBlockView');
  const selectableTextViews = renderer.root.findAll((node) => String(node.type) === 'SelectableTextView');
  const syntaxHighlighters = renderer.root.findAll((node) => String(node.type) === 'SyntaxHighlighter');

  const horizontalCodeScrolls = renderer.root.findAll((node) => node.props.horizontal === true);

  expect(enrichedMarkdown).toHaveLength(2);
  expect(enrichedMarkdown.map((node) => node.props.markdown.trim())).toEqual([
    'Intro paragraph.',
    'Outro paragraph.',
  ]);
  expect(selectableCodeBlocks).toHaveLength(1);
  expect(selectableCodeBlockViews).toHaveLength(1);
  expect(
    selectableCodeBlockViews[0].props.tokens
      .map((token: { text: string }) => token.text)
      .join(''),
  ).toBe('const value = 1;\n');
  expect(selectableCodeBlockViews[0].props.fontFamily).toBe('Courier');
  expect(selectableTextViews).toHaveLength(0);
  expect(syntaxHighlighters).toHaveLength(0);
  expect(horizontalCodeScrolls.length).toBeGreaterThan(0);
});
