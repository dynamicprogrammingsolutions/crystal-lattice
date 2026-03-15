import { describe, expect, it } from 'vitest';

import {
  attachmentDraftStatusLabel,
  isAttachmentDraftBlocking,
} from './draftStatus';

describe('attachment draft status helpers', () => {
  it('marks upload and delete states as blocking', () => {
    expect(isAttachmentDraftBlocking('uploading_to_server')).toBe(true);
    expect(isAttachmentDraftBlocking('uploading_to_openai')).toBe(true);
    expect(isAttachmentDraftBlocking('deleting')).toBe(true);
    expect(isAttachmentDraftBlocking('ready')).toBe(false);
    expect(isAttachmentDraftBlocking('failed')).toBe(false);
  });

  it('formats failure labels with details when present', () => {
    expect(attachmentDraftStatusLabel('failed', 'network')).toBe('Failed: network');
    expect(attachmentDraftStatusLabel('ready')).toBe('Ready');
  });
});