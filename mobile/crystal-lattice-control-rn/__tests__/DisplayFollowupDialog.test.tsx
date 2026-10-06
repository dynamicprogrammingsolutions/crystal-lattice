import React from 'react';
import { act, fireEvent, screen, waitFor } from '@testing-library/react-native';
import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
} from '@crystal-lattice/frontend-sdk';

jest.mock('@crystal-lattice/frontend-rn-components', () => ({
  ...jest.requireActual('@crystal-lattice/frontend-rn-components'),
}));

import { NEUTRAL_FOLLOWUP_DISPLAY } from '../../../test/fixture/displayFollowupDialog';
import { ApplicationPluginsProvider } from '../src/ApplicationPluginsContext';
import GlobalDisplayLayer, { MobileDisplayHost } from '../src/components/GlobalDisplayLayer';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import { Alert } from 'react-native';

function backendFixture(execute: jest.Mock): AgentBackend {
  return {
    kind: 'fixture',
    getCapabilities: () => ({ applicationActions: true }),
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => [],
    getLatestEventId: async () => '0',
    listEvents: async () => ({ events: [], latestEventId: '0' }),
    executeSessionAction: execute,
  } as unknown as AgentBackend;
}

test('global modal follow-up opens the production dialog, cancels, and maps both value sources', async () => {
  const execute = jest.fn(async () => ({
    status: 'ok', plugin: 'fixture', action_id: 'save',
    result: { display: { format: 'text', title: 'Saved', body: 'Updated', presentation: 'modal' } },
  }));
  const backend = backendFixture(execute);
  const rendered = renderWithMobileProviders(
    <ApplicationPluginsProvider backend={backend} connectionId="fixture">
      <GlobalDisplayLayer backend={backend} connectionId="fixture">
        <MobileDisplayHost scope="session" sessionId="session-1" />
      </GlobalDisplayLayer>
    </ApplicationPluginsProvider>,
  );
  act(() => emitDisplayPresentation(backend, normalizeDisplayEnvelope({
    id: 'fixture-display', source: 'action_response', connectionId: 'fixture',
    sessionId: 'session-1', display: NEUTRAL_FOLLOWUP_DISPLAY,
  })));
  fireEvent.press(screen.getByText('Enter value'));
  expect(screen.getByText('Edit value')).toBeTruthy();
  expect(execute).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId('application-action-dialog-cancel'));
  expect(screen.queryByText('Edit value')).toBeNull();
  expect(screen.getByText('Neutral result')).toBeTruthy();
  expect(execute).not.toHaveBeenCalled();
  fireEvent.press(screen.getByText('Enter value'));
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  expect(screen.getByText('Field "Value" is required.')).toBeTruthy();
  expect(execute).not.toHaveBeenCalled();
  fireEvent.changeText(screen.getByTestId('action-form-input-value'), 'updated value');
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  await waitFor(() => expect(screen.getByText('Saved')).toBeTruthy());
  expect(execute).toHaveBeenCalledWith(expect.objectContaining({
    sessionId: 'session-1', actionOwner: 'application',
    inputs: {
      source: 'neutral-result', value: 'updated value', cleared: '',
      note: 'kept note', session_id: 'session-1',
    },
  }));
  rendered.unmount();
});

test('a connection follow-up without a dialog executes immediately and reports errors', async () => {
  const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  const execute = jest.fn(async () => ({ status: 'error', message: 'Fixture error' }));
  const backend = { ...backendFixture(execute), executeAction: execute } as AgentBackend;
  const rendered = renderWithMobileProviders(
    <ApplicationPluginsProvider backend={backend} connectionId="fixture">
      <GlobalDisplayLayer backend={backend} connectionId="fixture">
        <MobileDisplayHost scope="connection" />
      </GlobalDisplayLayer>
    </ApplicationPluginsProvider>,
  );
  act(() => emitDisplayPresentation(backend, normalizeDisplayEnvelope({
    id: 'fixture-display', source: 'action_response', connectionId: 'fixture',
    display: {
      ...NEUTRAL_FOLLOWUP_DISPLAY,
      actions: [{
        kind: 'run_action', id: 'immediate', label: 'Run now', plugin: 'fixture',
        action_id: 'save', fixed_params: { value: 'immediate' },
      }],
    },
  })));
  fireEvent.press(screen.getByText('Run now'));
  await waitFor(() => expect(alert).toHaveBeenCalledWith('Action error', 'Fixture error'));
  expect(screen.queryByText('Edit value')).toBeNull();
  expect(screen.getByText('Neutral result')).toBeTruthy();
  expect(execute).toHaveBeenCalledWith(expect.objectContaining({
    inputs: { value: 'immediate' },
  }));
  rendered.unmount();
  alert.mockRestore();
});