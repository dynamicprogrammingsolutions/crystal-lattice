import { Platform } from 'react-native';
import RNFS from 'react-native-fs';
import Share from 'react-native-share';
import { saveDocuments } from '@react-native-documents/picker';
import {
  downloadSessionAttachment,
  type AgentBackend,
  type ActionDisplayDownloadAttachmentAssetAction,
} from '@crystal-lattice/frontend-sdk';

function sanitizeFileComponent(value: string): string {
  const normalized = value.replace(/[^a-zA-Z0-9._-]+/g, '-').replace(/-+/g, '-');
  return normalized.replace(/^-+|-+$/g, '') || 'file';
}

export async function saveLocalDocument(options: {
  localUri: string;
  mimeType: string;
  fileName: string;
}): Promise<string> {
  const result = await saveDocuments({
    sourceUris: [options.localUri],
    mimeType: options.mimeType,
    fileName: options.fileName,
    copy: true,
  });
  const saved = result[0];
  if (saved?.error) {
    throw new Error(saved.error);
  }
  return saved?.name || options.fileName;
}

export async function shareLocalDocument(options: {
  localUri: string;
  mimeType: string;
  fileName: string;
}): Promise<void> {
  await Share.open({
    url: options.localUri,
    type: options.mimeType,
    filename: options.fileName,
    failOnCancel: false,
  });
}

export async function downloadAttachmentAssetToLocalUri(options: {
  backend: AgentBackend;
  action: ActionDisplayDownloadAttachmentAssetAction;
}): Promise<string> {
  const pluginId =
    typeof options.action.plugin === 'string' && options.action.plugin.trim()
      ? options.action.plugin.trim()
      : 'session_asset_attachments';
  const downloaded = await downloadSessionAttachment({
    backend: options.backend,
    sessionId: options.action.session_id,
    assetId: options.action.asset_id,
    pluginId,
    actionOwner:
      typeof options.action.action_owner === 'string' && options.action.action_owner.trim()
        ? options.action.action_owner.trim()
        : undefined,
  });

  const cacheDir = `${RNFS.CachesDirectoryPath}/generated-action-files`;
  await RNFS.mkdir(cacheDir);
  const targetPath = `${cacheDir}/${sanitizeFileComponent(options.action.asset_id)}-${sanitizeFileComponent(
    options.action.filename,
  )}`;
  await RNFS.writeFile(targetPath, downloaded.data_base64, 'base64');
  return `file://${targetPath}`;
}

export async function handleGeneratedFileFollowupAction(options: {
  backend: AgentBackend;
  action: ActionDisplayDownloadAttachmentAssetAction;
}): Promise<void> {
  const localUri = await downloadAttachmentAssetToLocalUri(options);
  const behavior = options.action.behavior ?? 'platform_default';
  const isMobileShareHost = Platform.OS === 'ios' || Platform.OS === 'android';

  if (behavior === 'share' || (behavior === 'platform_default' && isMobileShareHost)) {
    await shareLocalDocument({
      localUri,
      mimeType: options.action.mime_type,
      fileName: options.action.filename,
    });
    return;
  }

  await saveLocalDocument({
    localUri,
    mimeType: options.action.mime_type,
    fileName: options.action.filename,
  });
}