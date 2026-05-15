import type { ApiMessage } from './api';
import type { AttachmentLike } from './components/AttachmentThumbnailStrip';

type MultipartPart = {
  type?: string;
  content?: any;
  metadata?: any;
};

export type MessageAttachmentSnapshot = AttachmentLike & {
  messageIndex?: number | null;
  partIndex: number;
  cacheKey: string;
};

export function selectMultipartParts(message: ApiMessage): MultipartPart[] {
  const parts = (message as any)?.multipartContent;
  const baseParts = Array.isArray(parts) ? (parts as MultipartPart[]) : [];
  const metadata = (message as any)?.metadata;
  const display = metadata && typeof metadata === 'object' ? (metadata as any).display : null;
  if (display && typeof display === 'object' && display.type === 'image') {
    return [
      ...baseParts,
      {
        type: 'image',
        content: (display as any).content,
        metadata: (display as any).metadata,
      },
    ];
  }
  return baseParts;
}

export function selectMultipartAttachments(
  message: ApiMessage,
  messageIndex?: number | null,
): MessageAttachmentSnapshot[] {
  return selectMultipartParts(message).map((part, partIndex) => {
    const type = typeof part?.type === 'string' ? part.type : 'attachment';
    const messageKey = messageIndex == null ? 'stream' : String(messageIndex);
    const id = `${partIndex}`;
    return {
      id,
      type,
      content: part?.content,
      metadata: part?.metadata,
      messageIndex: messageIndex ?? null,
      partIndex,
      cacheKey: `${messageKey}:${partIndex}`,
    };
  });
}

export function extensionFromMimeType(mimeType: string): string {
  switch (mimeType) {
    case 'image/png':
      return 'png';
    case 'image/jpeg':
      return 'jpg';
    case 'image/webp':
      return 'webp';
    case 'image/gif':
      return 'gif';
    default:
      return 'bin';
  }
}

export function attachmentMimeType(attachment: AttachmentLike): string {
  const content = attachment.content;
  if (
    content &&
    typeof content === 'object' &&
    typeof content.mime_type === 'string' &&
    content.mime_type
  ) {
    return content.mime_type;
  }
  return attachment.type === 'image' ? 'image/png' : 'application/octet-stream';
}

export function attachmentFilename(attachment: AttachmentLike): string {
  const content = attachment.content;
  if (
    content &&
    typeof content === 'object' &&
    typeof content.filename === 'string' &&
    content.filename
  ) {
    return content.filename;
  }
  const mimeType = attachmentMimeType(attachment);
  return `attachment-${attachment.id}.${extensionFromMimeType(mimeType)}`;
}

export function parseDataUrl(url: string): { mimeType: string; dataBase64: string } | null {
  const match = url.match(/^data:([^;]+);base64,(.+)$/i);
  if (!match) return null;
  return {
    mimeType: match[1] || 'application/octet-stream',
    dataBase64: match[2] || '',
  };
}

export function resolveAttachmentDownloadPluginId(attachment: AttachmentLike): string | null {
  const metadata = attachment.metadata;
  if (
    metadata &&
    typeof metadata === 'object' &&
    typeof (metadata as any).download_plugin_id === 'string' &&
    (metadata as any).download_plugin_id
  ) {
    return String((metadata as any).download_plugin_id);
  }
  return null;
}