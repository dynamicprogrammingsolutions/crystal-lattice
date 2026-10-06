import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import { AppState, Alert } from 'react-native';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-rn-components');
  const ReactModule = require('react');
  const { Text, TouchableOpacity, View } = require('react-native');
  return {
    ...actual,
    SessionActionsBar: ({ extraActions, onAction }: any) => ReactModule.createElement(
      View, null, (extraActions ?? []).map((action: any) => ReactModule.createElement(
        TouchableOpacity, { key: action.key, onPress: () => onAction(action.key) },
        ReactModule.createElement(Text, null, action.label),
      )),
    ),
    SessionListActionsBar: ({ pluginActions, onFallbackAction }: any) => ReactModule.createElement(
      View, null, pluginActions.map((action: any) => ReactModule.createElement(
        TouchableOpacity, { key: action.id, onPress: () => onFallbackAction(action) },
        ReactModule.createElement(Text, null, action.label),
      )),
    ),
  };
});

import { NEUTRAL_FOLLOWUP_DISPLAY } from '../../../test/fixture/displayFollowupDialog';
import { ApplicationPluginsProvider } from '../src/ApplicationPluginsContext';
import { PinnedActionsProvider } from '../src/PinnedActionsContext';
import SessionsScreen from '../src/SessionsScreen';
import SessionChatScreen from '../src/SessionChatScreen';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

const session = { session_id: 'session-1', modified: 1, preview: '', metadata: {} };

test.each([
  ['sessions', true], ['sessions', false], ['chat', true], ['chat', false],
])('%s host opens, cancels, and submits with preserve_display=%s', async (host, preserve) => {
  AppState.currentState = 'active';
  const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  const action = {
    plugin: 'fixture', id: 'show', action_id: 'show', label: 'Show neutral result',
    param_map: { session_id: '$session.session_id' }, dialog: { kind: 'none' },
  };
  const execute = jest.fn(async ({ actionId }: any) => ({
    status: 'ok', plugin: 'fixture', action_id: actionId,
    result: { display: actionId === 'show'
      ? { ...NEUTRAL_FOLLOWUP_DISPLAY, actions: NEUTRAL_FOLLOWUP_DISPLAY.actions!.map(
          action => ({ ...action, preserve_display: preserve }),
        ) }
      : { format: 'text', title: 'Saved', body: 'Updated', presentation: 'modal' } },
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
      { plugin: 'fixture', id: 'show', inputs: {} },
      { plugin: 'fixture', id: 'save', inputs: {} },
    ],
    listApplicationUiSchema: async () => [{ ...action, ui_type: 'session_list_action' }],
    getLatestEventId: async () => '0',
    listEvents: async () => ({ events: [], latestEventId: '0', cursorExpired: false }),
    executeSessionAction: execute,
  } as unknown as AgentBackend;
  const rendered = renderWithMobileProviders(
    <PinnedActionsProvider>
      <ApplicationPluginsProvider backend={backend} connectionId={`fixture-${host}`}>
        {host === 'sessions' ? (
          <SessionsScreen backend={backend} connectionId="fixture" isActive
            cachedSessions={[session]} lastLoadedAt={Date.now()}
            onUpdateCache={jest.fn()} onSelectSession={jest.fn()} />
        ) : (
          <SessionChatScreen backend={backend} connectionId="fixture" isActive
            sessionId={session.session_id} sessionSummary={session} cachedMessages={[]}
            lastLoadedAt={null} cachedEventsCursorId={null} cachedActiveRequestId={null}
            onUpdateCache={jest.fn()} onBack={jest.fn()} initialComposeText=""
            initialScrollAnchor={null} onSaveComposeText={jest.fn()}
            initialRangeStartText="-50" initialRangeEndText="" onSaveHistoryRange={jest.fn()}
            onSaveScrollAnchor={jest.fn()} debugTimeline={[]} onAppendDebugTimelineEntry={jest.fn()} />
        )}
      </ApplicationPluginsProvider>
    </PinnedActionsProvider>,
  );
  fireEvent.press(await screen.findByText('Show neutral result'));
  fireEvent.press(await screen.findByText('Enter value'));
  expect(screen.getByText('Edit value')).toBeTruthy();
  expect(execute).toHaveBeenCalledTimes(1);
  fireEvent.press(screen.getByTestId('application-action-dialog-cancel'));
  expect(screen.getByText('Neutral result')).toBeTruthy();
  expect(execute).toHaveBeenCalledTimes(1);
  fireEvent.press(screen.getByText('Enter value'));
  fireEvent.changeText(screen.getByTestId('action-form-input-value'), `${host} value`);
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  await waitFor(() => expect(screen.getByText('Saved')).toBeTruthy());
  expect(execute).toHaveBeenLastCalledWith(expect.objectContaining({
    sessionId: 'session-1',
    inputs: {
      source: 'neutral-result', value: `${host} value`, cleared: '',
      note: 'kept note', session_id: 'session-1',
    },
  }));
  expect(alert).not.toHaveBeenCalled();
  rendered.unmount();
  alert.mockRestore();
});