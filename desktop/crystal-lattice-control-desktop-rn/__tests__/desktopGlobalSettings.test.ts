import {
  complementarySessionOpenMode,
  normalizeDesktopGlobalSettings,
} from '../src/settings/desktopGlobalSettings';
import {
  resolveExplicitSessionOpenMode,
  resolveSessionItemClick,
} from '../src/sessions/sessionItemInteraction';

describe('desktop global session interaction settings', () => {
  it('defaults double-click to preview and exposes the complementary action', () => {
    const settings = normalizeDesktopGlobalSettings(null);
    expect(settings.sessionDoubleClickAction).toBe('preview');
    expect(settings.sessionsFollowActiveTabEnabled).toBe(false);
    expect(
      complementarySessionOpenMode(settings.sessionDoubleClickAction),
    ).toBe('open');
  });

  it('keeps first click light and dispatches configured action on second click', () => {
    const first = resolveSessionItemClick({
      previous: null,
      key: 'connection:session',
      nowMs: 100,
      doubleClickAction: 'preview',
    });
    expect(first.openMode).toBeNull();
    const second = resolveSessionItemClick({
      previous: first.next,
      key: 'connection:session',
      nowMs: 250,
      doubleClickAction: 'preview',
    });
    expect(second.openMode).toBe('preview');

    expect(
      resolveSessionItemClick({
        previous: first.next,
        key: 'connection:session',
        nowMs: 250,
        doubleClickAction: 'open',
      }).openMode,
    ).toBe('open');
  });

  it('uses Open for an existing preview or permanent tab', () => {
    expect(resolveExplicitSessionOpenMode('open', null)).toBe('preview');
    expect(resolveExplicitSessionOpenMode('preview', null)).toBe('open');
    expect(resolveExplicitSessionOpenMode('preview', 'preview')).toBe('open');
    expect(resolveExplicitSessionOpenMode('open', 'permanent')).toBe('open');
  });

  it('normalizes only an explicit true follow preference as enabled', () => {
    expect(
      normalizeDesktopGlobalSettings({
        sessionsFollowActiveTabEnabled: true,
      }).sessionsFollowActiveTabEnabled,
    ).toBe(true);
    expect(
      normalizeDesktopGlobalSettings({
        sessionsFollowActiveTabEnabled: 'true',
      }).sessionsFollowActiveTabEnabled,
    ).toBe(false);
  });
});
