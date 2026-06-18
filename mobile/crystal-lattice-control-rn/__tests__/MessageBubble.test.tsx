import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import MessageBubble from '../src/components/MessageBubble';
import { AttachmentThumbnailStrip } from '../src/components/AttachmentThumbnailStrip';
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
  const hiddenHint = renderer.root.findAll((node) => {
    return node.props?.children === 'Compiled system prompt hidden (tap chevron to expand).';
  });
  expect(hiddenHint.length).toBeGreaterThan(0);

  ReactTestRenderer.act(() => {
    toggle.props.onPress();
  });

  const compiledContent = renderer.root.findByProps({ testID: 'system-compiled-content' });
  expect(compiledContent.props.children).toBe('Template Alice');
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


test('assistant markdown mode renders selectable enriched markdown prose', () => {
  const renderer = renderMessageBubble({
    role: 'assistant',
    content: 'Hello **selectable** [world](https://example.com).',
    metadata: {},
  });

  const enrichedMarkdown = renderer.root.find((node) => String(node.type) === 'EnrichedMarkdownText');

  expect(enrichedMarkdown.props.markdown).toBe('Hello **selectable** [world](https://example.com).');
  expect(enrichedMarkdown.props.selectable).toBe(true);
  expect(enrichedMarkdown.props.flavor).toBe('commonmark');
  expect(enrichedMarkdown.props.onLinkPress).toEqual(expect.any(Function));
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
