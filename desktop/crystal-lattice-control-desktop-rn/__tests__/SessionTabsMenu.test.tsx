import React from 'react';
import { StyleSheet } from 'react-native';

jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  default: {
    OS: 'macos',
    select: (spec: any) => ('macos' in spec ? spec.macos : spec.default),
  },
}));

jest.mock('react-native/Libraries/ActionSheetIOS/ActionSheetIOS', () => ({
  default: {
    showActionSheetWithOptions: jest.fn(),
  },
}));

import { fireEvent, render } from '@testing-library/react-native';

import { SessionTabs } from '../src/tabs/SessionTabs';

describe('SessionTabs', () => {
  it('opens tab menu via ActionSheet on macOS', () => {
    const screen = render(
      <SessionTabs
        tabs={[]}
        activeTabId={null}
        styleVariant="toolbarTabs"
        connectionNameById={{}}
        onSelectTab={() => {}}
        onCloseTab={() => {}}
      />,
    );

    fireEvent.press(screen.getByText('⋯'));
    const { ActionSheetIOS } = require('react-native');
    expect(ActionSheetIOS.showActionSheetWithOptions).toHaveBeenCalledTimes(1);
  });

  it('renders the tab subtitle instead of the connection id', () => {
    const screen = render(
      <SessionTabs
        tabs={[
          {
            tabId: 'conn-123:session-abc',
            connectionId: 'conn-123',
            sessionId: 'session-abc',
            title: 'Test Session',
            subtitle: 'Actual subtitle',
          },
        ]}
        activeTabId="conn-123:session-abc"
        styleVariant="toolbarTabs"
        connectionNameById={{}}
        onSelectTab={() => {}}
        onCloseTab={() => {}}
      />,
    );

    expect(screen.getByText('Actual subtitle')).toBeTruthy();
    expect(screen.queryByText('conn-123')).toBeNull();
  });

  it('renders fixed Home, one italic preview, status, promotion, and accessible reorder', () => {
    const onPromotePreview = jest.fn();
    const onReorderPermanent = jest.fn();
    const now = jest
      .spyOn(Date, 'now')
      .mockReturnValueOnce(100)
      .mockReturnValueOnce(200);
    const screen = render(
      <SessionTabs
        permanentTabs={[
          {
            tabId: 'connection:one',
            connectionId: 'connection',
            sessionId: 'one',
            title: 'One',
          },
          {
            tabId: 'connection:two',
            connectionId: 'connection',
            sessionId: 'two',
            title: 'Two',
          },
        ]}
        previewTab={{
          tabId: 'connection:preview',
          connectionId: 'connection',
          sessionId: 'preview',
          title: 'Preview session',
        }}
        homeActive={false}
        activeTabId="connection:preview"
        styleVariant="toolbarTabs"
        connectionNameById={{ connection: 'Local' }}
        requestStatuses={{
          connection: {
            preview: {
              session_id: 'preview',
              request_id: null,
              state: 'running',
              basis: 'active_request',
              session_modified: 1,
            },
          },
        }}
        onSelectHome={() => {}}
        onSelectTab={() => {}}
        onCloseTab={() => {}}
        onPromotePreview={onPromotePreview}
        onReorderPermanent={onReorderPermanent}
      />,
    );

    expect(screen.getByTestId('desktop-home-tab')).toBeTruthy();
    const previewText = screen.getByText('Preview session');
    expect(StyleSheet.flatten(previewText.props.style).fontStyle).toBe(
      'italic',
    );
    expect(screen.getByLabelText('Request status: In progress')).toBeTruthy();

    const preview = screen.getByTestId(
      'desktop-session-tab-connection:preview',
    );
    fireEvent.press(preview);
    fireEvent.press(preview);
    expect(onPromotePreview).toHaveBeenCalledWith('connection:preview');

    fireEvent(
      screen.getByTestId('desktop-session-tab-connection:one'),
      'accessibilityAction',
      { nativeEvent: { actionName: 'increment' } },
    );
    expect(onReorderPermanent).toHaveBeenCalledWith(0, 1);
    now.mockRestore();
  });

  it('closes permanent and preview tabs on middle click without selecting or reordering', () => {
    const onSelectTab = jest.fn();
    const onCloseTab = jest.fn();
    const onReorderPermanent = jest.fn();
    const screen = render(
      <SessionTabs
        permanentTabs={[
          {
            tabId: 'connection:one',
            connectionId: 'connection',
            sessionId: 'one',
            title: 'One',
          },
        ]}
        previewTab={{
          tabId: 'connection:preview',
          connectionId: 'connection',
          sessionId: 'preview',
          title: 'Preview',
        }}
        activeTabId="connection:preview"
        styleVariant="toolbarTabs"
        connectionNameById={{ connection: 'Local' }}
        onSelectTab={onSelectTab}
        onCloseTab={onCloseTab}
        onReorderPermanent={onReorderPermanent}
      />,
    );
    const nativeEvent = {
      button: 2,
      translationX: 0,
      translationY: 0,
      locationX: 0,
      locationY: 0,
      pageX: 0,
      pageY: 0,
    };

    fireEvent(
      screen.getByTestId('desktop-session-tab-pointer-connection:one'),
      'auxiliaryClick',
      { nativeEvent },
    );
    fireEvent(
      screen.getByTestId('desktop-session-tab-pointer-connection:preview'),
      'auxiliaryClick',
      { nativeEvent },
    );

    expect(onCloseTab.mock.calls).toEqual([
      ['connection:one'],
      ['connection:preview'],
    ]);
    expect(onSelectTab).not.toHaveBeenCalled();
    expect(onReorderPermanent).not.toHaveBeenCalled();
  });
});
