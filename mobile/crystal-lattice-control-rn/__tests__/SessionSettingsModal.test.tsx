import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';

import SessionSettingsModal from '../src/components/SessionSettingsModal';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import { useSessionSettingsController } from '@crystal-lattice/frontend-sdk-react';

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-sdk-react');
  return {
    __esModule: true,
    ...actual,
    useSessionSettingsController: jest.fn(),
  };
});

const mockedUseSessionSettingsController =
  useSessionSettingsController as jest.MockedFunction<
    typeof useSessionSettingsController
  >;

const patchOverride = jest.fn<Promise<void>, [string, unknown]>(async () => {});
const deleteOverride = jest.fn<Promise<void>, [string]>(async () => {});
const invalidate = jest.fn();
const load = jest.fn<Promise<void>, []>(async () => {});

function renderSettingsModal() {
  mockedUseSessionSettingsController.mockReturnValue({
    controller: {
      patchOverride,
      deleteOverride,
      invalidate,
      load,
    } as any,
    state: {
      actions: [],
      elements: [
        {
          ui_type: 'config',
          key: 'generic_mode',
          type: 'select',
          label: 'Generic mode',
          description: 'Choose the mode.',
          options: [
            { value: 'fast', label: 'Fast' },
            { value: 'careful', label: 'Careful' },
          ],
        },
        {
          ui_type: 'config',
          key: 'generic_enabled',
          type: 'checkbox',
          label: 'Generic enabled',
          description: 'Turns the generic feature on.',
        },
        {
          ui_type: 'config',
          key: 'include_crystal_lattice_access',
          type: 'checkbox',
          label: 'Include Crystal Lattice Access Guidance (unavailable)',
          description:
            'Unavailable because CRYSTAL_LATTICE_CLI_COMMAND is missing.',
          disabled: true,
        },
        {
          ui_type: 'config',
          key: 'generic_provider',
          type: 'dropdown',
          label: 'Generic provider',
          options: [
            { value: 'local', label: 'Local' },
            { value: 'remote', label: 'Remote' },
          ],
          placeholder: 'Search providers or enter a provider ID',
          custom_value: {
            enabled: true,
            pattern: '^[^\\s]+$',
            option_label: "Use '{value}' as a custom provider ID",
          },
        },
        {
          ui_type: 'config',
          key: 'generic_name',
          type: 'text',
          label: 'Generic name',
        },
        {
          ui_type: 'config',
          key: 'working_directory',
          type: 'directory',
          label: 'Working directory',
          description: 'Choose a workspace directory.',
          placeholder: 'Select a workspace directory',
          options: [
            {
              value: '/app/workspace',
              label: 'Workspace root',
            },
            {
              value: '/app/workspace/projects/alpha',
              label: 'projects/alpha',
            },
          ],
        },
        {
          ui_type: 'config',
          key: 'generic_readonly',
          type: 'readonly',
          label: 'Generic readonly',
        },
        {
          ui_type: 'config',
          key: 'generic_unknown',
          type: 'custom-unknown',
          label: 'Generic fallback',
        },
      ],
      overrides: {
        generic_mode: 'fast',
      },
      configSchema: [
        { key: 'generic_mode', default: 'fast' },
        { key: 'generic_enabled', default: false },
        { key: 'include_crystal_lattice_access', default: false },
        { key: 'generic_provider', default: 'local' },
        { key: 'generic_name', default: 'Alpha' },
        { key: 'working_directory' },
        { key: 'generic_readonly', default: 'Read only value' },
        { key: 'generic_unknown', default: 'Fallback value' },
      ],
      baseConfig: {
        generic_enabled: false,
        include_crystal_lattice_access: false,
        generic_provider: 'local',
        generic_name: 'Alpha',
        working_directory: '/app/workspace',
        generic_readonly: 'Read only value',
        generic_unknown: 'Fallback value',
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

  return renderWithMobileProviders(
    <SessionSettingsModal
      backend={{ kind: 'rest' } as any}
      sessionId="session-1"
      visible
      onRequestClose={jest.fn()}
    />
  );
}

function renderOpenAIAuthSettingsModal(
  overrides: Record<string, unknown> = {}
) {
  mockedUseSessionSettingsController.mockReturnValue({
    controller: {
      patchOverride,
      deleteOverride,
      invalidate,
      load,
    } as any,
    state: {
      actions: [],
      elements: [
        {
          ui_type: 'config',
          key: 'auth_mode',
          type: 'select',
          label: 'OpenAI auth mode',
          options: [
            { value: 'api', label: 'API' },
            { value: 'chatgpt', label: 'ChatGPT' },
          ],
        },
      ],
      overrides,
      configSchema: [{ key: 'auth_mode', default: 'api' }],
      baseConfig: { auth_mode: 'chatgpt' },
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
    <SessionSettingsModal
      backend={{ kind: 'inProcess' } as any}
      sessionId="openai-session"
      visible
      onRequestClose={jest.fn()}
    />
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

test('session settings modal renders generic settings control types', () => {
  renderSettingsModal();

  expect(screen.getByText('Generic mode')).toBeTruthy();
  expect(screen.getByText('Fast')).toBeTruthy();
  expect(screen.getByText('Careful')).toBeTruthy();
  expect(screen.getByText('Generic enabled')).toBeTruthy();
  expect(
    screen.getByText('Include Crystal Lattice Access Guidance (unavailable)')
  ).toBeTruthy();
  expect(
    screen.getByText(
      'Unavailable because CRYSTAL_LATTICE_CLI_COMMAND is missing.'
    )
  ).toBeTruthy();
  expect(
    screen.getByTestId(
      'session-setting-checkbox-include_crystal_lattice_access'
    ).props.disabled
  ).toBe(true);
  expect(screen.getByText('Generic provider:')).toBeTruthy();
  expect(screen.getByText('Local')).toBeTruthy();
  expect(screen.getByText('Generic name')).toBeTruthy();
  expect(screen.getByDisplayValue('Alpha')).toBeTruthy();
  expect(screen.getByText('Working directory')).toBeTruthy();
  expect(screen.getByText('Workspace root')).toBeTruthy();
  expect(screen.queryByText('/app/workspace')).toBeNull();
  expect(screen.getByText('Generic readonly')).toBeTruthy();
  expect(screen.getByText('Read only value')).toBeTruthy();
  expect(screen.getByText('Generic fallback')).toBeTruthy();
  expect(screen.getByDisplayValue('Fallback value')).toBeTruthy();
});

test('disabled session setting cannot patch an override', () => {
  renderSettingsModal();

  fireEvent(
    screen.getByTestId(
      'session-setting-checkbox-include_crystal_lattice_access'
    ),
    'valueChange',
    true
  );

  expect(patchOverride).not.toHaveBeenCalledWith(
    'include_crystal_lattice_access',
    true
  );
});

test('session settings select chips patch generic option values', async () => {
  renderSettingsModal();

  fireEvent.press(screen.getByText('Careful'));

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith('generic_mode', 'careful');
  });
});

test('session OpenAI auth starts from the saved default and supports an override', async () => {
  renderOpenAIAuthSettingsModal();

  expect(screen.queryByText('Auto')).toBeNull();
  expect(
    screen.getByTestId('session-setting-select-auth_mode-chatgpt').props
      .accessibilityState
  ).toEqual(expect.objectContaining({ selected: true }));
  expect(
    screen.getByTestId('session-setting-select-auth_mode-api').props
      .accessibilityState
  ).toEqual(expect.objectContaining({ selected: false }));

  fireEvent.press(screen.getByTestId('session-setting-select-auth_mode-api'));

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith('auth_mode', 'api');
  });
});

test('session OpenAI auth override is shown independently from the saved default', () => {
  renderOpenAIAuthSettingsModal({ auth_mode: 'api' });

  expect(
    screen.getByTestId('session-setting-select-auth_mode-api').props
      .accessibilityState
  ).toEqual(expect.objectContaining({ selected: true }));
  expect(
    screen.getByTestId('session-setting-select-auth_mode-chatgpt').props
      .accessibilityState
  ).toEqual(expect.objectContaining({ selected: false }));
});

test('session settings text controls save generic string values', async () => {
  renderSettingsModal();

  fireEvent.changeText(screen.getByDisplayValue('Alpha'), 'Beta');
  fireEvent.press(screen.getAllByText('Save')[0]);

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith('generic_name', 'Beta');
  });
});

test('session settings dropdown opens and patches selected value', async () => {
  renderSettingsModal();

  fireEvent.press(screen.getByText('Generic provider:'));

  expect(
    screen.getByPlaceholderText('Search providers or enter a provider ID')
  ).toBeTruthy();

  fireEvent.press(screen.getByText('Remote'));

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith('generic_provider', 'remote');
  });
});

