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

import { act, fireEvent, render } from '@testing-library/react-native';

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import {
  MARKDOWN_BASE_FONT_SIZES,
  applyDisplayTypographyPreset,
} from '../../../packages/frontend-rn-components/src/markdownDisplayPreferences';

import {
  ConnectionsPanel,
  getConnectionsListMaxHeight,
} from '../src/panels/ConnectionsPanel';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

const largestPreset =
  MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1];
const theme = applyDisplayTypographyPreset(
  buildDesktopTheme(null),
  largestPreset,
);

function connection(index: number): ConnectionRecord {
  return {
    id: `conn-${index}`,
    kind: 'manual',
    name: `Connection ${index}`,
    host: '127.0.0.1',
    port: 8000 + index,
    lastUsedAt: index,
  };
}

function renderPanel(records: ConnectionRecord[]) {
  return render(
    <ThemeProvider theme={theme}>
      <ConnectionsPanel
        connectionRecords={records}
        focusedConnectionId={null}
        openConnectionsById={{}}
        rowClickBehavior="focusOnly"
        onFocusConnection={() => {}}
        onOpenConnection={() => {}}
        onCloseConnection={() => {}}
        onDeleteConnection={() => {}}
        onClearConnections={() => {}}
        onOpenNewConnectionEditor={() => {}}
        onOpenEditConnectionEditor={() => {}}
      />
    </ThemeProvider>,
  );
}

describe('ConnectionsPanel', () => {
  it('opens header and row menus without crashing', () => {
    const record = connection(1);

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

  it('uses natural non-scroll containers for up to three connections', () => {
    const one = renderPanel([connection(1)]);
    expect(one.getByTestId('connections-list-static')).toBeTruthy();
    expect(one.queryByTestId('connections-list-scroll')).toBeNull();
    one.unmount();

    const three = renderPanel([connection(1), connection(2), connection(3)]);
    expect(three.getByTestId('connections-list-static')).toBeTruthy();
    expect(three.queryByTestId('connections-list-scroll')).toBeNull();
  });

  it('bounds larger lists and removes the overflow fade at the real bottom', () => {
    const rendered = renderPanel([
      connection(1),
      connection(2),
      connection(3),
      connection(4),
      connection(5),
    ]);
    const scroll = rendered.getByTestId('connections-list-scroll');
    expect(scroll).toBeTruthy();
    expect(StyleSheet.flatten(scroll.props.style)).toMatchObject({
      maxHeight: getConnectionsListMaxHeight(theme),
    });

    const viewportHeight = getConnectionsListMaxHeight(theme);
    const contentHeight = viewportHeight + theme.typography.lineHeight.normal;
    act(() => {
      scroll.props.onLayout({
        nativeEvent: { layout: { height: viewportHeight } },
      });
      scroll.props.onContentSizeChange(0, contentHeight);
    });
    expect(
      rendered.getByTestId('connections-list-bottom-fade').props
        .accessibilityLabel,
    ).toBe('More connections below');
    expect(scroll.props.accessibilityValue.text).toBe(
      'More connections below',
    );

    act(() => {
      scroll.props.onScroll({
        nativeEvent: {
          contentOffset: { y: contentHeight - viewportHeight },
          layoutMeasurement: { height: viewportHeight },
          contentSize: { height: contentHeight },
        },
      });
    });
    expect(rendered.queryByTestId('connections-list-bottom-fade')).toBeNull();
    expect(
      rendered.getByTestId('connections-list-scroll').props.accessibilityValue
        .text,
    ).toBe('Bottom reached');
  });

  it('collapses to the header and expands the connection list again', () => {
    const rendered = renderPanel([connection(1)]);
    const toggle = rendered.getByTestId('connections-collapse-toggle');
    expect(toggle.props.accessibilityState.expanded).toBe(true);

    fireEvent.press(toggle);
    expect(rendered.queryByTestId('connections-list-static')).toBeNull();
    expect(
      rendered.getByTestId('connections-collapse-toggle').props
        .accessibilityState.expanded,
    ).toBe(false);

    fireEvent.press(rendered.getByTestId('connections-collapse-toggle'));
    expect(rendered.getByTestId('connections-list-static')).toBeTruthy();
  });
});
