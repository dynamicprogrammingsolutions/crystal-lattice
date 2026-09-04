import React from 'react';
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

import { useSessionSettingsController } from '@crystal-lattice/frontend-sdk-react';

import { SessionSettingsWindow } from '../src/windows/SessionSettingsWindow';
import {
  clearActiveSessionSettingsWindow,
  setActiveSessionSettingsWindow,
} from '../src/windows/sessionSettingsCoordinator';

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-sdk-react');
  return {
    ...actual,
    useSessionSettingsController: jest.fn(),
  };
});

jest.mock('../src/native/MacSelect', () => {
  const React = require('react');
  const { Pressable, Text } = require('react-native');
  return {
    MacSelect: (props: any) => (
      <Pressable
        testID={props.testID}
        accessibilityLabel={props.accessibilityLabel}
        onPress={() => props.onValueChange?.('claude-b')}
      >
        <Text>{props.selectedValue || props.placeholder}</Text>
      </Pressable>
    ),
  };
});

const mockedUseSessionSettingsController =
  useSessionSettingsController as jest.MockedFunction<
    typeof useSessionSettingsController
  >;

const patchOverride = jest.fn(async () => {});
const deleteOverride = jest.fn(async () => {});

beforeEach(() => {
  jest.clearAllMocks();
  mockedUseSessionSettingsController.mockReturnValue({
    controller: {
      patchOverride,
      deleteOverride,
    } as any,
    state: {
      elements: [
        {
          ui_type: 'config',
          key: 'model',
          type: 'dropdown',
          label: 'Model',
          options: [
            { value: 'claude-a', label: 'Claude A' },
            { value: 'claude-b', label: 'Claude B' },
          ],
          allow_custom_value: true,
          custom_value_label: 'Other model…',
          custom_value_placeholder: 'Enter a model ID',
        },
      ],
      overrides: {},
      configSchema: [{ key: 'model', type: 'string' }],
      baseConfig: { model: 'claude-a' },
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
  setActiveSessionSettingsWindow({
    state: {
      id: 'session-settings:test',
      connectionId: 'connection',
      connectionName: 'Test',
      sessionId: 'session',
      backend: {} as any,
    },
  });
});

afterEach(() => {
  clearActiveSessionSettingsWindow();
});

test('renders dropdown through MacSelect and patches a declared option', async () => {
  render(<SessionSettingsWindow />);

  const dropdown = screen.getByTestId('session-setting-dropdown-model');
  expect(dropdown).toBeTruthy();
  expect(screen.queryByDisplayValue('claude-a')).toBeNull();

  fireEvent.press(dropdown);

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith('model', 'claude-b');
  });
});

test('patches an arbitrary model from the desktop dropdown editor', async () => {
  render(<SessionSettingsWindow />);

  fireEvent.changeText(
    screen.getByTestId('session-setting-dropdown-model-custom-input'),
    'vendor/custom-model',
  );
  fireEvent.press(
    screen.getByTestId('session-setting-dropdown-model-custom-save'),
  );

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith('model', 'vendor/custom-model');
  });
});
