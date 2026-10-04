import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';
import type { MacOSSystemThemePayload } from '../src/theme/types';

function payload(
  appearance: 'light' | 'dark',
  accent: string,
  background: string,
): MacOSSystemThemePayload {
  return {
    appearance,
    accent,
    windowBackground: background,
    controlBackground: background,
    separator:
      appearance === 'dark'
        ? 'rgba(255, 255, 255, 0.2)'
        : 'rgba(0, 0, 0, 0.2)',
    text: appearance === 'dark' ? '#FFFFFF' : '#000000',
    textSecondary: appearance === 'dark' ? '#D1D1D6' : '#3A3A3C',
    textMuted: '#8E8E93',
    danger: appearance === 'dark' ? '#FF453A' : '#FF3B30',
    success: appearance === 'dark' ? '#32D74B' : '#34C759',
    warning: appearance === 'dark' ? '#FF9F0A' : '#FF9500',
    notification: accent,
  };
}

test('derives readable user-bubble text from the effective dynamic background', () => {
  const light = buildDesktopTheme(payload('light', '#FFFFFF', '#FFFFFF'));
  const dark = buildDesktopTheme(payload('dark', '#000000', '#000000'));

  expect(light.bubbleUserText).toBe('#000000');
  expect(dark.bubbleUserText).toBe('#FFFFFF');
});