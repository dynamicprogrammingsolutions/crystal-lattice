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

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';

import { ConnectionsPanel } from '../src/panels/ConnectionsPanel';

describe('ConnectionsPanel', () => {
  it('opens header and row menus without crashing', () => {
    const record: ConnectionRecord = {
      id: 'conn-1',
      kind: 'manual',
      name: 'Local',
      host: '127.0.0.1',
      port: 8080,
      lastUsedAt: Date.now(),
    };

    const onOpenNewConnectionEditor = jest.fn();
    const onOpenEditConnectionEditor = jest.fn();

    const screen = render(
      <ConnectionsPanel
        connectionRecords={[record]}
        focusedConnectionId={null}
        openConnectionsById={{}}
        rowClickBehavior="focusOnly"
        onFocusConnection={() => {}}
        onOpenConnection={() => {}}
        onCloseConnection={() => {}}
        onDeleteConnection={() => {}}
        onClearConnections={() => {}}
        onOpenNewConnectionEditor={onOpenNewConnectionEditor}
        onOpenEditConnectionEditor={onOpenEditConnectionEditor}
      />,
    );

    const kebabs = screen.getAllByText('⋯');
    expect(kebabs.length).toBeGreaterThanOrEqual(2);

    const { ActionSheetIOS } = require('react-native');
    const show = ActionSheetIOS.showActionSheetWithOptions as jest.Mock;

    const headerMenuButton = kebabs[0];
    fireEvent.press(headerMenuButton);
    expect(show).toHaveBeenCalledTimes(1);
    const headerCallback = show.mock.calls[0][1] as (index: number) => void;
    headerCallback(0);
    expect(onOpenNewConnectionEditor).toHaveBeenCalledTimes(1);

    const rowMenuButton = kebabs[kebabs.length - 1];
    fireEvent.press(rowMenuButton);
    expect(show).toHaveBeenCalledTimes(2);
    const rowCallback = show.mock.calls[1][1] as (index: number) => void;
    rowCallback(0);
    expect(onOpenEditConnectionEditor).toHaveBeenCalledTimes(1);
  });
});
