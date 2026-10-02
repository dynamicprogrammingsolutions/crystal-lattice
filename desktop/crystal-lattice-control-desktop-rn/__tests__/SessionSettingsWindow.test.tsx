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

jest.mock('../src/native/MacComboBox', () => {
  const React = require('react');
  const { TextInput } = require('react-native');
  return {
    MacComboBox: (props: any) => (
      <TextInput
        testID={props.testID}
        accessibilityLabel={props.accessibilityLabel}
        value={props.inputValue}
        onChangeText={props.onInputValueChange}
        onSubmitEditing={() => props.onSubmit?.(props.inputValue)}
      />
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
          placeholder: 'Search models or enter a model ID',
          custom_value: {
            enabled: true,
            pattern: '^[^\\s]+$',
            option_label: "Use '{value}' as a custom model ID",
          },
        },
        {
          ui_type: 'config',
          key: 'include_crystal_lattice_access',
          type: 'checkbox',
          label: 'Include Crystal Lattice Access Guidance (CLI only)',
          description:
            'CLI-only guidance is available; Python SDK guidance is unavailable.',
          disabled: false,
        },
        {
          ui_type: 'config',
          key: 'crystal_lattice_access_unavailable_fixture',
          type: 'checkbox',
          label: 'Include Crystal Lattice Access Guidance (unavailable)',
          description:
            'Unavailable because CRYSTAL_LATTICE_CLI_COMMAND is missing.',
          disabled: true,
        },
      ],
      actions: [],
      overrides: {},
      configSchema: [
        { key: 'model', type: 'string' },
        { key: 'include_crystal_lattice_access', type: 'boolean', default: false },
        {
          key: 'crystal_lattice_access_unavailable_fixture',
          type: 'boolean',
          default: false,
        },
      ],
      baseConfig: {
        model: 'claude-a',
        include_crystal_lattice_access: false,
        crystal_lattice_access_unavailable_fixture: false,
      },
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

test('renders a custom dropdown through MacComboBox', async () => {
  render(<SessionSettingsWindow />);

  const dropdown = screen.getByTestId('session-setting-dropdown-model');
  expect(dropdown).toBeTruthy();
  expect(screen.getByDisplayValue('claude-a')).toBeTruthy();
  expect(
    screen.getByText('Include Crystal Lattice Access Guidance (CLI only)'),
  ).toBeTruthy();
  expect(
    screen.getByText(
      'CLI-only guidance is available; Python SDK guidance is unavailable.',
    ),
  ).toBeTruthy();
  expect(
    screen.getByText('Include Crystal Lattice Access Guidance (unavailable)'),
  ).toBeTruthy();
  expect(
    screen.getByText(
      'Unavailable because CRYSTAL_LATTICE_CLI_COMMAND is missing.',
    ),
  ).toBeTruthy();
  expect(
    screen.getByTestId(
      'session-setting-checkbox-crystal_lattice_access_unavailable_fixture',
    ).props.disabled,
  ).toBe(true);
});

test('does not patch a disabled access setting', () => {
  render(<SessionSettingsWindow />);

  fireEvent(
    screen.getByTestId(
      'session-setting-checkbox-crystal_lattice_access_unavailable_fixture',
    ),
    'valueChange',
    true,
  );

  expect(patchOverride).not.toHaveBeenCalledWith(
    'crystal_lattice_access_unavailable_fixture',
    true,
  );
});

test('patches an arbitrary model from the desktop dropdown editor', async () => {
  render(<SessionSettingsWindow />);

  fireEvent.changeText(
    screen.getByTestId('session-setting-dropdown-model'),
    'vendor/custom-model',
  );
  fireEvent(
    screen.getByTestId('session-setting-dropdown-model'),
    'submitEditing',
  );

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith('model', 'vendor/custom-model');
  });
});
