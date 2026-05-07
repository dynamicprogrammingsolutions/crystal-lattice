import type { AgentBackend } from '../backend/backend';
import type { ExecuteActionResponse } from '../types/plugins';

export const DEFAULT_ATTACHMENT_ACTION_PLUGIN_ID = 'openai_responses_attachments';
export const DEFAULT_ATTACHMENT_ACTION_OWNER = 'provider_extension';
export const STORE_ATTACHMENT_ACTION_ID = 'store_attachment';
export const DELETE_ATTACHMENT_ACTION_ID = 'delete_attachment';
export const DOWNLOAD_ATTACHMENT_ACTION_ID = 'download_attachment';

export interface SessionAssetRef {
  kind: 'session_asset';
  session_id: string;
  asset_id: string;
  attachment_type: string;
  [k: string]: any;
}

export interface StoredAttachmentAssetDescriptor {
  asset_ref: SessionAssetRef;
  filename: string;
  mime_type: string;
  provider_refs?: Record<string, any>;
  size_bytes?: number;
  sha256?: string;
  created_at?: string;
  metadata?: Record<string, any>;
  client_attachment_id?: string;
  [k: string]: any;
}

export interface DownloadedAttachmentPayload {
  attachment_asset: StoredAttachmentAssetDescriptor;
  data_base64: string;
}

function actionErrorMessage(response: ExecuteActionResponse): string {
  if (!response) return 'Failed to execute attachment action';
  if (response.status !== 'ok') {
    return (response as any).message || 'Failed to execute attachment action';
  }
  const result = (response as any).result;
  if (result && typeof result === 'object' && typeof result.message === 'string' && result.message) {
    return result.message;
  }
  return 'Failed to execute attachment action';
}

function parseBase64Payload(options: { dataUrl?: string | null; dataBase64?: string | null }): string {
  if (typeof options.dataBase64 === 'string' && options.dataBase64.trim()) {
    return options.dataBase64.trim();
  }

  const dataUrl = typeof options.dataUrl === 'string' ? options.dataUrl.trim() : '';
  const match = dataUrl.match(/^data:[^;]+;base64,(.+)$/i);
  if (match && typeof match[1] === 'string' && match[1].trim()) {
    return match[1].trim();
  }

  throw new Error('Attachment content must include base64 data or a data: URL.');
}

function ensureStoredAttachmentDescriptor(value: any): StoredAttachmentAssetDescriptor {
  const assetRef = value?.asset_ref;
  if (
    !assetRef ||
    typeof assetRef !== 'object' ||
    assetRef.kind !== 'session_asset' ||
    typeof assetRef.session_id !== 'string' ||
    !assetRef.session_id ||
    typeof assetRef.asset_id !== 'string' ||
    !assetRef.asset_id ||
    typeof assetRef.attachment_type !== 'string' ||
    !assetRef.attachment_type
  ) {
    throw new Error('Attachment action returned an invalid asset_ref.');
  }
  if (typeof value?.filename !== 'string' || !value.filename) {
    throw new Error('Attachment action returned an invalid filename.');
  }
  if (typeof value?.mime_type !== 'string' || !value.mime_type) {
    throw new Error('Attachment action returned an invalid mime_type.');
  }
  return value as StoredAttachmentAssetDescriptor;
}

export function selectSessionAssetId(content: any): string | null {
  const assetRef = content?.asset_ref;
  if (
    assetRef &&
    typeof assetRef === 'object' &&
    assetRef.kind === 'session_asset' &&
    typeof assetRef.asset_id === 'string' &&
    assetRef.asset_id
  ) {
    return assetRef.asset_id;
  }
  return null;
}

