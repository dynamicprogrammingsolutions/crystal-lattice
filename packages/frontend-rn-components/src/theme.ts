import React from 'react';

export interface Theme {
  typography: {
    fontSize: {
      tiny: number;
      small: number;
      secondary: number;
      normal: number;
      message: number;
      large: number;
      title: number;
      screenTitle: number;
      display: number;
      code: number;
    };
    lineHeight: {
      tiny: number;
      small: number;
      secondary: number;
      normal: number;
      message: number;
      large: number;
      title: number;
      screenTitle: number;
      display: number;
      code: number;
    };
  };
  background: string;
  backgroundAlt: string;
  surface: string;
  surfaceAlt: string;
  primary: string;
  primaryMuted: string;
  border: string;
  divider: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  textOnPrimary: string;
  danger: string;
  dangerMuted: string;
  success: string;
  successMuted: string;
  /** Yellow emphasis used for saved/pinned state, distinct from warning. */
  highlight: string;
  warning: string;
  warningMuted: string;
  notification: string;
  notificationMuted: string;
  message: string;
  bubbleUserBg: string;
  bubbleSystemBorder: string;
  bubbleToolBg: string;
  modalBackdrop: string;
  inlineCodeBg: string;
  codeBlockBg: string;
  navBarBg: string;
  navBarBorder: string;
  navIconActive: string;
  navIconInactive: string;
}

const defaultLightTheme: Theme = {
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
  highlight: '#FFCC00',
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
  codeBlockBg: '#1C1C1E',
  navBarBg: '#FFFFFF',
  navBarBorder: '#E5E5EA',
  navIconActive: '#007AFF',
  navIconInactive: '#8E8E93',
};

const ThemeContext = React.createContext<Theme>(defaultLightTheme);

interface ThemeProviderProps {
  theme: Theme;
  children: React.ReactNode;
}

export function ThemeProvider({ theme, children }: ThemeProviderProps): React.JSX.Element {
  return React.createElement(ThemeContext.Provider, { value: theme }, children);
}

export function useTheme(): Theme {
  return React.useContext(ThemeContext);
}
