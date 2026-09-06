import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { fireEvent, render } from '@testing-library/react-native';

import {
  ActionsMenuBar,
  type ActionDefinition,
} from '@crystal-lattice/frontend-rn-components';

import { ThemeProvider, lightTheme } from '../src/theme';

const actions: ActionDefinition[] = Array.from({ length: 8 }, (_, index) => ({
  key: `action-${index}`,
  label: `Action ${index}`,
  iconName: 'circle',
  testID: `pinned-action-${index}`,
}));

test('limits compact pins while keeping the overflow menu complete', () => {
  const visibleLimit = actions.length - 3;
  const rendered = render(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Responsive actions"
        baseActions={actions}
        pinned={actions.map((action) => action.key)}
        maxPinnedActionsForBar={visibleLimit}
        onChangePinned={() => {}}
        onAction={() => {}}
        menuButtonTestID="responsive-actions-menu"
        renderIcon={({ name }) => <Text>{name}</Text>}
      />
    </ThemeProvider>
  );

  expect(rendered.getByTestId('actions-menu-overflow-slot')).toBeTruthy();
  for (let index = 0; index < visibleLimit; index += 1) {
    expect(rendered.getByTestId(`pinned-action-${index}`)).toBeTruthy();
  }
  for (let index = visibleLimit; index < actions.length; index += 1) {
    expect(rendered.queryByTestId(`pinned-action-${index}`)).toBeNull();
  }

  fireEvent.press(rendered.getByTestId('responsive-actions-menu'));

  for (const action of actions) {
    expect(
      rendered.getByTestId(`actions-menu-action-${action.key}`)
    ).toBeTruthy();
    expect(rendered.getByTestId(`actions-menu-pin-${action.key}`)).toBeTruthy();
  }
});

test('enables an explicitly positioned second pinned row', () => {
  const rendered = render(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Two row actions"
        baseActions={actions}
        pinned={actions.map((action) => action.key)}
        pinnedRows={2}
        secondPinnedRowPlacement="below"
        onChangePinned={() => {}}
        onAction={() => {}}
        renderIcon={({ name }) => <Text>{name}</Text>}
      />
    </ThemeProvider>
  );

  expect(
    StyleSheet.flatten(
      rendered.getByTestId('actions-menu-pinned-viewport').props.style
    )
  ).toMatchObject({
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
    height: 82,
    maxHeight: 82,
  });
  expect(
    StyleSheet.flatten(
      rendered.getByTestId('actions-menu-overflow-slot').props.style
    )
  ).toMatchObject({ alignSelf: 'flex-start' });

  rendered.rerender(
    <ThemeProvider theme={lightTheme}>
      <ActionsMenuBar
        title="Two row actions"
        baseActions={actions}
        pinned={actions.map((action) => action.key)}
        pinnedRows={2}
        secondPinnedRowPlacement="above"
        onChangePinned={() => {}}
        onAction={() => {}}
        renderIcon={({ name }) => <Text>{name}</Text>}
      />
    </ThemeProvider>
  );

  expect(
    StyleSheet.flatten(
      rendered.getByTestId('actions-menu-pinned-viewport').props.style
    )
  ).toMatchObject({ flexWrap: 'wrap-reverse' });
  expect(
    StyleSheet.flatten(
      rendered.getByTestId('actions-menu-overflow-slot').props.style
    )
  ).toMatchObject({ alignSelf: 'flex-end' });
});