test('session settings dropdown patches an arbitrary custom value', async () => {
  renderSettingsModal();

  fireEvent.press(screen.getByText('Generic provider:'));
  fireEvent.changeText(
    screen.getByTestId('options-picker-input'),
    'custom/provider'
  );
  fireEvent.press(
    screen.getByText("Use 'custom/provider' as a custom provider ID")
  );

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith(
      'generic_provider',
      'custom/provider'
    );
  });
});

test('session settings directory opens contained options and persists selection', async () => {
  renderSettingsModal();

  fireEvent.press(
    screen.getByTestId('session-setting-directory-working_directory')
  );
  fireEvent.press(screen.getByText('projects/alpha'));

  await waitFor(() => {
    expect(patchOverride).toHaveBeenCalledWith(
      'working_directory',
      '/app/workspace/projects/alpha'
    );
  });
});

test('session settings renders and executes an action anchored to a field', async () => {
  const executeSessionAction = jest.fn(async () => ({
    status: 'ok' as const,
    plugin: 'openai_responses_prompt_caching',
    action_id: 'regenerate_prompt_cache_key',
    action_owner: 'provider_extension',
    result: {
      mutations: { updated_session_ids: ['session-1'] },
      ui_effects: { reload_session_ids: ['session-1'] },
    },
  }));
  mockedUseSessionSettingsController.mockReturnValue({
    controller: {
      patchOverride,
      deleteOverride,
      invalidate,
      load,
    } as any,
    state: {
      elements: [
        {
          ui_type: 'config',
          key: 'prompt_cache_key',
          type: 'text',
          label: 'Prompt cache key',
        },
      ],
      actions: [
        {
          ui_type: 'session_action',
          plugin: 'openai_responses_prompt_caching',
          id: 'regenerate_prompt_cache_key',
          label: 'Regenerate cache key',
          action_id: 'regenerate_prompt_cache_key',
          action_owner: 'provider_extension',
          param_map: { session_id: '$session.session_id' },
          rich_ui: {
            kind: 'button',
            placements: ['session_settings'],
            anchor_key: 'prompt_cache_key',
            position: 'after',
          },
        },
      ],
      overrides: {},
      configSchema: [{ key: 'prompt_cache_key' }],
      baseConfig: { prompt_cache_key: 'opcache_old' },
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

  renderWithMobileProviders(
    <SessionSettingsModal
      backend={{ executeSessionAction } as any}
      sessionId="session-1"
      visible
      acquireClientValues={async () => ({})}
      onRequestClose={jest.fn()}
    />
  );

  fireEvent.press(
    screen.getByTestId(
      'session-settings-action-regenerate_prompt_cache_key'
    )
  );

  await waitFor(() => {
    expect(executeSessionAction).toHaveBeenCalledWith(
      expect.objectContaining({
        sessionId: 'session-1',
        actionId: 'regenerate_prompt_cache_key',
        inputs: { session_id: 'session-1' },
      })
    );
    expect(invalidate).toHaveBeenCalled();
    expect(load).toHaveBeenCalled();
  });
});

test('canceling a directory client input skips action execution', async () => {
  const executeSessionAction = jest.fn();
  mockedUseSessionSettingsController.mockReturnValue({
    controller: {
      patchOverride,
      deleteOverride,
      invalidate,
      load,
    } as any,
    state: {
      elements: [],
      actions: [
        {
          ui_type: 'session_action',
          plugin: 'workspace',
          id: 'select_external_workspace',
          label: 'Choose folder from Files…',
          action_id: 'select_external_workspace',
          action_owner: 'application',
          client_input: {
            kind: 'directory',
            input_name: 'workspace_grant_id',
            persistent: true,
          },
          param_map: {
            session_id: '$session.session_id',
            grant_id: '$client.workspace_grant_id',
          },
          rich_ui: {
            kind: 'button',
            placements: ['session_settings'],
          },
        },
      ],
      overrides: {},
      configSchema: [],
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

  renderWithMobileProviders(
    <SessionSettingsModal
      backend={{ executeSessionAction } as any}
      sessionId="session-1"
      visible
      acquireClientValues={async () => null}
      onRequestClose={jest.fn()}
    />
  );

  fireEvent.press(
    screen.getByTestId('session-settings-action-select_external_workspace')
  );

  await waitFor(() => {
    expect(executeSessionAction).not.toHaveBeenCalled();
  });
});
