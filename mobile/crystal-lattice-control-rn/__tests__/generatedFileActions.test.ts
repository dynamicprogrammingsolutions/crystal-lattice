import { Platform } from 'react-native';

import { downloadAttachmentAssetToLocalUri, handleGeneratedFileFollowupAction } from '../src/utils/generatedFileActions';

const mockWriteFile = jest.fn<Promise<void>, [string, string, string]>(async () => {});
const mockShareOpen = jest.fn<Promise<void>, [any]>(async () => {});
const mockSaveDocuments = jest.fn<Promise<Array<{ name: string }>>, [any]>(
  async () => [{ name: 'export.pdf' }],
);

jest.mock('react-native-fs', () => ({
  CachesDirectoryPath: '/tmp',
  mkdir: jest.fn(async () => {}),
  writeFile: (path: string, data: string, encoding: string) => mockWriteFile(path, data, encoding),
}));

jest.mock('react-native-share', () => ({
  open: (options: any) => mockShareOpen(options),
}));

jest.mock('@react-native-documents/picker', () => ({
  saveDocuments: (options: any) => mockSaveDocuments(options),
}));

const BASE_ACTION = {
  kind: 'download_attachment_asset' as const,
  id: 'open_pdf',
  label: 'Open PDF',
  session_id: 'session-1',
  asset_id: 'asset-1',
  filename: 'report.pdf',
  mime_type: 'application/pdf',
  plugin: 'message_share_as_pdf',
  action_owner: 'application',
  behavior: 'platform_default' as const,
};

beforeEach(() => {
  jest.clearAllMocks();
});

test('downloads a generated attachment asset into the cache directory', async () => {
  const executeAction = jest.fn(async () => ({
    status: 'ok',
    result: {
      attachment_asset: {
        asset_ref: {
          kind: 'session_asset',
          session_id: 'session-1',
          asset_id: 'asset-1',
          attachment_type: 'pdf',
        },
        filename: 'report.pdf',
        mime_type: 'application/pdf',
      },
      data_base64: 'UERG',
    },
  }));
  const uri = await downloadAttachmentAssetToLocalUri({
    backend: { kind: 'rest', executeAction } as any,
    action: BASE_ACTION,
  });

  expect(executeAction).toHaveBeenCalledWith({
    pluginId: 'message_share_as_pdf',
    actionId: 'download_attachment',
    actionOwner: 'application',
    inputs: {
      session_id: 'session-1',
      asset_id: 'asset-1',
    },
  });
  expect(mockWriteFile).toHaveBeenCalledWith(
    '/tmp/generated-action-files/asset-1-report.pdf',
    'UERG',
    'base64',
  );
  expect(uri).toBe('file:///tmp/generated-action-files/asset-1-report.pdf');
});

test('uses the share sheet on mobile hosts by default', async () => {
  const original = Platform.OS;
  Object.defineProperty(Platform, 'OS', { configurable: true, value: 'ios' });

  try {
    await handleGeneratedFileFollowupAction({
      backend: {
        kind: 'rest',
        executeAction: jest.fn(async () => ({
          status: 'ok',
          result: {
            attachment_asset: {
              asset_ref: {
                kind: 'session_asset',
                session_id: 'session-1',
                asset_id: 'asset-1',
                attachment_type: 'pdf',
              },
              filename: 'report.pdf',
              mime_type: 'application/pdf',
            },
            data_base64: 'UERG',
          },
        })),
      } as any,
      action: BASE_ACTION,
    });
  } finally {
    Object.defineProperty(Platform, 'OS', { configurable: true, value: original });
  }

  expect(mockShareOpen).toHaveBeenCalledWith(
    expect.objectContaining({
      url: 'file:///tmp/generated-action-files/asset-1-report.pdf',
      type: 'application/pdf',
      filename: 'report.pdf',
    }),
  );
  expect(mockSaveDocuments).not.toHaveBeenCalled();
});

test('uses the save dialog on desktop hosts by default', async () => {
  const original = Platform.OS;
  Object.defineProperty(Platform, 'OS', { configurable: true, value: 'macos' });

  try {
    await handleGeneratedFileFollowupAction({
      backend: {
        kind: 'rest',
        executeAction: jest.fn(async () => ({
          status: 'ok',
          result: {
            attachment_asset: {
              asset_ref: {
                kind: 'session_asset',
                session_id: 'session-1',
                asset_id: 'asset-1',
                attachment_type: 'pdf',
              },
              filename: 'report.pdf',
              mime_type: 'application/pdf',
            },
            data_base64: 'UERG',
          },
        })),
      } as any,
      action: BASE_ACTION,
    });
  } finally {
    Object.defineProperty(Platform, 'OS', { configurable: true, value: original });
  }

  expect(mockSaveDocuments).toHaveBeenCalledWith(
    expect.objectContaining({
      sourceUris: ['file:///tmp/generated-action-files/asset-1-report.pdf'],
      mimeType: 'application/pdf',
      fileName: 'report.pdf',
      copy: true,
    }),
  );
  expect(mockShareOpen).not.toHaveBeenCalled();
});