import type { Theme } from '@crystal-lattice/frontend-rn-components';

import type { MacOSSystemThemePayload } from './types';
import { mixColors, pickTextOnColor, scaleAlpha, withAlpha } from './colorUtils';

const TYPOGRAPHY: Theme['typography'] = {
  fontSize: {
    tiny: 11,
    small: 12,
    secondary: 13,
    normal: 14,
    message: 15,
    large: 16,
    title: 18,
    screenTitle: 24,
    display: 28,
    code: 14,
  },
  lineHeight: {
    tiny: 15,
    small: 17,
    secondary: 18,
    normal: 20,
    message: 21,
    large: 22,
    title: 24,
    screenTitle: 30,
    display: 34,
    code: 19,
  },
};

const FALLBACK_LIGHT: Theme = {
  typography: TYPOGRAPHY,
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
  dangerMuted: 'rgba(255, 59, 48, 0.12)',
  success: '#34C759',
  successMuted: 'rgba(52, 199, 89, 0.12)',
  highlight: '#FFCC00',
  warning: '#FF9500',
  warningMuted: 'rgba(255, 149, 0, 0.12)',
  notification: '#007AFF',
  notificationMuted: 'rgba(0, 122, 255, 0.12)',
  message: '#0A84FF',
  bubbleUserBg: 'rgba(0, 122, 255, 0.12)',
  bubbleSystemBorder: '#D1D1D6',
  bubbleToolBg: 'rgba(142, 142, 147, 0.08)',
  modalBackdrop: 'rgba(0, 0, 0, 0.25)',
  inlineCodeBg: 'rgba(142, 142, 147, 0.16)',
  codeBlockBg: '#FFFFFF',
  navBarBg: '#FFFFFF',
  navBarBorder: '#D1D1D6',
  navIconActive: '#007AFF',
  navIconInactive: '#8E8E93',
};

const FALLBACK_DARK: Theme = {
  typography: TYPOGRAPHY,
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
  dangerMuted: 'rgba(255, 69, 58, 0.22)',
  success: '#32D74B',
  successMuted: 'rgba(50, 215, 75, 0.22)',
  highlight: '#FFD60A',
  warning: '#FF9F0A',
  warningMuted: 'rgba(255, 159, 10, 0.22)',
  notification: '#0A84FF',
  notificationMuted: 'rgba(10, 132, 255, 0.22)',
  message: '#0A84FF',
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

  const notification = payload.notification || primary;
  const notificationMuted = withAlpha(notification, isDark ? 0.22 : 0.12);
  const warning = payload.warning || (isDark ? '#FF9F0A' : '#FF9500');
  const warningMuted = withAlpha(warning, isDark ? 0.22 : 0.12);
  const danger = payload.danger;
  const dangerMuted = withAlpha(danger, isDark ? 0.22 : 0.12);
  const success = payload.success;
  const successMuted = withAlpha(success, isDark ? 0.22 : 0.12);
  const highlight = isDark ? '#FFD60A' : '#FFCC00';
  const message = notification;

  const border = scaleAlpha(payload.separator, isDark ? 1.55 : 1.85);
  const divider = scaleAlpha(payload.separator, isDark ? 1.85 : 2.25);

  const surfaceAlt = mixColors(surface, background, isDark ? 0.22 : 0.14);
  const backgroundAlt = mixColors(background, surface, isDark ? 0.16 : 0.22);

  return {
    typography: TYPOGRAPHY,
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
    danger,
    dangerMuted,
    success,
    successMuted,
    highlight,
    warning,
    warningMuted,
    notification,
    notificationMuted,
    message,
    bubbleUserBg: withAlpha(primary, isDark ? 0.22 : 0.12),
    bubbleSystemBorder: border,
    bubbleToolBg: withAlpha(payload.textSecondary, isDark ? 0.18 : 0.08),
    modalBackdrop: isDark ? 'rgba(0, 0, 0, 0.45)' : 'rgba(0, 0, 0, 0.25)',
    inlineCodeBg: withAlpha(payload.textSecondary, isDark ? 0.35 : 0.16),
    codeBlockBg: isDark ? '#1C1C1E' : '#FFFFFF',
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
