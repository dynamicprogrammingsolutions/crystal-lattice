import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { Text, TouchableOpacity } from 'react-native';

import AttachmentViewerHost from '../src/components/AttachmentViewerHost';
import { ThemeProvider, lightTheme } from '../src/theme';

const mockShareOpen = jest.fn<Promise<void>, [any]>(async () => {});
const mockSaveDocuments = jest.fn<Promise<Array<{ name: string }>>, [any]>(
  async () => [{ name: 'attachment.png' }],
);
const mockWriteFile = jest.fn<Promise<void>, [string, string, string]>(async () => {});

jest.mock('react-native', () => {
  const React = require('react');
  const actual = jest.requireActual('react-native');
  const mock = Object.create(actual);
  mock.Modal = ({ children, ...props }: any) =>
    React.createElement(actual.View, { ...props, testID: 'modal' }, children);
  return mock;
});

jest.mock('react-native-gesture-handler', () => ({
  gestureHandlerRootHOC: (Component: any) => Component,
}));

jest.mock('@likashefqet/react-native-image-zoom', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    ImageZoom: (props: any) => React.createElement(View, { ...props, testID: 'image-zoom' }),
  };
});

jest.mock('react-native-fs', () => ({
  CachesDirectoryPath: '/tmp',
  mkdir: jest.fn(async () => {}),
  writeFile: (path: string, data: string, encoding: string) =>
    mockWriteFile(path, data, encoding),
  downloadFile: jest.fn(() => ({ promise: Promise.resolve({ statusCode: 200 }) })),
}));

jest.mock('react-native-share', () => ({
  open: (options: any) => mockShareOpen(options),
}));

jest.mock('@react-native-documents/picker', () => ({
  saveDocuments: (options: any) => mockSaveDocuments(options),
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

function createAttachment(overrides: Record<string, any> = {}) {
  return {
    id: '0',
    type: 'image',
    content: {
      filename: 'red.png',
      mime_type: 'image/png',
      data_base64: 'QUJDRA==',
      ...overrides.content,
    },
    metadata: overrides.metadata ?? {},
    messageIndex: 2,
    partIndex: 0,
    cacheKey: '2:0',
  };
}

function renderHost(options: { backend?: any; attachment?: any } = {}) {
  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ThemeProvider theme={lightTheme}>
        <AttachmentViewerHost
          backend={options.backend ?? null}
          sessionId="session-1"
          attachment={options.attachment ?? createAttachment()}
          onRequestClose={jest.fn()}
        />
      </ThemeProvider>,
    );
  });
  return renderer!;
}

function renderFooter(renderer: ReactTestRenderer.ReactTestRenderer) {
  return renderer;
}

function findButtonByText(renderer: ReactTestRenderer.ReactTestRenderer, label: string) {
  return renderer.root.findAllByType(TouchableOpacity).find((button) => {
    return button.findAllByType(Text).some((text) => text.props.children === label);
  });
}

beforeEach(() => {
  jest.clearAllMocks();
});

test('attachment viewer renders image modal footer actions and shares the selected image', async () => {
  const renderer = renderHost();
  const footerRenderer = renderFooter(renderer);
  const shareButton = findButtonByText(footerRenderer, 'Share');

  expect(shareButton).toBeTruthy();

  await ReactTestRenderer.act(async () => {
    shareButton!.props.onPress();
  });

  expect(mockWriteFile).toHaveBeenCalledWith(
    '/tmp/attachment-previews/session-session-1-message-2-part-0-red.png',
    'QUJDRA==',
    'base64',
  );
  expect(mockShareOpen).toHaveBeenCalledWith(
    expect.objectContaining({
      url: 'file:///tmp/attachment-previews/session-session-1-message-2-part-0-red.png',
      type: 'image/png',
      filename: 'red.png',
      failOnCancel: false,
    }),
  );
});

