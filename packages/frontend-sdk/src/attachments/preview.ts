export function selectAttachmentPreviewUrl(content: any, previewUrl?: string | null): string | null {
  if (typeof previewUrl === 'string' && previewUrl) {
    return previewUrl;
  }
  if (!content || typeof content !== 'object') {
    return null;
  }
  if (typeof content.url === 'string' && content.url) {
    return content.url;
  }
  if (typeof content.data_base64 === 'string' && content.data_base64) {
    const mimeType =
      typeof content.mime_type === 'string' && content.mime_type
        ? content.mime_type
        : 'application/octet-stream';
    return `data:${mimeType};base64,${content.data_base64}`;
  }
  if (typeof content.preview_data_base64 === 'string' && content.preview_data_base64) {
    const mimeType =
      typeof content.preview_mime_type === 'string' && content.preview_mime_type
        ? content.preview_mime_type
        : typeof content.mime_type === 'string' && content.mime_type
          ? content.mime_type
          : 'application/octet-stream';
    return `data:${mimeType};base64,${content.preview_data_base64}`;
  }
  return null;
}