export async function storeSessionAttachment(options: {
  backend: AgentBackend;
  sessionId: string;
  attachmentType: string;
  filename: string;
  mimeType: string;
  dataUrl?: string | null;
  dataBase64?: string | null;
  clientAttachmentId?: string | null;
  pluginId?: string;
  idempotencyKey?: string;
}): Promise<StoredAttachmentAssetDescriptor> {
  const pluginId =
    typeof options.pluginId === 'string' && options.pluginId.trim()
      ? options.pluginId.trim()
      : DEFAULT_ATTACHMENT_ACTION_PLUGIN_ID;
  const sessionId = typeof options.sessionId === 'string' ? options.sessionId.trim() : '';
  if (!sessionId) {
    throw new Error('sessionId is required to store an attachment.');
  }

  const response = await options.backend.executeAction({
    pluginId,
    actionId: STORE_ATTACHMENT_ACTION_ID,
    actionOwner: DEFAULT_ATTACHMENT_ACTION_OWNER,
    idempotencyKey: options.idempotencyKey,
    inputs: {
      session_id: sessionId,
      attachment_type: options.attachmentType,
      filename: options.filename,
      mime_type: options.mimeType,
      data_base64: parseBase64Payload({
        dataUrl: options.dataUrl,
        dataBase64: options.dataBase64,
      }),
      ...(typeof options.clientAttachmentId === 'string' && options.clientAttachmentId.trim()
        ? { client_attachment_id: options.clientAttachmentId.trim() }
        : {}),
    },
  });

  if (!response || response.status !== 'ok') {
    throw new Error(actionErrorMessage(response));
  }

  return ensureStoredAttachmentDescriptor((response as any).result?.attachment_asset);
}

export async function deleteSessionAttachment(options: {
  backend: AgentBackend;
  sessionId: string;
  assetId: string;
  pluginId?: string;
  idempotencyKey?: string;
}): Promise<StoredAttachmentAssetDescriptor> {
  const pluginId =
    typeof options.pluginId === 'string' && options.pluginId.trim()
      ? options.pluginId.trim()
      : DEFAULT_ATTACHMENT_ACTION_PLUGIN_ID;
  const sessionId = typeof options.sessionId === 'string' ? options.sessionId.trim() : '';
  const assetId = typeof options.assetId === 'string' ? options.assetId.trim() : '';
  if (!sessionId) {
    throw new Error('sessionId is required to delete an attachment.');
  }
  if (!assetId) {
    throw new Error('assetId is required to delete an attachment.');
  }

  const response = await options.backend.executeAction({
    pluginId,
    actionId: DELETE_ATTACHMENT_ACTION_ID,
    actionOwner: DEFAULT_ATTACHMENT_ACTION_OWNER,
    idempotencyKey: options.idempotencyKey,
    inputs: {
      session_id: sessionId,
      asset_id: assetId,
    },
  });

  if (!response || response.status !== 'ok') {
    throw new Error(actionErrorMessage(response));
  }

  return ensureStoredAttachmentDescriptor((response as any).result?.deleted_attachment_asset);
}

export async function downloadSessionAttachment(options: {
  backend: AgentBackend;
  sessionId: string;
  assetId: string;
  pluginId?: string;
  idempotencyKey?: string;
}): Promise<DownloadedAttachmentPayload> {
  const pluginId =
    typeof options.pluginId === 'string' && options.pluginId.trim()
      ? options.pluginId.trim()
      : DEFAULT_ATTACHMENT_ACTION_PLUGIN_ID;
  const sessionId = typeof options.sessionId === 'string' ? options.sessionId.trim() : '';
  const assetId = typeof options.assetId === 'string' ? options.assetId.trim() : '';
  if (!sessionId) {
    throw new Error('sessionId is required to download an attachment.');
  }
  if (!assetId) {
    throw new Error('assetId is required to download an attachment.');
  }

  const response = await options.backend.executeAction({
    pluginId,
    actionId: DOWNLOAD_ATTACHMENT_ACTION_ID,
    actionOwner: DEFAULT_ATTACHMENT_ACTION_OWNER,
    idempotencyKey: options.idempotencyKey,
    inputs: {
      session_id: sessionId,
      asset_id: assetId,
    },
  });

  if (!response || response.status !== 'ok') {
    throw new Error(actionErrorMessage(response));
  }

  const result = (response as any).result;
  const attachmentAsset = ensureStoredAttachmentDescriptor(result?.attachment_asset);
  const dataBase64 = typeof result?.data_base64 === 'string' ? result.data_base64 : '';
  if (!dataBase64) {
    throw new Error('Attachment action returned an invalid data_base64 payload.');
  }

  return {
    attachment_asset: attachmentAsset,
    data_base64: dataBase64,
  };
}