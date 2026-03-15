import { describe, expect, it } from 'vitest';

import { selectAttachmentPreviewUrl } from './preview';

describe('selectAttachmentPreviewUrl', () => {
  it('prefers explicit previewUrl overrides', () => {
    expect(selectAttachmentPreviewUrl({ url: 'https://example.com/original.png' }, 'data:image/png;base64,abc')).toBe(
      'data:image/png;base64,abc',
    );
  });

  it('builds data urls from preview_data_base64 when direct payloads are absent', () => {
    expect(
      selectAttachmentPreviewUrl({
        mime_type: 'image/png',
        preview_data_base64: 'YWJj',
        preview_mime_type: 'image/png',
      }),
    ).toBe('data:image/png;base64,YWJj');
  });

  it('falls back to content data_base64 before preview bytes', () => {
    expect(
      selectAttachmentPreviewUrl({
        mime_type: 'image/png',
        data_base64: 'ZGF0YQ==',
        preview_data_base64: 'cHJldmlldw==',
      }),
    ).toBe('data:image/png;base64,ZGF0YQ==');
  });

  it('returns null for unsupported content', () => {
    expect(selectAttachmentPreviewUrl({ asset_ref: { asset_id: 'asset_1' } })).toBeNull();
    expect(selectAttachmentPreviewUrl(null)).toBeNull();
  });
});