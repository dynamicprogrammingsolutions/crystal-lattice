import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import type { ExecuteActionResponse } from '../../types/plugins';
import {
  downloadSessionAttachment,
  deleteSessionAttachment,
  DOWNLOAD_ATTACHMENT_ACTION_ID,
  resolveAttachmentActionPluginId,
  SESSION_ASSET_ATTACHMENTS_PLUGIN_ID,
  selectSessionAssetId,
  storeSessionAttachment,
} from '../attachmentActions';

function buildBackend(executeAction: AgentBackend['executeAction']): AgentBackend {
  return {
    kind: 'test',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    executeAction,
  } as any;
}

describe('attachmentActions', () => {
  it('stores an attachment using the provider-extension action contract', async () => {
    const executeAction: AgentBackend['executeAction'] = vi.fn(async (): Promise<ExecuteActionResponse> => ({
      status: 'ok',
      plugin: 'openai_responses_attachments',
      action_id: 'store_attachment',
      result: {
        attachment_asset: {
          asset_ref: {
            kind: 'session_asset',
            session_id: 's1',
            asset_id: 'asset_1',
            attachment_type: 'image',
          },
          filename: 'red.png',
          mime_type: 'image/png',
        },
      },
    }));

    const asset = await storeSessionAttachment({
      backend: buildBackend(executeAction),
      sessionId: 's1',
      attachmentType: 'image',
      filename: 'red.png',
      mimeType: 'image/png',
      dataUrl: 'data:image/png;base64,QUJDRA==',
      clientAttachmentId: 'draft-1',
      pluginId: 'openai_responses_attachments',
    });

    expect(asset.asset_ref.asset_id).toBe('asset_1');
    expect(executeAction).toHaveBeenCalledWith({
      pluginId: 'openai_responses_attachments',
      actionId: 'store_attachment',
      actionOwner: 'provider_extension',
      idempotencyKey: undefined,
      inputs: {
        session_id: 's1',
        attachment_type: 'image',
        filename: 'red.png',
        mime_type: 'image/png',
        data_base64: 'QUJDRA==',
        client_attachment_id: 'draft-1',
      },
    });
  });

  it('deletes an attachment using the provider-extension action contract', async () => {
    const executeAction: AgentBackend['executeAction'] = vi.fn(async (): Promise<ExecuteActionResponse> => ({
      status: 'ok',
      plugin: 'openai_responses_attachments',
      action_id: 'delete_attachment',
      result: {
        deleted_attachment_asset: {
          asset_ref: {
            kind: 'session_asset',
            session_id: 's1',
            asset_id: 'asset_1',
            attachment_type: 'pdf',
          },
          filename: 'report.pdf',
          mime_type: 'application/pdf',
        },
      },
    }));

    const deleted = await deleteSessionAttachment({
      backend: buildBackend(executeAction),
      sessionId: 's1',
      assetId: 'asset_1',
      pluginId: 'openai_responses_attachments',
    });

    expect(deleted.filename).toBe('report.pdf');
    expect(executeAction).toHaveBeenCalledWith({
      pluginId: 'openai_responses_attachments',
      actionId: 'delete_attachment',
      actionOwner: 'provider_extension',
      idempotencyKey: undefined,
      inputs: {
        session_id: 's1',
        asset_id: 'asset_1',
      },
    });
  });

  it('downloads an attachment using the provider-extension action contract', async () => {
    const executeAction: AgentBackend['executeAction'] = vi.fn(async (): Promise<ExecuteActionResponse> => ({
      status: 'ok',
      plugin: 'openrouter_image_generation_attachments',
      action_id: 'download_attachment',
      result: {
        attachment_asset: {
          asset_ref: {
            kind: 'session_asset',
            session_id: 's1',
            asset_id: 'asset_9',
            attachment_type: 'image',
          },
          filename: 'generated.png',
          mime_type: 'image/png',
        },
        data_base64: 'QUJDRA==',
      },
    }));

    const downloaded = await downloadSessionAttachment({
      backend: buildBackend(executeAction),
      sessionId: 's1',
      assetId: 'asset_9',
      pluginId: 'openrouter_image_generation_attachments',
    });

    expect(downloaded.attachment_asset.filename).toBe('generated.png');
    expect(downloaded.data_base64).toBe('QUJDRA==');
    expect(executeAction).toHaveBeenCalledWith({
      pluginId: 'openrouter_image_generation_attachments',
      actionId: DOWNLOAD_ATTACHMENT_ACTION_ID,
      actionOwner: 'provider_extension',
      idempotencyKey: undefined,
      inputs: {
        session_id: 's1',
        asset_id: 'asset_9',
      },
    });
  });

  it('downloads a generic session asset using the application action contract', async () => {
    const executeAction: AgentBackend['executeAction'] = vi.fn(async (): Promise<ExecuteActionResponse> => ({
      status: 'ok',
      plugin: SESSION_ASSET_ATTACHMENTS_PLUGIN_ID,
      action_id: 'download_attachment',
      result: {
        attachment_asset: {
          asset_ref: {
            kind: 'session_asset',
            session_id: 's1',
            asset_id: 'asset_10',
            attachment_type: 'image',
          },
          filename: 'opened.png',
          mime_type: 'image/png',
        },
        data_base64: 'QUJDRA==',
      },
    }));

    const downloaded = await downloadSessionAttachment({
      backend: buildBackend(executeAction),
      sessionId: 's1',
      assetId: 'asset_10',
      pluginId: SESSION_ASSET_ATTACHMENTS_PLUGIN_ID,
    });

    expect(downloaded.attachment_asset.filename).toBe('opened.png');
    expect(executeAction).toHaveBeenCalledWith({
      pluginId: SESSION_ASSET_ATTACHMENTS_PLUGIN_ID,
      actionId: DOWNLOAD_ATTACHMENT_ACTION_ID,
      actionOwner: 'application',
      idempotencyKey: undefined,
      inputs: {
        session_id: 's1',
        asset_id: 'asset_10',
      },
    });
  });

  it('forwards an explicit plugin id override for attachment actions', async () => {
    const executeAction: AgentBackend['executeAction'] = vi.fn(async (): Promise<ExecuteActionResponse> => ({
      status: 'ok',
      plugin: 'reference_openai_compatible_attachments',
      action_id: 'store_attachment',
      result: {
        attachment_asset: {
          asset_ref: {
            kind: 'session_asset',
            session_id: 's1',
            asset_id: 'asset_2',
            attachment_type: 'image',
          },
          filename: 'red.png',
          mime_type: 'image/png',
        },
      },
    }));

    await storeSessionAttachment({
      backend: buildBackend(executeAction),
      sessionId: 's1',
      attachmentType: 'image',
      filename: 'red.png',
      mimeType: 'image/png',
      dataBase64: 'QUJDRA==',
      pluginId: 'reference_openai_compatible_attachments',
    });

    expect(executeAction).toHaveBeenCalledWith({
      pluginId: 'reference_openai_compatible_attachments',
      actionId: 'store_attachment',
      actionOwner: 'provider_extension',
      idempotencyKey: undefined,
      inputs: {
        session_id: 's1',
        attachment_type: 'image',
        filename: 'red.png',
        mime_type: 'image/png',
        data_base64: 'QUJDRA==',
      },
    });
  });

  it('prefers attachment_action_plugin over plugin when resolving attachment action ownership', () => {
    expect(
      resolveAttachmentActionPluginId({
        ui_type: 'composer_attachment',
        plugin: 'openai_responses',
        attachment_action_plugin: 'openai_responses_attachments',
        attachment_type: 'image',
      }),
    ).toBe('openai_responses_attachments');
  });

  it('falls back to plugin when no attachment_action_plugin is provided', () => {
    expect(
      resolveAttachmentActionPluginId({
        ui_type: 'composer_attachment',
        plugin: 'openrouter_image_generation_attachments',
        attachment_type: 'image',
      }),
    ).toBe('openrouter_image_generation_attachments');
  });

  it('returns null when an attachment element does not define a usable action plugin', () => {
    expect(
      resolveAttachmentActionPluginId({
        ui_type: 'composer_attachment',
        plugin: '   ',
        attachment_action_plugin: '',
        attachment_type: 'image',
      }),
    ).toBeNull();
  });

  it('surfaces backend action errors with the server message', async () => {
    const executeAction: AgentBackend['executeAction'] = vi.fn(async (): Promise<ExecuteActionResponse> => ({
      status: 'error',
      message: 'asset store unavailable',
    }));

    await expect(
      storeSessionAttachment({
        backend: buildBackend(executeAction),
        sessionId: 's1',
        attachmentType: 'pdf',
        filename: 'report.pdf',
        mimeType: 'application/pdf',
        dataBase64: 'QUJDRA==',
        pluginId: 'openai_responses_attachments',
      }),
    ).rejects.toThrow('asset store unavailable');
  });

  it('uses an explicit actionOwner when provided', async () => {
    const executeAction: AgentBackend['executeAction'] = vi.fn(async (): Promise<ExecuteActionResponse> => ({
      status: 'ok',
      plugin: 'message_share_as_pdf',
      action_id: 'download_attachment',
      result: {
        attachment_asset: {
          asset_ref: {
            kind: 'session_asset',
            session_id: 's1',
            asset_id: 'asset_20',
            attachment_type: 'pdf',
          },
          filename: 'report.pdf',
          mime_type: 'application/pdf',
        },
        data_base64: 'QUJDRA==',
      },
    }));

    await downloadSessionAttachment({
      backend: buildBackend(executeAction),
      sessionId: 's1',
      assetId: 'asset_20',
      pluginId: 'message_share_as_pdf',
      actionOwner: 'application',
    });

    expect(executeAction).toHaveBeenCalledWith({
      pluginId: 'message_share_as_pdf',
      actionId: DOWNLOAD_ATTACHMENT_ACTION_ID,
      actionOwner: 'application',
      idempotencyKey: undefined,
      inputs: {
        session_id: 's1',
        asset_id: 'asset_20',
      },
    });
  });

  it('rejects missing plugin ids for generic attachment helpers', async () => {
    await expect(
      storeSessionAttachment({
        backend: buildBackend(vi.fn()),
        sessionId: 's1',
        attachmentType: 'image',
        filename: 'red.png',
        mimeType: 'image/png',
        dataBase64: 'QUJDRA==',
        pluginId: '',
      }),
    ).rejects.toThrow('pluginId is required');
  });

  it('selects asset ids from session-asset content payloads', () => {
    expect(
      selectSessionAssetId({
        asset_ref: {
          kind: 'session_asset',
          session_id: 's1',
          asset_id: 'asset_1',
          attachment_type: 'image',
        },
      }),
    ).toBe('asset_1');
    expect(selectSessionAssetId({ url: 'https://example.com/image.png' })).toBeNull();
  });
});