import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import MessageBubble from '../src/components/MessageBubble';
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
      lineHeight: Math.round(lightTheme.typography.fontSize.message * 1.25),
      color: lightTheme.text,
      marginTop: 10,
      marginBottom: 10,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.h1).toEqual(
    expect.objectContaining({
      fontSize: 32,
      lineHeight: 40,
      fontWeight: '700',
      marginTop: 4,
      marginBottom: 2,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.h2).toEqual(
    expect.objectContaining({
      fontSize: 24,
      lineHeight: 30,
      fontWeight: '700',
      marginTop: 4,
      marginBottom: 2,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.h6).toEqual(
    expect.objectContaining({
      fontSize: 11,
      lineHeight: 14,
      fontWeight: '700',
      marginTop: 4,
      marginBottom: 2,
    }),
  );
  expect(enrichedMarkdown.props.markdownStyle.list).toEqual(
    expect.objectContaining({
      fontSize: lightTheme.typography.fontSize.message,
      lineHeight: Math.round(lightTheme.typography.fontSize.message * 1.25),
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
      lineHeight: Math.round(lightTheme.typography.fontSize.message * 1.25),
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
});


test('assistant markdown mode preserves syntax-highlighted fenced code blocks', () => {
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
  const syntaxHighlighters = renderer.root.findAll((node) => String(node.type) === 'SyntaxHighlighter');

  expect(enrichedMarkdown).toHaveLength(2);
  expect(enrichedMarkdown.map((node) => node.props.markdown.trim())).toEqual([
    'Intro paragraph.',
    'Outro paragraph.',
  ]);
  expect(syntaxHighlighters).toHaveLength(1);
  expect(syntaxHighlighters[0].props.language).toBe('ts');
  expect(syntaxHighlighters[0].props.children).toBe('const value = 1;\n');
});
