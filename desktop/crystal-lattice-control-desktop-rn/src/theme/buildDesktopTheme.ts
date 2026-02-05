import type { Theme } from '@crystal-lattice/frontend-rn-components';

import type { MacOSSystemThemePayload } from './types';
import { mixColors, pickTextOnColor, scaleAlpha, withAlpha } from './colorUtils';

const FALLBACK_LIGHT: Theme = {
  background: '#F2F2F7',
  backgroundAlt: '#FFFFFF',
  surface: '#FFFFFF',
  surfaceAlt: '#F2F2F7',
  primary: '#007AFF',
  primaryMuted: 'rgba(0, 122, 255, 0.1)',
  border: '#D1D1D6',
  divider: '#D1D1D6',
  text: '#000000',
  textSecondary: '#3A3A3C',
  textMuted: '#8E8E93',
  textOnPrimary: '#FFFFFF',
  danger: '#FF3B30',
  success: '#34C759',
  bubbleUserBg: 'rgba(0, 122, 255, 0.12)',
  bubbleSystemBorder: '#D1D1D6',
  bubbleToolBg: 'rgba(142, 142, 147, 0.08)',
  modalBackdrop: 'rgba(0, 0, 0, 0.25)',
  inlineCodeBg: 'rgba(142, 142, 147, 0.16)',
  codeBlockBg: '#1C1C1E',
  navBarBg: '#FFFFFF',
  navBarBorder: '#D1D1D6',
  navIconActive: '#007AFF',
  navIconInactive: '#8E8E93',
};

const FALLBACK_DARK: Theme = {
  background: '#000000',
  backgroundAlt: '#1C1C1E',
  surface: '#1C1C1E',
  surfaceAlt: '#2C2C2E',
  primary: '#0A84FF',
  primaryMuted: 'rgba(10, 132, 255, 0.2)',
  border: '#5A5A5E',
  divider: '#5A5A5E',
  text: '#FFFFFF',
  textSecondary: '#D1D1D6',
  textMuted: '#8E8E93',
  textOnPrimary: '#FFFFFF',
  danger: '#FF453A',
  success: '#32D74B',
  bubbleUserBg: '#0040A5',
  bubbleSystemBorder: '#5A5A5E',
  bubbleToolBg: 'rgba(142, 142, 147, 0.25)',
  modalBackdrop: 'rgba(0, 0, 0, 0.45)',
  inlineCodeBg: 'rgba(142, 142, 147, 0.5)',
  codeBlockBg: '#1C1C1E',
  navBarBg: '#1C1C1E',
  navBarBorder: '#5A5A5E',
  navIconActive: '#0A84FF',
  navIconInactive: '#8E8E93',
};

export function buildDesktopTheme(payload: MacOSSystemThemePayload | null): Theme {
  if (!payload) {
    return FALLBACK_LIGHT;
  }

  const appearance = payload.appearance;
  const isDark = appearance === 'dark';

  const background = payload.windowBackground;
  const surface = payload.controlBackground;

  const primary = payload.accent;
  const textOnPrimary = pickTextOnColor(primary);
  const primaryMuted = withAlpha(primary, isDark ? 0.22 : 0.12);

  const border = scaleAlpha(payload.separator, isDark ? 1.55 : 1.85);
  const divider = scaleAlpha(payload.separator, isDark ? 1.85 : 2.25);

  const surfaceAlt = mixColors(surface, background, isDark ? 0.22 : 0.14);
  const backgroundAlt = mixColors(background, surface, isDark ? 0.16 : 0.22);

  return {
    background,
    backgroundAlt,
    surface,
    surfaceAlt,
    primary,
    primaryMuted,
    border,
    divider,
    text: payload.text,
    textSecondary: payload.textSecondary,
    textMuted: payload.textMuted,
    textOnPrimary,
    danger: payload.danger,
    success: payload.success,
    bubbleUserBg: withAlpha(primary, isDark ? 0.22 : 0.12),
    bubbleSystemBorder: border,
    bubbleToolBg: withAlpha(payload.textSecondary, isDark ? 0.18 : 0.08),
    modalBackdrop: isDark ? 'rgba(0, 0, 0, 0.45)' : 'rgba(0, 0, 0, 0.25)',
    inlineCodeBg: withAlpha(payload.textSecondary, isDark ? 0.35 : 0.16),
    codeBlockBg: '#1C1C1E',
    navBarBg: surface,
    navBarBorder: border,
    navIconActive: primary,
    navIconInactive: payload.textMuted,
  };
}

export function buildDesktopThemeWithFallback(
  payload: MacOSSystemThemePayload | null,
  fallbackAppearance: 'light' | 'dark',
): Theme {
  if (payload) {
    return buildDesktopTheme(payload);
  }
  return fallbackAppearance === 'dark' ? FALLBACK_DARK : FALLBACK_LIGHT;
}
