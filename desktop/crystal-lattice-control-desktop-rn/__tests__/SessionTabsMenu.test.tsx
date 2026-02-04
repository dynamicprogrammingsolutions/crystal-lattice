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
        connectionNameById={{}}
        onSelectTab={() => {}}
        onCloseTab={() => {}}
      />,
    );

    fireEvent.press(screen.getByText('⋯'));
    const { ActionSheetIOS } = require('react-native');
    expect(ActionSheetIOS.showActionSheetWithOptions).toHaveBeenCalledTimes(1);
  });
});
