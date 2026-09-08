import React from 'react';
import { render, screen, waitFor } from '@testing-library/react-native';

const mockSetDesktopGlobalSetting = jest.fn();

jest.mock('../src/windows/desktopWindowManager', () => ({
  DesktopWindowManager: {
    getDesktopGlobalSettings: jest.fn(async () => ({
      baseFontSize: 16,
      headerSize: 'small',
      recentSessionsWindow: '1w',
      sessionDoubleClickAction: 'open',
    })),
    setDesktopGlobalSetting: mockSetDesktopGlobalSetting,
    closeReactWindow: jest.fn(),
  },
  desktopWindowEvents: null,
}));

import {
  applyDesktopGlobalSettingChange,
  GlobalSettingsWindow,
} from '../src/windows/GlobalSettingsWindow';

test('loads native global settings and writes double-click changes through native authority', async () => {
  render(<GlobalSettingsWindow />);
  await waitFor(() =>
    expect(screen.getByText('Open permanent tab')).toBeTruthy(),
  );
  expect(screen.getByText('Open permanent tab')).toBeTruthy();

  const next = applyDesktopGlobalSettingChange(
    {
      baseFontSize: 16,
      headerSize: 'small',
      recentSessionsWindow: '1w',
      sessionDoubleClickAction: 'open',
    },
    'sessionDoubleClickAction',
    'preview',
    mockSetDesktopGlobalSetting,
  );
  expect(next.sessionDoubleClickAction).toBe('preview');
  expect(mockSetDesktopGlobalSetting).toHaveBeenCalledWith({
    key: 'sessionDoubleClickAction',
    value: 'preview',
  });
});
