import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import { ApplicationPluginsProvider } from '@crystal-lattice/frontend-sdk-react';

jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  default: { OS: 'macos', select: (values: any) => values.macos ?? values.default },
}));
jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-rn-components');
  const ReactModule = require('react');
  const { Text, Pressable, View } = require('react-native');
  return {
    ...actual,
    ActionsMenuBar: ({ extraActions, onAction }: any) => ReactModule.createElement(
      View, null, (extraActions ?? []).map((action: any) => ReactModule.createElement(
        Pressable, { key: action.key, onPress: () => onAction(action.key) },
        ReactModule.createElement(Text, null, action.label),
      )),
    ),
    SessionListActionsBar: ({ pluginActions, onFallbackAction }: any) => ReactModule.createElement(
      View, null, pluginActions.map((action: any) => ReactModule.createElement(
        Pressable, { key: action.id, onPress: () => onFallbackAction(action) },
        ReactModule.createElement(Text, null, action.label),
      )),
    ),
  };
});
jest.mock('../src/windows/desktopWindowManager', () => ({
  DesktopWindowManager: {
    openApplicationActionDialogPopover: jest.fn(),
    closeApplicationActionDialogPopover: jest.fn(),
    openApplicationActionDialogWindow: jest.fn(),
    closeApplicationActionDialogWindow: jest.fn(),
    openReactWindow: jest.fn(),
    closeReactWindow: jest.fn(),
  },
  desktopWindowEvents: null,
}));

import { NEUTRAL_FOLLOWUP_DISPLAY } from '../../../test/fixture/displayFollowupDialog';
import { SessionsPanel } from '../src/panels/SessionsPanel';
import { ChatPane } from '../src/chat/ChatPane';
import { ApplicationActionDialogWindow } from '../src/windows/ApplicationActionDialogWindow';
import { clearActiveApplicationActionDialog } from '../src/windows/applicationActionDialogCoordinator';
import { DesktopWindowManager } from '../src/windows/desktopWindowManager';
import { DesktopGlobalDisplayLayer, DesktopConnectionDisplayRail } from '../src/ui/DesktopGlobalDisplayLayer';

afterEach(() => {
  clearActiveApplicationActionDialog();
  jest.clearAllMocks();
});

test.each(['sessions', 'chat'])('%s host uses the existing native dialog coordinator', async (host) => {
  const session = { session_id: 'session-1', modified: 1, preview: '', metadata: {} };
  const action = {
    plugin: 'fixture', id: 'show', action_id: 'show', label: 'Show neutral result',
    param_map: { session_id: '$session.session_id' }, dialog: { kind: 'none' },
  };
  const execute = jest.fn(async ({ actionId }: any) => ({
    status: 'ok', plugin: 'fixture', action_id: actionId,
    result: { display: actionId === 'show'
      ? { ...NEUTRAL_FOLLOWUP_DISPLAY, presentation: 'inline' }
      : { format: 'text', title: 'Saved', body: 'Updated', presentation: 'inline' } },
  }));
  const backend = {
    kind: 'fixture',
    getCapabilities: () => ({ applicationActions: true, sessionUiSchema: true }),
    listSessions: async () => [session],
    listAgents: async () => ['default'],
    getSessionAgent: async () => 'default',
    listMessages: async () => ({ messages: [], cursorEventId: '0', activeRequestId: null }),
    getSessionSummary: async () => session,
    getSelectedSessionSnapshot: async () => null,
    listSessionSnapshots: async () => [],
    listSessionPlugins: async () => [],
    getSessionUiSchema: async () => [],
    getSessionApplicationUiSchema: async () => [{ ...action, ui_type: 'session_action' }],
    getSessionOverrides: async () => ({}),
    getSessionConfigSchema: async () => [],
    getSessionBaseConfig: async () => ({}),
    listApplicationActions: async () => [
      { plugin: 'fixture', id: 'show', inputs: {} }, { plugin: 'fixture', id: 'save', inputs: {} },
    ],
    listApplicationUiSchema: async () => [{ ...action, ui_type: 'session_list_action' }],
    getLatestEventId: async () => '0',
    listEvents: async () => ({ events: [], latestEventId: '0', cursorExpired: false }),
    executeSessionAction: execute,
  } as unknown as AgentBackend;
  const rendered = render(
    <DesktopGlobalDisplayLayer
      openConnectionsById={{
        'fixture-sessions': { status: 'open', baseUrl: 'http://fixture', backend: backend as any },
        'fixture-chat': { status: 'open', baseUrl: 'http://fixture', backend: backend as any },
      }}
      connectionNameById={{}}
    >
      {host === 'sessions' ? (
        <SessionsPanel focusedConnectionId="fixture-sessions" focusedConnectionName="Fixture"
          connectionId="fixture-sessions" backend={backend} cachedSessions={[session]}
          cachedLastLoadedAt={Date.now()} isOnline onUpdateCache={jest.fn()}
          onOpenSessionTab={jest.fn()} />
      ) : (
        <ApplicationPluginsProvider backend={backend} connectionId="fixture-chat">
          <ChatPane isVisible isActive connectionId="fixture-chat" connectionName="Fixture"
            sessionId="session-1" sessionSummary={session} title="Fixture session"
            backend={backend} cachedEntry={null} onUpdateCache={jest.fn()} />
        </ApplicationPluginsProvider>
      )}
      <DesktopConnectionDisplayRail />
      <ApplicationActionDialogWindow />
    </DesktopGlobalDisplayLayer>,
  );
  if (host === 'sessions') {
    fireEvent(screen.getByTestId('session-row-session-1'), 'hoverIn');
  }
  fireEvent.press(await screen.findByText('Show neutral result'));
  fireEvent.press(await screen.findByText('Enter value'));
  expect(screen.getByText('Edit value')).toBeTruthy();
  expect(host === 'sessions'
    ? DesktopWindowManager?.openApplicationActionDialogWindow
    : DesktopWindowManager?.openApplicationActionDialogPopover
  ).toHaveBeenCalled();
  expect(execute).toHaveBeenCalledTimes(1);
  fireEvent.press(screen.getByTestId('application-action-dialog-cancel'));
  expect(screen.getByText('Neutral result')).toBeTruthy();
  fireEvent.press(screen.getByText('Enter value'));
  fireEvent.changeText(screen.getByTestId('action-form-input-value'), `${host} value`);
  if (host === 'chat') {
    fireEvent(screen.getByTestId('action-form-input-value'), 'submitEditing');
  } else {
    fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  }
  await waitFor(() => expect(screen.getByText('Saved')).toBeTruthy());
  expect(execute).toHaveBeenLastCalledWith(expect.objectContaining({
    sessionId: 'session-1',
    inputs: {
      source: 'neutral-result', value: `${host} value`, cleared: '',
      note: 'kept note', session_id: 'session-1',
    },
  }));
  rendered.unmount();
});