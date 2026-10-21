import React, { useState } from 'react';
import { Text } from 'react-native';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import {
  MarkdownDisplayPreferencesProvider,
  useMarkdownDisplayPreferences,
  type MarkdownDisplayPreferences,
} from '@crystal-lattice/frontend-rn-components';

import GlobalSettingsModal from '../src/components/GlobalSettingsModal';
import {
  configureEmbeddedPythonRuntime,
  getEmbeddedPythonRuntimeConfiguration,
  isEmbeddedPythonRuntimeAvailable,
  type EmbeddedRuntimePublicConfiguration,
} from '../src/embeddedRuntime/embeddedPythonRuntime';

jest.mock('../src/embeddedRuntime/embeddedPythonRuntime', () => ({
  configureEmbeddedPythonRuntime: jest.fn(),
  getEmbeddedPythonRuntimeConfiguration: jest.fn(),
  isEmbeddedPythonRuntimeAvailable: jest.fn(() => false),
}));

beforeEach(() => {
  jest.clearAllMocks();
  jest.mocked(isEmbeddedPythonRuntimeAvailable).mockReturnValue(false);
});

function PreferenceProbe() {
  const { preferences } = useMarkdownDisplayPreferences();
  return <Text testID="preference-probe">{JSON.stringify(preferences)}</Text>;
}

function Host() {
  const [value, setValue] = useState<MarkdownDisplayPreferences>({
    baseFontSize: 15,
    headerSize: 'normal',
    markdownRenderer: 'react-native-markdown-display',
    codeBlockRenderer: 'selectable-native',
  });
  return (
    <MarkdownDisplayPreferencesProvider value={value} onChange={setValue}>
      <GlobalSettingsModal visible onRequestClose={() => {}} />
      <PreferenceProbe />
    </MarkdownDisplayPreferencesProvider>
  );
}

test('updates markdown typography and renderer preferences from the settings modal', () => {
  const screen = render(<Host />);
  fireEvent.press(screen.getByTestId('global-settings-base-font-size'));
  fireEvent.press(screen.getByText('16'));
  expect(screen.getByTestId('preference-probe').props.children).toContain(
    '"baseFontSize":16',
  );

  fireEvent.press(screen.getByTestId('global-settings-markdown-headers'));
  fireEvent.press(screen.getByText('Small'));
  expect(screen.getByTestId('preference-probe').props.children).toContain(
    '"headerSize":"small"',
  );

  fireEvent.press(screen.getByTestId('global-settings-markdown-renderer'));
  fireEvent.press(screen.getByText('Enriched Markdown (experimental)'));
  expect(screen.getByTestId('preference-probe').props.children).toContain(
    '"markdownRenderer":"react-native-enriched-markdown"',
  );

  fireEvent.press(screen.getByTestId('global-settings-code-renderer'));
  fireEvent.press(screen.getByText('Syntax highlighter'));
  expect(screen.getByTestId('preference-probe').props.children).toContain(
    '"codeBlockRenderer":"syntax-highlighter"',
  );
});

test('loads reviewer exposure and saves only the global flag', async () => {
  const configuration: EmbeddedRuntimePublicConfiguration = {
    version: 3,
    defaultAgent: 'local',
    reviewerVisible: false,
    profileOrder: [],
    providers: {} as EmbeddedRuntimePublicConfiguration['providers'],
    proxyUrl: '',
    model: '',
    hasApiKey: false,
  };
  jest.mocked(isEmbeddedPythonRuntimeAvailable).mockReturnValue(true);
  jest.mocked(getEmbeddedPythonRuntimeConfiguration).mockResolvedValue(configuration);
  const saved = { ...configuration, reviewerVisible: true };
  jest.mocked(configureEmbeddedPythonRuntime).mockResolvedValue(saved);
  const onSaved = jest.fn();
  const screen = render(
    <GlobalSettingsModal
      visible
      onRequestClose={() => {}}
      onEmbeddedSettingsChanged={onSaved}
    />
  );
  await waitFor(() => expect(
    screen.getByTestId('global-settings-reviewer-visible').props.accessibilityState
  ).toEqual({ disabled: false, checked: false }));

  fireEvent(
    screen.getByTestId('global-settings-reviewer-visible-control'), 'valueChange', true,
  );
  await waitFor(() => expect(onSaved).toHaveBeenCalledWith(saved));
  expect(configureEmbeddedPythonRuntime).toHaveBeenCalledWith({
    version: 3,
    reviewerVisible: true,
  });
  expect(screen.getByTestId('global-settings-reviewer-visible').props.accessibilityState.checked)
    .toBe(true);
  expect(screen.getByText(
    'Enter the supplied reviewer API key in Local provider settings.',
  )).toBeTruthy();
});