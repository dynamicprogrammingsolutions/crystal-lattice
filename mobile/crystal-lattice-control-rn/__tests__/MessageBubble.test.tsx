import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import MessageBubble from '../src/components/MessageBubble';
import { ThemeProvider, lightTheme } from '../src/theme';


jest.mock('react-native-image-modal', () => {
  const React = require('react');
  const { View } = require('react-native');
  return function ImageModalMock(props: any) {
    return React.createElement(View, props);
  };
});

jest.mock('react-native-fs', () => ({
  CachesDirectoryPath: '/tmp',
  mkdir: jest.fn(async () => {}),
  writeFile: jest.fn(async () => {}),
  downloadFile: jest.fn(() => ({ promise: Promise.resolve({ statusCode: 200 }) })),
}));

jest.mock('react-native-share', () => ({
  open: jest.fn(async () => {}),
}));

jest.mock('@react-native-documents/picker', () => ({
  saveDocuments: jest.fn(async () => [{ name: 'attachment.png' }]),
}));

jest.mock('@react-native-camera-roll/camera-roll', () => ({
  CameraRoll: {
    saveAsset: jest.fn(async () => {}),
  },
  iosRequestAddOnlyGalleryPermission: jest.fn(async () => 'granted'),
}));

jest.mock('../src/theme', () => {
  const actual = jest.requireActual('../src/theme');
  return {
    ...actual,
    ThemeProvider: ({ children }: any) => <>{children}</>,
    useTheme: () => actual.lightTheme,
  };
});


function renderMessageBubble(message: any) {
  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ThemeProvider theme={lightTheme}>
        <MessageBubble
          index={0}
          message={message}
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