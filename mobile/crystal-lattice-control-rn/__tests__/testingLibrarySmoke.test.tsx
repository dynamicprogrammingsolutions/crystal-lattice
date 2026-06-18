import React, { useState } from 'react';
import { Text, TouchableOpacity, View } from 'react-native';
import { fireEvent, screen } from '@testing-library/react-native';

import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

function ToggleExample() {
  const [pressed, setPressed] = useState(false);

  return (
    <View>
      <TouchableOpacity onPress={() => setPressed(true)}>
        <Text>Reveal</Text>
      </TouchableOpacity>
      {pressed ? <Text>Visible after press</Text> : null}
    </View>
  );
}

test('React Native Testing Library renders and presses mobile controls', () => {
  renderWithMobileProviders(<ToggleExample />);

  expect(screen.queryByText('Visible after press')).toBeNull();

  fireEvent.press(screen.getByText('Reveal'));

  expect(screen.getByText('Visible after press')).toBeTruthy();
});
