jest.unmock('@crystal-lattice/frontend-rn-components');

import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { fireEvent, render } from '@testing-library/react-native';

import {
  normalizeSessionListActionElement,
  type SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import {
  MARKDOWN_BASE_FONT_SIZES,
  SessionListActionsBar,
  SessionListRichActionControl,
  SessionListRichActionList,
  applyDisplayTypographyPreset,
} from '@crystal-lattice/frontend-rn-components';

import { ThemeProvider, lightTheme } from '../src/theme';

const session: SessionSummary = {
  session_id: 'rich-session',
  modified: 1,
  preview: 'preview',
  metadata: {
    pinned: true,
    status: 'done',
  },
};

const pinAction = normalizeSessionListActionElement({
  ui_type: 'session_list_action',
  plugin: 'session_pinned',
  id: 'toggle_session_pinned',
  label: 'Pin/unpin session',
  icon: 'star',
  action_id: 'toggle_session_pinned',
  dialog: { kind: 'none' },
  rich_ui: {
    kind: 'toggle',
    value_path: 'metadata.pinned',
    missing_value: false,
    active_value: true,
    default_pinned: true,
    placements: ['header_trailing', 'actions_bar'],
    appearance: {
      active: { tone: 'highlight' },
      inactive: { tone: 'muted' },
    },
  },
}).value!;

const statusAction = normalizeSessionListActionElement({
  ui_type: 'session_list_action',
  plugin: 'session_status',
  id: 'set_session_status',
  label: 'Set status',
  icon: 'circle',
  action_id: 'set_session_status',
  dialog: {
    kind: 'form',
    inputs: [{ name: 'status', type: 'select' }],
  },
  rich_ui: {
    kind: 'list',
    value_path: 'metadata.status',
    missing_value: 'todo',
    input_name: 'status',
    options: [
      { value: 'todo', label: 'To do', tone: 'muted' },
      { value: 'done', label: 'Done', tone: 'success' },
    ],
  },
}).value!;

const archiveAction = normalizeSessionListActionElement({
  ui_type: 'session_list_action',
  plugin: 'session_archive',
  id: 'toggle_session_archived',
  label: 'Archive/restore session',
  icon: 'archive',
  action_id: 'toggle_session_archived',
  dialog: { kind: 'none' },
  rich_ui: {
    kind: 'toggle',
    value_path: 'metadata.archived',
    missing_value: false,
    active_value: true,
    default_pinned: true,
    appearance: {
      active: { tone: 'primary' },
      inactive: { tone: 'muted' },
    },
  },
}).value!;

function wrap(children: React.ReactNode, theme = lightTheme) {
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}

test('renders rich pinned state and routes unpinned list actions through rich presentation', () => {
  const onExecuteAction = jest.fn();
  const onPresentRichList = jest.fn();
  const rendered = render(
    wrap(
      <SessionListActionsBar
        session={session}
        pluginActions={[pinAction, statusAction]}
        baseActions={[]}
        pinned={['toggle_session_pinned']}
        onChangePinned={jest.fn()}
        onBaseAction={jest.fn()}
        onExecuteAction={onExecuteAction}
        onFallbackAction={jest.fn()}
        onPresentRichList={onPresentRichList}
      />,
    ),
  );

  expect(
    rendered.getByTestId('session-rich-action-rich-session-toggle_session_pinned')
      .props.accessibilityState.selected,
  ).toBe(true);
  fireEvent.press(
    rendered.getByTestId('session-rich-action-rich-session-toggle_session_pinned'),
  );
  expect(onExecuteAction).toHaveBeenCalledWith(pinAction);

  fireEvent.press(rendered.getByLabelText('Open Session actions'));
  fireEvent.press(
    rendered.getByTestId('actions-menu-action-set_session_status'),
  );
  expect(onPresentRichList).toHaveBeenCalledWith(statusAction);
});

test('marks the current rich-list option and executes another option without confirmation', () => {
  const onExecuteAction = jest.fn();
  const onRequestClose = jest.fn();
  const rendered = render(
    wrap(
      <SessionListRichActionList
        element={statusAction}
        session={session}
        onExecuteAction={onExecuteAction}
        onRequestClose={onRequestClose}
      />,
    ),
  );

  expect(
    rendered.getByTestId('session-rich-list-set_session_status-option-done').props
      .accessibilityState.selected,
  ).toBe(true);

  fireEvent.press(
    rendered.getByTestId('session-rich-list-set_session_status-option-done'),
  );
  expect(onRequestClose).toHaveBeenCalledTimes(1);
  expect(onExecuteAction).not.toHaveBeenCalled();

  fireEvent.press(
    rendered.getByTestId('session-rich-list-set_session_status-option-todo'),
  );
  expect(onRequestClose).toHaveBeenCalledTimes(2);
  expect(onExecuteAction).toHaveBeenCalledWith({ status: 'todo' });
});

test('renders a highlighted rich toggle in its declared header slot', () => {
  const onExecuteAction = jest.fn();
  const rendered = render(
    wrap(
      <SessionListRichActionControl
        element={pinAction}
        session={session}
        placement="header_trailing"
        onExecuteAction={onExecuteAction}
        onPresentRichList={jest.fn()}
        renderIcon={({ color }) => <Text testID="header-pin-color">{color}</Text>}
      />,
    ),
  );

  expect(
    rendered.getByTestId(
      'session-rich-action-rich-session-toggle_session_pinned-header_trailing',
    ),
  ).toBeTruthy();
  expect(rendered.getByTestId('header-pin-color').props.children).toBe('#FFCC00');
  fireEvent.press(
    rendered.getByTestId(
      'session-rich-action-rich-session-toggle_session_pinned-header_trailing',
    ),
  );
  expect(onExecuteAction).toHaveBeenCalledWith(pinAction);
});

test('uses active semantic metrics for rich labels and textual fallbacks', () => {
  const largestPreset =
    MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1];
  const theme = applyDisplayTypographyPreset(lightTheme, largestPreset);
  const list = render(
    wrap(
      <SessionListRichActionControl
        element={statusAction}
        session={session}
        placement="actions_bar"
        onExecuteAction={jest.fn()}
        onPresentRichList={jest.fn()}
      />,
      theme,
    ),
  );
  expect(StyleSheet.flatten(list.getByText('Done').props.style)).toMatchObject({
    fontSize: theme.typography.fontSize.small,
    lineHeight: theme.typography.lineHeight.small,
  });
  list.unmount();

  const fallback = render(
    wrap(
      <SessionListRichActionControl
        element={pinAction}
        session={session}
        placement="header_trailing"
        onExecuteAction={jest.fn()}
        onPresentRichList={jest.fn()}
      />,
      theme,
    ),
  );
  expect(StyleSheet.flatten(fallback.getByText('●').props.style)).toMatchObject({
    fontSize: theme.typography.fontSize.normal,
    lineHeight: theme.typography.lineHeight.normal,
  });
});

