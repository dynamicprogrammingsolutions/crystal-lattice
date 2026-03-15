export type AttachmentDraftStatus =
  | 'local'
  | 'uploading_to_server'
  | 'stored'
  | 'uploading_to_openai'
  | 'ready'
  | 'failed'
  | 'deleting';

export function isAttachmentDraftBlocking(status: AttachmentDraftStatus): boolean {
  return status === 'uploading_to_server' || status === 'uploading_to_openai' || status === 'deleting';
}

export function attachmentDraftStatusLabel(
  status: AttachmentDraftStatus,
  errorMessage?: string | null,
): string {
  switch (status) {
    case 'local':
      return 'Local';
    case 'uploading_to_server':
      return 'Uploading';
    case 'stored':
      return 'Stored';
    case 'uploading_to_openai':
      return 'Preparing';
    case 'ready':
      return 'Ready';
    case 'failed':
      return errorMessage && errorMessage.trim() ? `Failed: ${errorMessage.trim()}` : 'Failed';
    case 'deleting':
      return 'Deleting';
    default:
      return 'Attachment';
  }
}