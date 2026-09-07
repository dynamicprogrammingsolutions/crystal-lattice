import React from 'react';
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

import { DesktopRichSessionUiHarness } from '../src/testing/DesktopRichSessionUiHarness';
import { MessageLimitPopoverView } from '../src/windows/MessageLimitPopoverView';
import {
  clearActiveDesktopPopover,
  getActiveDesktopPopover,
} from '../src/windows/desktopPopoverCoordinator';
import { setLastActionsPopoverAnchorTag } from '@crystal-lattice/frontend-rn-components';

class TestErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  state = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <>{String((this.state.error as Error).stack ?? this.state.error)}</>
      );
    }
    return this.props.children;
  }
}

afterEach(() => {
  clearActiveDesktopPopover();
  setLastActionsPopoverAnchorTag(null);
});

test('desktop ChatPane opens the native-popover content for rich settings and actions', async () => {
  render(
    <TestErrorBoundary>
      <DesktopRichSessionUiHarness />
      <MessageLimitPopoverView />
    </TestErrorBoundary>,
  );

  const modelControl = await screen.findByTestId('composer-rich-config-model');
  fireEvent.press(modelControl);
  fireEvent.press(
    await screen.findByTestId('rich-config-dropdown-model-declared-claude-b'),
  );
  await waitFor(() => {
    expect(
      screen.getByTestId('desktop-rich-session-ui-model').props.children,
    ).toBe('claude-b');
  });

  fireEvent.press(screen.getByTestId('composer-rich-config-model'));
  fireEvent.changeText(
    await screen.findByTestId('rich-config-dropdown-model-input'),
    'vendor/custom-model',
  );
  fireEvent.press(
    screen.getByTestId('rich-config-dropdown-model-custom-vendor/custom-model'),
  );
  await waitFor(() => {
    expect(
      screen.getByTestId('desktop-rich-session-ui-model').props.children,
    ).toBe('vendor/custom-model');
  });

  fireEvent.press(
    await screen.findByTestId(
      'session-rich-action-toggle_feature-session-header',
    ),
  );
  await waitFor(() => {
    expect(
      screen.getByTestId('desktop-rich-session-ui-last-action').props.children,
    ).toBe('toggle_feature:true');
  });

  fireEvent.press(
    await screen.findByTestId('session-rich-action-set_status-composer'),
    { nativeEvent: { target: 321 } },
  );
  expect(getActiveDesktopPopover()?.anchorTag).toBe(321);
  fireEvent.press(
    await screen.findByTestId('session-rich-list-set_status-option-done'),
  );
  await waitFor(() => {
    expect(
      screen.getByTestId('desktop-rich-session-ui-last-action').props.children,
    ).toBe('set_status:done');
  });
});

test('a directly pressed rich action overrides a stale popover anchor', async () => {
  setLastActionsPopoverAnchorTag(999);
  render(
    <TestErrorBoundary>
      <DesktopRichSessionUiHarness />
      <MessageLimitPopoverView />
    </TestErrorBoundary>,
  );

  fireEvent.press(
    await screen.findByTestId('session-rich-action-set_status-composer'),
    { nativeEvent: { target: 654 } },
  );

  expect(getActiveDesktopPopover()?.anchorTag).toBe(654);
});
