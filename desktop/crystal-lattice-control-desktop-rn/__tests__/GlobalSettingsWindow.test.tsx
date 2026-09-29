import React from 'react';
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

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
      timeTrackingEnabled: true,
      timeTrackingPluginId: 'duration_tracking_app',
      timeTrackingInactivitySeconds: 30,
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
import { desktopHumanTimeDiagnosticsBridge } from '../src/humanTimeTelemetry/desktopHumanTimeDiagnostics';

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
      timeTrackingEnabled: true,
      timeTrackingPluginId: 'duration_tracking_app',
      timeTrackingInactivitySeconds: 30,
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

  const trackingDisabled = applyDesktopGlobalSettingChange(
    switchEnabled,
    'timeTrackingEnabled',
    false,
    mockSetDesktopGlobalSetting,
  );
  expect(trackingDisabled.timeTrackingEnabled).toBe(false);
  expect(mockSetDesktopGlobalSetting).toHaveBeenCalledWith({
    key: 'timeTrackingEnabled',
    value: false,
  });

  const customPlugin = applyDesktopGlobalSettingChange(
    trackingDisabled,
    'timeTrackingPluginId',
    'custom_duration',
    mockSetDesktopGlobalSetting,
  );
  expect(customPlugin.timeTrackingPluginId).toBe('custom_duration');
  expect(mockSetDesktopGlobalSetting).toHaveBeenCalledWith({
    key: 'timeTrackingPluginId',
    value: 'custom_duration',
  });

  const longerInactivity = applyDesktopGlobalSettingChange(
    customPlugin,
    'timeTrackingInactivitySeconds',
    60,
    mockSetDesktopGlobalSetting,
  );
  expect(longerInactivity.timeTrackingInactivitySeconds).toBe(60);
  expect(mockSetDesktopGlobalSetting).toHaveBeenCalledWith({
    key: 'timeTrackingInactivitySeconds',
    value: 60,
  });
});

test('shows compact aggregate telemetry diagnostics with connection context', async () => {
  desktopHumanTimeDiagnosticsBridge.publish({
    enabled: true,
    connectedConnectionCount: 2,
    activityEventCount: 3,
    openSpan: null,
    lastCollectedSpan: null,
    pendingCount: 1,
    lastUpload: null,
    recentEntries: [
      {
        connectionId: 'ireland',
        sessionId: 'session-1',
        from: '2026-09-24T10:00:00.000Z',
        to: '2026-09-24T10:01:00.000Z',
        uploadStatus: 'failed',
        error: 'rejected',
      },
    ],
    collectionError: null,
  });

  render(<GlobalSettingsWindow />);
  await waitFor(() =>
    expect(
      screen.getByTestId('global-settings-time-tracking-toggle'),
    ).toBeTruthy(),
  );
  fireEvent.press(
    screen.getByTestId('global-settings-time-tracking-diagnostics'),
  );

  expect(screen.getByText('Connected servers: 2')).toBeTruthy();
  expect(screen.getByText('Pending uploads: 1')).toBeTruthy();
  expect(screen.getByText('ireland')).toBeTruthy();
  expect(screen.getByText('session-1')).toBeTruthy();
  expect(screen.getByText('1m 0s')).toBeTruthy();
});
