import React from 'react';

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
});
