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
    expect(settings.sessionsFollowActiveTabEnabled).toBe(true);
    expect(settings.switchConnectionWithActiveTabEnabled).toBe(false);
    expect(settings.timeTrackingEnabled).toBe(false);
    expect(settings.timeTrackingPluginId).toBe('duration_tracking_app');
    expect(settings.timeTrackingInactivitySeconds).toBe(30);
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

  it('preserves explicit navigation booleans and otherwise uses their defaults', () => {
    expect(
      normalizeDesktopGlobalSettings({
        sessionsFollowActiveTabEnabled: true,
      }).sessionsFollowActiveTabEnabled,
    ).toBe(true);
    expect(
      normalizeDesktopGlobalSettings({
        sessionsFollowActiveTabEnabled: false,
      }).sessionsFollowActiveTabEnabled,
    ).toBe(false);
    expect(
      normalizeDesktopGlobalSettings({
        sessionsFollowActiveTabEnabled: 'false',
      }).sessionsFollowActiveTabEnabled,
    ).toBe(true);
    expect(
      normalizeDesktopGlobalSettings({
        switchConnectionWithActiveTabEnabled: true,
      }).switchConnectionWithActiveTabEnabled,
    ).toBe(true);
    expect(
      normalizeDesktopGlobalSettings({
        switchConnectionWithActiveTabEnabled: 'true',
      }).switchConnectionWithActiveTabEnabled,
    ).toBe(false);
  });

  it('normalizes the desktop inactivity setting', () => {
    expect(
      normalizeDesktopGlobalSettings({
        timeTrackingInactivitySeconds: 60,
      }).timeTrackingInactivitySeconds,
    ).toBe(60);
    expect(
      normalizeDesktopGlobalSettings({
        timeTrackingInactivitySeconds: 0,
      }).timeTrackingInactivitySeconds,
    ).toBe(30);
    expect(
      normalizeDesktopGlobalSettings({
        timeTrackingInactivitySeconds: Number.NaN,
      }).timeTrackingInactivitySeconds,
    ).toBe(30);
  });
});
