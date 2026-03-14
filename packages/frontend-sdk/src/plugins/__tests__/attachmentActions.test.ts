import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import {
  deleteSessionAttachment,
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
    const executeAction = vi.fn(async () => ({
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
    const executeAction = vi.fn(async () => ({
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

  it('surfaces backend action errors with the server message', async () => {
    const executeAction = vi.fn(async () => ({
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
      }),
    ).rejects.toThrow('asset store unavailable');
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