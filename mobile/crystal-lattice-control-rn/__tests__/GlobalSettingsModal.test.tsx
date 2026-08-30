import React, { useState } from 'react';
import { Text } from 'react-native';
import { fireEvent, render } from '@testing-library/react-native';
import {
  MarkdownDisplayPreferencesProvider,
  useMarkdownDisplayPreferences,
  type MarkdownDisplayPreferences,
} from '@crystal-lattice/frontend-rn-components';

import GlobalSettingsModal from '../src/components/GlobalSettingsModal';

function PreferenceProbe() {
  const { preferences } = useMarkdownDisplayPreferences();
  return <Text testID="preference-probe">{JSON.stringify(preferences)}</Text>;
}

function Host() {
  const [value, setValue] = useState<MarkdownDisplayPreferences>({
    baseFontSize: 15,
    headerSize: 'normal',
  });
  return (
    <MarkdownDisplayPreferencesProvider value={value} onChange={setValue}>
      <GlobalSettingsModal visible onRequestClose={() => {}} />
      <PreferenceProbe />
    </MarkdownDisplayPreferencesProvider>
  );
}

test('updates both markdown display preferences from the settings modal', () => {
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
});