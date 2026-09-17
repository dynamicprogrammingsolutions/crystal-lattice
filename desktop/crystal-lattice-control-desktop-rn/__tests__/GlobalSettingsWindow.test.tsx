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
      sessionsFollowActiveTabEnabled: true,
      switchConnectionWithActiveTabEnabled: false,
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
      sessionsFollowActiveTabEnabled: true,
      switchConnectionWithActiveTabEnabled: false,
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

  const followDisabled = applyDesktopGlobalSettingChange(
    next,
    'sessionsFollowActiveTabEnabled',
    false,
    mockSetDesktopGlobalSetting,
  );
  expect(followDisabled.sessionsFollowActiveTabEnabled).toBe(false);
  expect(mockSetDesktopGlobalSetting).toHaveBeenCalledWith({
    key: 'sessionsFollowActiveTabEnabled',
    value: false,
  });

  const switchEnabled = applyDesktopGlobalSettingChange(
    followDisabled,
    'switchConnectionWithActiveTabEnabled',
    true,
    mockSetDesktopGlobalSetting,
  );
  expect(switchEnabled.switchConnectionWithActiveTabEnabled).toBe(true);
  expect(mockSetDesktopGlobalSetting).toHaveBeenCalledWith({
    key: 'switchConnectionWithActiveTabEnabled',
    value: true,
  });
  expect(screen.getByText('On')).toBeTruthy();
  expect(screen.getByText('Off')).toBeTruthy();
});
