import React from 'react';

jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  default: {
    OS: 'macos',
    select: (spec: any) => ('macos' in spec ? spec.macos : spec.default),
  },
}));

import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';

import type { ActionDisplayPayload } from '@crystal-lattice/frontend-sdk';

import { ActionDisplayCard } from '../src/ui/ActionDisplayCard';

const DISPLAY_WITH_FORM: ActionDisplayPayload = {
  format: 'text',
  title: 'Finish login',
  body: 'Paste the callback URL from Safari.',
  form: {
    kind: 'form',
    inputs: [
      {
        name: 'callback_url',
        type: 'multiline',
        label: 'Callback URL',
        placeholder: 'http://127.0.0.1:41793/callback?code=...',
        required: true,
      },
    ],
  },
  actions: [
    {
      kind: 'run_action',
      id: 'submit-callback',
      label: 'Submit',
      plugin: 'dummy_display_form_app',
      action_id: 'submit_callback',
      param_map: {
        callback_url: '$form.callback_url',
      },
    },
    {
      kind: 'dismiss',
      id: 'cancel',
      label: 'Cancel',
    },
  ],
};

describe('ActionDisplayCard', () => {
  it('bounds a lengthy text body in a scroll view', () => {
    const body = Array.from(
      { length: 300 },
      (_, index) => `Instruction line ${index}`,
    ).join('\n');

    render(
      <ActionDisplayCard
        display={{
          format: 'text',
          title: 'Compiled system message',
          body,
        }}
        bounded
        bodyTestID="long-action-display-body"
      />,
    );

    expect(screen.getByText(body)).toBeTruthy();
    const bodyScroll = screen.getByTestId('long-action-display-body');
    expect(bodyScroll).toBeTruthy();
    expect(StyleSheet.flatten(bodyScroll.props.style).maxHeight).toBe(420);
  });

  it('submits embedded form values with follow-up action', () => {
    const onFollowupAction = jest.fn();

    render(<ActionDisplayCard display={DISPLAY_WITH_FORM} onFollowupAction={onFollowupAction} />);

    fireEvent.changeText(
      screen.getByPlaceholderText('http://127.0.0.1:41793/callback?code=...'),
      'http://127.0.0.1:41793/callback?code=abc&state=xyz',
    );
    fireEvent.press(screen.getByText('Submit'));

    expect(onFollowupAction).toHaveBeenCalledWith(
      expect.objectContaining({
        kind: 'run_action',
        id: 'submit-callback',
      }),
      {
        callback_url: 'http://127.0.0.1:41793/callback?code=abc&state=xyz',
      },
    );
  });

  it('dismisses locally without invoking a follow-up action', () => {
    const onFollowupAction = jest.fn();
    const onDismiss = jest.fn();

    render(
      <ActionDisplayCard
        display={DISPLAY_WITH_FORM}
        onDismiss={onDismiss}
        onFollowupAction={onFollowupAction}
      />,
    );

    fireEvent.press(screen.getByText('Cancel'));

    expect(onDismiss).toHaveBeenCalledTimes(1);
    expect(onFollowupAction).not.toHaveBeenCalled();
  });
});