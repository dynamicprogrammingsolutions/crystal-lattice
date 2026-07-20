import { useColorScheme } from 'react-native';

import {
  ThemeProvider,
  useTheme,
  type Theme,
} from '@crystal-lattice/frontend-rn-components';

export { ThemeProvider, useTheme };
export type { Theme };

export const lightTheme: Theme = {
  typography: {
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
  },
  background: '#F2F2F7',
  backgroundAlt: '#FFFFFF',
  surface: '#FFFFFF',
  surfaceAlt: '#F2F2F7',
  primary: '#007AFF',
  primaryMuted: 'rgba(0, 122, 255, 0.1)',
  border: '#E5E5EA',
  divider: '#E5E5EA',
  text: '#000000',
  textSecondary: '#8E8E93',
  textMuted: '#8E8E93',
  textOnPrimary: '#FFFFFF',
  danger: '#FF3B30',
  dangerMuted: 'rgba(255, 59, 48, 0.12)',
  success: '#34C759',
  successMuted: 'rgba(52, 199, 89, 0.12)',
  warning: '#FF9500',
  warningMuted: 'rgba(255, 149, 0, 0.12)',
  notification: '#007AFF',
  notificationMuted: 'rgba(0, 122, 255, 0.12)',
  message: '#0A84FF',
  bubbleUserBg: 'rgba(0, 122, 255, 0.12)',
  bubbleSystemBorder: '#E5E5EA',
  bubbleToolBg: 'rgba(142, 142, 147, 0.08)',
  modalBackdrop: 'rgba(0, 0, 0, 0.3)',
  inlineCodeBg: 'rgba(142, 142, 147, 0.16)',
  codeBlockBg: '#FFFFFF',
  navBarBg: '#FFFFFF',
  navBarBorder: '#E5E5EA',
  navIconActive: '#007AFF',
  navIconInactive: '#8E8E93',
};

export const darkTheme: Theme = {
  typography: {
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
  },
  background: '#000000',
  backgroundAlt: '#1C1C1E',
  surface: '#1C1C1E',
  surfaceAlt: '#2C2C2E',
  primary: '#0A84FF',
  primaryMuted: 'rgba(10, 132, 255, 0.2)',
  border: '#3A3A3C',
  divider: '#3A3A3C',
  text: '#FFFFFF',
  textSecondary: '#D1D1D6',
  textMuted: '#8E8E93',
  textOnPrimary: '#FFFFFF',
  danger: '#FF453A',
  dangerMuted: 'rgba(255, 69, 58, 0.22)',
  success: '#32D74B',
  successMuted: 'rgba(50, 215, 75, 0.22)',
  warning: '#FF9F0A',
  warningMuted: 'rgba(255, 159, 10, 0.22)',
  notification: '#0A84FF',
  notificationMuted: 'rgba(10, 132, 255, 0.22)',
  message: '#0A84FF',
  bubbleUserBg: '#0040A5',
  bubbleSystemBorder: '#3A3A3C',
  bubbleToolBg: 'rgba(142, 142, 147, 0.25)',
  modalBackdrop: 'rgba(0, 0, 0, 0.4)',
  inlineCodeBg: 'rgba(142, 142, 147, 0.5)',
  codeBlockBg: '#1C1C1E',
  navBarBg: '#1C1C1E',
  navBarBorder: '#3A3A3C',
  navIconActive: '#0A84FF',
  navIconInactive: '#8E8E93',
};

export function useSystemTheme(): Theme {
  const scheme = useColorScheme();
  return scheme === 'dark' ? darkTheme : lightTheme;
}
