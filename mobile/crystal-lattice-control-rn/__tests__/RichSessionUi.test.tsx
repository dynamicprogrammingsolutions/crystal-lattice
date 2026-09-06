import React from 'react';
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

import { MobileRichSessionUiHarness } from '../src/testing/MobileRichSessionUiHarness';

test('production chat renders and mutates portable rich config and session actions', async () => {
  render(<MobileRichSessionUiHarness />);

  const modelControl = await screen.findByTestId('composer-rich-config-model');
  fireEvent.press(modelControl);
  fireEvent.press(
    await screen.findByTestId('options-picker-declared-claude-b')
  );
  await waitFor(() => {
    expect(screen.getByTestId('rich-session-ui-model').props.children).toBe(
      'claude-b'
    );
  });

  fireEvent.press(screen.getByTestId('composer-rich-config-model'));
  fireEvent.changeText(
    await screen.findByTestId('options-picker-input'),
    'vendor/custom-model'
  );
  fireEvent.press(
    screen.getByText("Use 'vendor/custom-model' as a custom model ID")
  );
  await waitFor(() => {
    expect(screen.getByTestId('rich-session-ui-model').props.children).toBe(
      'vendor/custom-model'
    );
  });

  fireEvent.press(screen.getByTestId('composer-rich-config-model'));
  fireEvent.press(await screen.findByTestId('options-picker-reset'));
  await waitFor(() => {
    expect(screen.getByTestId('rich-session-ui-model').props.children).toBe(
      'claude-a'
    );
  });

  fireEvent.press(
    await screen.findByTestId('session-rich-action-set_status-composer')
  );
  fireEvent.press(
    await screen.findByTestId('session-rich-list-set_status-option-done')
  );
  await waitFor(() => {
    expect(
      screen.getByTestId('rich-session-ui-last-action').props.children
    ).toBe('set_status:done');
  });

  fireEvent.press(screen.getByTestId('composer-rich-config-reasoning_effort'));
  fireEvent.press(await screen.findByTestId('options-picker-declared-high'));

  fireEvent.press(
    screen.getByTestId('composer-rich-config-web_search_enabled')
  );
  await waitFor(() => {
    expect(
      screen.getByTestId('composer-rich-config-web_search_enabled').props
        .accessibilityState.checked
    ).toBe(true);
  });
});

test('mobile composer keeps one draft across inline and maximized editing', async () => {
  render(<MobileRichSessionUiHarness />);

  const inlineInput = await screen.findByTestId('message-composer-input');
  fireEvent.changeText(inlineInput, 'Draft before maximize');
  fireEvent.press(screen.getByTestId('composer-maximize'));

  const expandedInput = await screen.findByTestId('expanded-composer-input');
  expect(expandedInput.props.value).toBe('Draft before maximize');
  fireEvent.changeText(expandedInput, 'Draft after maximize');
  fireEvent.press(screen.getByTestId('expanded-composer-collapse'));

  expect(screen.getByTestId('message-composer-input').props.value).toBe(
    'Draft after maximize'
  );

  const sideButtons = screen.getByTestId('composer-side-buttons');
  expect(
    sideButtons.children.flatMap((child) =>
      typeof child === 'object' && child !== null && 'props' in child
        ? [(child as any).props.testID]
        : []
    )
  ).toEqual(['composer-cancel-request', 'composer-send']);
});
