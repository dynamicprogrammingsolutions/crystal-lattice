import React from 'react';

export interface Theme {
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
  success: string;
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
  success: '#34C759',
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
