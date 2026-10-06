import React from 'react';
import { render } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';

jest.mock('@crystal-lattice/react-native-mac-text-view', () => {
  const ReactModule = require('react');
  const { View: MockView } = require('react-native');

  return {
    MacTextView: ReactModule.forwardRef((props: any, ref: any) => {
      ReactModule.useImperativeHandle(ref, () => ({
        focus: jest.fn(),
        setText: jest.fn(),
      }));
      return <MockView ref={ref} {...props} />;
    }),
  };
});

import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { useDesktopApplicationActionFieldRenderers } from '../src/ui/useDesktopApplicationActionFieldRenderers';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

function MultilineActionHarness({
  onChange,
}: {
  onChange: jest.Mock;
}): React.JSX.Element {
  const fieldRenderers = useDesktopApplicationActionFieldRenderers();
  const renderer = fieldRenderers.multiline;

  if (!renderer) {
    throw new Error('Desktop multiline renderer is unavailable.');
  }

  return renderer({
    field: { name: 'prompt', type: 'multiline' },
    name: 'prompt',
    label: 'Prompt',
    description: '',
    placeholder: '',
    fieldType: 'multiline',
    value: 'Initial prompt',
    options: [],
    isFirstField: false,
    onChange,
    onSubmit: jest.fn(),
    renderFallback: () => null,
  }) as React.JSX.Element;
}

test('desktop action multiline fields use a fixed-height MacTextView with normal newlines', () => {
  const onChange = jest.fn();
  const screen = render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <MultilineActionHarness onChange={onChange} />
    </ThemeProvider>,
  );

  const input = screen.getByTestId('action-form-input-prompt');
  expect(input.props.initialText).toBe('Initial prompt');
  expect(input.props.submitOnEnter).toBe(false);
  expect(input.props.autoGrow).toBeUndefined();
  expect(StyleSheet.flatten(input.props.style).height).toBe(112);

  input.props.onChangeText('alpha beta\ngamma');
  expect(onChange).toHaveBeenCalledWith('alpha beta\ngamma');
});