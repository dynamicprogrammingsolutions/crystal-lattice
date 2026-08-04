import React from 'react';
import { render, screen } from '@testing-library/react-native';

import { useServerSettingsForm } from '@crystal-lattice/frontend-sdk-react';

import { ServerSettingsWindow } from '../src/windows/ServerSettingsWindow';
import { setActiveServerSettingsWindow } from '../src/windows/serverSettingsCoordinator';

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-sdk-react');
  return {
    ...actual,
    useServerSettingsForm: jest.fn(),
  };
});

const mockUseServerSettingsForm =
  useServerSettingsForm as jest.MockedFunction<typeof useServerSettingsForm>;

afterEach(() => setActiveServerSettingsWindow(null));

test('renders server settings in a separate desktop window surface', () => {
  mockUseServerSettingsForm.mockReturnValue({
    controller: {
      patchSetting: jest.fn(),
      deleteSetting: jest.fn(),
    } as any,
    state: {
      elements: [],
      settings: {},
      baseConfig: {},
      loading: false,
      refreshing: false,
      error: null,
      savingKeys: [],
      statusMessage: null,
      statusTone: 'idle',
      lastSavedAt: null,
      lastLoadedAt: null,
    },
    items: [],
    savingKeys: new Set(),
  });
  setActiveServerSettingsWindow({
    id: 'server-settings:connection',
    connectionId: 'connection',
    connectionName: 'Local server',
    backend: {} as any,
  });

  render(<ServerSettingsWindow />);
  expect(screen.getByText('Server settings')).toBeTruthy();
  expect(screen.getByText('Local server')).toBeTruthy();
  expect(screen.getByLabelText('Close server settings')).toBeTruthy();
});