test('keeps a header-only action out of the action bar and renders a dual-placement action once', () => {
  const headerOnlyAction = normalizeSessionListActionElement({
    ui_type: 'session_list_action',
    plugin: 'fixture',
    id: 'header_only',
    label: 'Header only',
    icon: 'star',
    action_id: 'header_only',
    dialog: { kind: 'none' },
    rich_ui: {
      kind: 'toggle',
      value_path: 'metadata.pinned',
      active_value: true,
      placements: ['header_trailing'],
      appearance: {
        active: { tone: 'highlight' },
        inactive: { tone: 'muted' },
      },
    },
  }).value!;
  const rendered = render(
    wrap(
      <SessionListActionsBar
        session={session}
        pluginActions={[headerOnlyAction, pinAction]}
        baseActions={[]}
        pinned={['header_only', 'toggle_session_pinned']}
        onChangePinned={jest.fn()}
        onBaseAction={jest.fn()}
        onExecuteAction={jest.fn()}
        onFallbackAction={jest.fn()}
        onPresentRichList={jest.fn()}
      />,
    ),
  );

  expect(
    rendered.queryByTestId('session-rich-action-rich-session-header_only'),
  ).toBeNull();
  expect(
    rendered.getAllByTestId(
      'session-rich-action-rich-session-toggle_session_pinned',
    ),
  ).toHaveLength(1);
});

test('renders the default-pinned archive action in the shared actions bar', () => {
  const onExecuteAction = jest.fn();
  const rendered = render(
    wrap(
      <SessionListActionsBar
        session={session}
        pluginActions={[archiveAction]}
        baseActions={[]}
        pinned={['toggle_session_archived']}
        onChangePinned={jest.fn()}
        onBaseAction={jest.fn()}
        onExecuteAction={onExecuteAction}
        onFallbackAction={jest.fn()}
        onPresentRichList={jest.fn()}
      />,
    ),
  );

  fireEvent.press(
    rendered.getByTestId(
      'session-rich-action-rich-session-toggle_session_archived',
    ),
  );
  expect(onExecuteAction).toHaveBeenCalledWith(archiveAction);
});