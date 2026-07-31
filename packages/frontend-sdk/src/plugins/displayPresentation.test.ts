import { describe, expect, it } from 'vitest';

import {
  normalizeDisplayEnvelope,
  normalizeDisplayEnvelopeForHost,
} from './displayPresentation';

describe('display presentation envelopes', () => {
  it.each([
    ['application_notification', 'banner'],
    ['session_notification', 'inline'],
    ['action_response', 'modal'],
  ] as const)('uses the compatible %s default', (source, presentation) => {
    const envelope = normalizeDisplayEnvelope({
      id: 'display-1',
      source,
      display: { format: 'text', body: 'Body' },
    });
    expect(envelope.display.presentation).toBe(presentation);
    expect(envelope.display.display_id).toBe('display-1');
  });

  it('preserves every explicit standard presentation', () => {
    for (const presentation of ['banner', 'inline', 'modal'] as const) {
      expect(
        normalizeDisplayEnvelope({
          source: 'action_response',
          display: { format: 'text', body: 'Body', presentation },
        }).display.presentation,
      ).toBe(presentation);
    }
  });

  it('rejects inline application notifications', () => {
    expect(() =>
      normalizeDisplayEnvelope({
        source: 'application_notification',
        display: { format: 'text', body: 'Body', presentation: 'inline' },
      }),
    ).toThrow('Application notifications do not support inline presentation');
  });

  it('normalizes desktop modal displays to inline', () => {
    const envelope = normalizeDisplayEnvelope({
      source: 'session_notification',
      display: { format: 'text', body: 'Body', presentation: 'modal' },
    });
    expect(
      normalizeDisplayEnvelopeForHost(envelope, 'desktop').display.presentation,
    ).toBe('inline');
  });
});