test('attachment viewer opens preview first and loads full size only from explicit button', async () => {
  const executeAction = jest.fn(async () => ({
    status: 'ok',
    result: {
      attachment_asset: {
        asset_ref: {
          kind: 'session_asset',
          session_id: 'session-1',
          asset_id: 'asset-1',
          attachment_type: 'image',
        },
        filename: 'red.png',
        mime_type: 'image/png',
      },
      data_base64: 'RlVMTA==',
    },
  }));
  const backend = {
    kind: 'rest',
    executeAction,
  };
  const renderer = renderHost({
    backend,
    attachment: createAttachment({
      content: {
        asset_ref: {
          kind: 'session_asset',
          session_id: 'session-1',
          asset_id: 'asset-1',
          attachment_type: 'image',
        },
      },
      metadata: { download_plugin_id: 'plugin.image' },
    }),
  });

  expect(renderer.root.findByProps({ testID: 'image-zoom' }).props.uri).toBe(
    'data:image/png;base64,QUJDRA==',
  );

  const footerRenderer = renderFooter(renderer);
  const loadButton = findButtonByText(footerRenderer, 'Load Full Size');
  expect(loadButton).toBeTruthy();

  await ReactTestRenderer.act(async () => {
    loadButton!.props.onPress();
  });

  expect(executeAction).toHaveBeenCalledWith(
    expect.objectContaining({
      pluginId: 'plugin.image',
      actionId: 'download_attachment',
      inputs: {
        session_id: 'session-1',
        asset_id: 'asset-1',
      },
    }),
  );
  expect(mockWriteFile).toHaveBeenCalledWith(
    '/tmp/attachment-previews/session-session-1-asset-asset-1-plugin-plugin.image-full-red.png',
    'RlVMTA==',
    'base64',
  );
  expect(renderer.root.findByProps({ testID: 'image-zoom' }).props.uri).toBe(
    'file:///tmp/attachment-previews/session-session-1-asset-asset-1-plugin-plugin.image-full-red.png',
  );
});

test('attachment viewer shows an explicit full-size download error', async () => {
  const renderer = renderHost({
    backend: {
      kind: 'rest',
      executeAction: jest.fn(),
    },
  });
  const footerRenderer = renderFooter(renderer);
  const loadButton = findButtonByText(footerRenderer, 'Load Full Size');

  await ReactTestRenderer.act(async () => {
    loadButton!.props.onPress();
  });

  const errorText = footerRenderer.root.findAllByType(Text).find((text) => {
    return text.props.children === 'Full-size download is unavailable for this attachment.';
  });

  expect(errorText).toBeTruthy();
});

test('attachment viewer reopens with cached full-size image', async () => {
  const attachment = createAttachment({
    content: {
      asset_ref: {
        kind: 'session_asset',
        session_id: 'session-1',
        asset_id: 'asset-1',
        attachment_type: 'image',
      },
    },
    metadata: { download_plugin_id: 'plugin.image' },
  });
  const backend = {
    kind: 'rest',
    executeAction: jest.fn(async () => ({
      status: 'ok',
      result: {
        attachment_asset: {
          asset_ref: {
            kind: 'session_asset',
            session_id: 'session-1',
            asset_id: 'asset-1',
            attachment_type: 'image',
          },
          filename: 'red.png',
          mime_type: 'image/png',
        },
        data_base64: 'RlVMTA==',
      },
    })),
  };
  const renderer = renderHost({ backend, attachment });
  const footerRenderer = renderFooter(renderer);
  const loadButton = findButtonByText(footerRenderer, 'Load Full Size');

  await ReactTestRenderer.act(async () => {
    loadButton!.props.onPress();
  });

  ReactTestRenderer.act(() => {
    renderer.update(
      <ThemeProvider theme={lightTheme}>
        <AttachmentViewerHost
          backend={backend as any}
          sessionId="session-1"
          attachment={null}
          onRequestClose={jest.fn()}
        />
      </ThemeProvider>,
    );
  });

  ReactTestRenderer.act(() => {
    renderer.update(
      <ThemeProvider theme={lightTheme}>
        <AttachmentViewerHost
          backend={backend as any}
          sessionId="session-1"
          attachment={attachment}
          onRequestClose={jest.fn()}
        />
      </ThemeProvider>,
    );
  });

  expect(renderer.root.findByProps({ testID: 'image-zoom' }).props.uri).toBe(
    'file:///tmp/attachment-previews/session-session-1-asset-asset-1-plugin-plugin.image-full-red.png',
  );
});