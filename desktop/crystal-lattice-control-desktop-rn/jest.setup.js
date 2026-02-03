jest.mock(
  '@react-native-async-storage/async-storage',
  () => require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
);

jest.mock('@crystal-lattice/frontend-sdk', () => ({
  CONNECTIONS_STORAGE_KEY: 'clc_connections_v1',
  loadConnections: async () => [],
  saveConnections: async () => {},
}));

jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const React = require('react');
  const theme = {
    background: '#fff',
    backgroundAlt: '#fff',
    surface: '#fff',
    surfaceAlt: '#eee',
    primary: '#007AFF',
    primaryMuted: 'rgba(0, 122, 255, 0.1)',
    border: '#ddd',
    divider: '#ddd',
    text: '#000',
    textSecondary: '#666',
    textMuted: '#666',
    textOnPrimary: '#fff',
    danger: '#f00',
    success: '#0a0',
    bubbleUserBg: '#fff',
    bubbleSystemBorder: '#ddd',
    bubbleToolBg: '#fff',
    modalBackdrop: 'rgba(0,0,0,0.2)',
    inlineCodeBg: '#eee',
    codeBlockBg: '#000',
    navBarBg: '#fff',
    navBarBorder: '#ddd',
    navIconActive: '#007AFF',
    navIconInactive: '#666',
  };

  return {
    ThemeProvider: ({ children }: { children: any }) => React.createElement(React.Fragment, null, children),
    useSystemTheme: () => theme,
    useTheme: () => theme,
    DropdownMenuSurface: ({ visible, children }: { visible: boolean; children: any }) =>
      visible ? React.createElement(React.Fragment, null, children) : null,
  };
});
