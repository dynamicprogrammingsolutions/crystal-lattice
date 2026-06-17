import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';

import ServerSettingsModal from '../src/components/ServerSettingsModal';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import { useServerSettingsController } from '@crystal-lattice/frontend-sdk-react';

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-sdk-react');
  return {
    __esModule: true,
    ...actual,
    useServerSettingsController: jest.fn(),
  };
});

const mockedUseServerSettingsController =
  useServerSettingsController as jest.MockedFunction<typeof useServerSettingsController>;

const patchSetting = jest.fn<Promise<void>, [string, unknown]>(async () => {});
const deleteSetting = jest.fn<Promise<void>, [string]>(async () => {});

function renderModal() {
  mockedUseServerSettingsController.mockReturnValue({
    controller: {
      patchSetting,
      deleteSetting,
    } as any,
    state: {
      elements: [
        {
          ui_type: 'config',
          scope: 'server',
          key: 'dummy_server_mode',
          type: 'select',
          label: 'Dummy server mode',
          options: [
            { value: 'fast', label: 'Fast' },
            { value: 'careful', label: 'Careful' },
          ],
        },
        {
          ui_type: 'config',
          scope: 'server',
          key: 'dummy_server_enabled',
          type: 'checkbox',
          label: 'Dummy server enabled',
        },
        {
          ui_type: 'config',
          scope: 'server',
          key: 'dummy_server_name',
          type: 'text',
          label: 'Dummy server name',
        },
      ],
      settings: {
        dummy_server_mode: 'fast',
        dummy_server_name: 'Alpha',
      },
      baseConfig: {},
      loading: false,
      refreshing: false,
      savingKeys: [],
      error: null,
      statusMessage: null,
      statusTone: 'idle',
      lastSavedAt: null,
      lastLoadedAt: 1,
    },
  });

  return renderWithMobileProviders(
    <ServerSettingsModal
      backend={{ kind: 'rest' } as any}
      visible
      onRequestClose={jest.fn()}
    />,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

test('server settings modal renders generic controls', () => {
  renderModal();

  expect(screen.getByText('Server settings')).toBeTruthy();
  expect(screen.getByText('Dummy server mode')).toBeTruthy();
  expect(screen.getByText('Fast')).toBeTruthy();
  expect(screen.getByText('Careful')).toBeTruthy();
  expect(screen.getByText('Dummy server enabled')).toBeTruthy();
  expect(screen.getByText('Dummy server name')).toBeTruthy();
  expect(screen.getByDisplayValue('Alpha')).toBeTruthy();
});

test('server settings modal patches select and text values', async () => {
  renderModal();

  fireEvent.press(screen.getByText('Careful'));
  await waitFor(() => {
    expect(patchSetting).toHaveBeenCalledWith('dummy_server_mode', 'careful');
  });

  fireEvent.changeText(screen.getByDisplayValue('Alpha'), 'Beta');
  fireEvent.press(screen.getByText('Save'));
  await waitFor(() => {
    expect(patchSetting).toHaveBeenCalledWith('dummy_server_name', 'Beta');
  });
});