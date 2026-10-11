import React from 'react';
import { fireEvent, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';
import { ApplicationActionDialog } from '@crystal-lattice/frontend-rn-components';

jest.mock('@crystal-lattice/frontend-rn-components', () => ({
  ...jest.requireActual('@crystal-lattice/frontend-rn-components'),
}));

import { MANY_FIELD_DIALOG, buildLayoutDisplay } from '../../../test/fixture/actionFormLayouts';
import ActionResultModal from '../src/components/ActionResultModal';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

function resize(id: string, height: number) {
  fireEvent(screen.getByTestId(id), 'layout', {
    nativeEvent: { layout: { x: 0, y: 0, width: 380, height } },
  });
}

test('a many-field dialog retains edited values through viewport changes and submits typed defaults', () => {
  const onSubmit = jest.fn();
  renderWithMobileProviders(
    <ApplicationActionDialog
      visible
      dialog={MANY_FIELD_DIALOG}
      onSubmit={onSubmit}
      onCancel={jest.fn()}
    />,
  );
  resize('application-action-dialog-viewport', 700);
  fireEvent.changeText(screen.getByTestId('action-form-input-value_0'), 'changed first');
  fireEvent.changeText(screen.getByTestId('action-form-input-last'), 'changed last');
  resize('application-action-dialog-viewport', 320);
  expect(screen.getByTestId('action-form-input-value_0').props.value).toBe('changed first');
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  expect(onSubmit).toHaveBeenCalledWith(
    expect.objectContaining({
      value_0: 'changed first',
      value_17: 'initial 17',
      count: 7,
      last: 'changed last',
    }),
  );
  expect(Object.keys(onSubmit.mock.calls[0][0])).toHaveLength(20);
});

test('dialog submission still validates required fields and clears supplied defaults', () => {
  const onSubmit = jest.fn();
  renderWithMobileProviders(
    <ApplicationActionDialog
      visible
      dialog={{
        kind: 'form',
        title: 'Edit values',
        inputs: [
          { name: 'value', label: 'Value', type: 'string', required: true },
          { name: 'note', type: 'string', default: 'previous note' },
        ],
      }}
      onSubmit={onSubmit}
      onCancel={jest.fn()}
    />,
  );
  resize('application-action-dialog-viewport', 300);
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  expect(screen.getByText('Field "Value" is required.')).toBeTruthy();
  expect(onSubmit).not.toHaveBeenCalled();
  fireEvent.changeText(screen.getByTestId('action-form-input-value'), 'new value');
  fireEvent.changeText(screen.getByTestId('action-form-input-note'), '');
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  expect(onSubmit).toHaveBeenCalledWith({ value: 'new value', note: '' });
});

test('result viewport changes preserve embedded values and keep form submission outside markdown', () => {
  const onFollowupAction = jest.fn();
  renderWithMobileProviders(
    <ActionResultModal
      visible
      display={buildLayoutDisplay(2)}
      testID="fixture-result"
      onFollowupAction={onFollowupAction}
      onRequestClose={jest.fn()}
    />,
  );
  resize('action-result-viewport', 650);
  resize('action-result-header', 50);
  resize('action-result-controls', 70);
  fireEvent.changeText(screen.getByTestId('action-form-input-to'), 'changed bound');
  resize('action-result-viewport', 320);
  const bodyStyle = StyleSheet.flatten(screen.getByTestId('fixture-result-body').props.style);
  const formStyle = StyleSheet.flatten(screen.getByTestId('fixture-result-body-form').props.style);
  expect(formStyle.maxHeight).toBeLessThan(bodyStyle.maxHeight);
  expect(screen.getByTestId('fixture-result-body-form').props.keyboardShouldPersistTaps).toBe(
    'handled',
  );
  expect(screen.getByTestId('action-form-input-to').props.value).toBe('changed bound');
  fireEvent.press(screen.getByTestId('action-display-action-apply'));
  expect(onFollowupAction).toHaveBeenCalledWith(expect.objectContaining({ id: 'apply' }), {
    from: 'first bound',
    to: 'changed bound',
  });
});

test('an overlay follow-up owns keyboard avoidance and hardware Back cancels it first', () => {
  const onClose = jest.fn();
  const onCancel = jest.fn();
  const rendered = renderWithMobileProviders(
    <ActionResultModal
      visible
      display={buildLayoutDisplay()}
      testID="fixture-result"
      onRequestClose={onClose}
      onOverlayRequestClose={onCancel}
      overlayChildren={
        <ApplicationActionDialog
          visible
          presentationMode="overlay"
          dialog={MANY_FIELD_DIALOG}
          onSubmit={jest.fn()}
          onCancel={onCancel}
        />
      }
    />,
  );
  expect(
    screen.UNSAFE_getAllByType(require('react-native').KeyboardAvoidingView)[0].props.enabled,
  ).toBe(false);
  expect(screen.queryByTestId('action-result-close')).toBeNull();
  const nativeModal = rendered.UNSAFE_getByType(require('react-native').Modal);
  fireEvent(nativeModal, 'requestClose');
  expect(onCancel).toHaveBeenCalledTimes(1);
  expect(onClose).not.toHaveBeenCalled();
});
