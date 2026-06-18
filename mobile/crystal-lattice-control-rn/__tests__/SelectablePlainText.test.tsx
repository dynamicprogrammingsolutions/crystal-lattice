import React from 'react';
import { Platform, Text, TextInput } from 'react-native';
import ReactTestRenderer from 'react-test-renderer';

import SelectablePlainText from '../src/components/SelectablePlainText';

const originalPlatform = Platform.OS;

function setPlatform(os: typeof Platform.OS) {
  Object.defineProperty(Platform, 'OS', {
    configurable: true,
    value: os,
  });
}

afterEach(() => {
  setPlatform(originalPlatform);
});

test('renders readonly TextInput on iOS', () => {
  setPlatform('ios');

  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <SelectablePlainText
        text="Selectable iOS"
        style={{ fontSize: 15 }}
        numberOfLines={2}
      />,
    );
  });

  const input = renderer!.root.findByType(TextInput);

  expect(input.props.value).toBe('Selectable iOS');
  expect(input.props.editable).toBe(false);
  expect(input.props.multiline).toBe(true);
  expect(input.props.scrollEnabled).toBe(false);
  expect(input.props.numberOfLines).toBe(2);
});

test('renders selectable Text on Android', () => {
  setPlatform('android');

  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <SelectablePlainText
        style={{ fontSize: 15 }}
        numberOfLines={1}
      >
        Selectable Android
      </SelectablePlainText>,
    );
  });

  const text = renderer!.root.findByType(Text);

  expect(text.props.children).toBe('Selectable Android');
  expect(text.props.selectable).toBe(true);
  expect(text.props.numberOfLines).toBe(1);
});