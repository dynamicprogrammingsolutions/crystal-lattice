import React from 'react';
import { fireEvent, screen } from '@testing-library/react-native';

import type { ActionDisplayPayload } from '@crystal-lattice/frontend-sdk';

import ActionDisplayCard from '../src/components/ActionDisplayCard';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

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

test('action display card submits embedded form values with follow-up action', () => {
  const onFollowupAction = jest.fn();

  renderWithMobileProviders(
    <ActionDisplayCard display={DISPLAY_WITH_FORM} onFollowupAction={onFollowupAction} />,
  );

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

test('action display card validates required embedded form fields', () => {
  const onFollowupAction = jest.fn();

  renderWithMobileProviders(
    <ActionDisplayCard display={DISPLAY_WITH_FORM} onFollowupAction={onFollowupAction} />,
  );

  fireEvent.press(screen.getByText('Submit'));

  expect(onFollowupAction).not.toHaveBeenCalled();
  expect(screen.getByText('Field "Callback URL" is required.')).toBeTruthy();
});

test('action display card dismiss action closes without backend follow-up', () => {
  const onFollowupAction = jest.fn();
  const onDismiss = jest.fn();

  renderWithMobileProviders(
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