import React from 'react';

jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  default: {
    OS: 'macos',
    select: (spec: any) => ('macos' in spec ? spec.macos : spec.default),
  },
}));

import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';

import { ActionDisplayWindow } from '../src/windows/ActionDisplayWindow';
import {
  clearActiveActionDisplayWindow,
  setActiveActionDisplayWindow,
} from '../src/windows/actionDisplayWindowCoordinator';

afterEach(() => {
  clearActiveActionDisplayWindow();
});

test('renders a lengthy action display in a bounded scroll area and dismisses it', () => {
  const onDismiss = jest.fn();
  const body = Array.from(
    { length: 300 },
    (_, index) => `Instruction line ${index}`,
  ).join('\n');
  setActiveActionDisplayWindow({
    state: {
      id: 'long-display',
      display: {
        format: 'text',
        title: 'Compiled system message',
        body,
        presentation: 'modal',
      },
      contextLabel: 'Local agent',
    },
    handlers: {
      onDismiss,
      onFollowupAction: jest.fn(),
    },
  });

  render(<ActionDisplayWindow />);

  expect(screen.getByText('Compiled system message')).toBeTruthy();
  expect(screen.getByText(body)).toBeTruthy();
  const bodyScroll = screen.getByTestId('desktop-action-display-body');
  expect(bodyScroll).toBeTruthy();
  expect(StyleSheet.flatten(bodyScroll.props.style).maxHeight).toBe(420);
  fireEvent.scroll(bodyScroll, {
    nativeEvent: {
      contentOffset: { x: 0, y: 500 },
      contentSize: { width: 700, height: 6000 },
      layoutMeasurement: { width: 700, height: 420 },
    },
  });
  fireEvent.press(screen.getByText('Close'));
  expect(onDismiss).toHaveBeenCalledTimes(1);
});
