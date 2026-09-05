import { describe, expect, it } from 'vitest';

import {
  classifyDisplayEnvelope,
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

  it('normalizes desktop notification modals to inline', () => {
    const notification = normalizeDisplayEnvelope({
      source: 'session_notification',
      display: { format: 'text', body: 'Body', presentation: 'modal' },
    });
    expect(
      normalizeDisplayEnvelopeForHost(notification, 'desktop').display.presentation,
    ).toBe('inline');

    const action = normalizeDisplayEnvelope({
      source: 'action_response',
      display: { format: 'text', body: 'Body', presentation: 'modal' },
    });
    expect(
      normalizeDisplayEnvelopeForHost(action, 'desktop').display.presentation,
    ).toBe('modal');
  });

  it('classifies connection and session display ownership', () => {
    expect(
      classifyDisplayEnvelope(
        normalizeDisplayEnvelope({
          source: 'application_notification',
          connectionId: 'connection-1',
          display: { format: 'text', body: 'Application' },
        }),
      ),
    ).toEqual({ scope: 'connection', connectionId: 'connection-1' });
    expect(
      classifyDisplayEnvelope(
        normalizeDisplayEnvelope({
          source: 'action_response',
          connectionId: 'connection-1',
          sessionId: 'session-1',
          display: { format: 'text', body: 'Session action' },
        }),
      ),
    ).toEqual({
      scope: 'session',
      connectionId: 'connection-1',
      sessionId: 'session-1',
    });
    expect(
      classifyDisplayEnvelope(
        normalizeDisplayEnvelope({
          source: 'action_response',
          ownershipScope: 'connection',
          connectionId: 'connection-1',
          sessionId: 'session-1',
          display: { format: 'text', body: 'Session-list action' },
        }),
      ),
    ).toEqual({ scope: 'connection', connectionId: 'connection-1' });
  });

  it('rejects session notifications without session ownership', () => {
    expect(() =>
      classifyDisplayEnvelope({
        id: 'notification-1',
        source: 'session_notification',
        display: {
          format: 'text',
          body: 'Missing session',
          presentation: 'inline',
        },
      }),
    ).toThrow('Session notification display requires sessionId');
  });
});