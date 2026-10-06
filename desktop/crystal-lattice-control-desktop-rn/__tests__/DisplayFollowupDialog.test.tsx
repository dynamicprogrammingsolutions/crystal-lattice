import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import { emitDisplayPresentation, normalizeDisplayEnvelope, type AgentBackend } from '@crystal-lattice/frontend-sdk';

jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  default: { OS: 'macos', select: (values: any) => values.macos ?? values.default },
}));
jest.mock('@crystal-lattice/frontend-rn-components', () => ({
  ...jest.requireActual('@crystal-lattice/frontend-rn-components'),
}));
jest.mock('../src/windows/desktopWindowManager', () => ({
  DesktopWindowManager: {
    openReactWindow: jest.fn(),
    closeReactWindow: jest.fn(),
    openApplicationActionDialogWindow: jest.fn(),
    closeApplicationActionDialogWindow: jest.fn(),
    openApplicationActionDialogPopover: jest.fn(),
    closeApplicationActionDialogPopover: jest.fn(),
  },
  desktopWindowEvents: null,
}));

import { NEUTRAL_FOLLOWUP_DISPLAY } from '../../../test/fixture/displayFollowupDialog';
import { DesktopGlobalDisplayLayer } from '../src/ui/DesktopGlobalDisplayLayer';
import { ActionDisplayWindow } from '../src/windows/ActionDisplayWindow';
import { ApplicationActionDialogWindow } from '../src/windows/ApplicationActionDialogWindow';
import { DesktopWindowManager } from '../src/windows/desktopWindowManager';
import { clearActiveActionDisplayWindow } from '../src/windows/actionDisplayWindowCoordinator';
import { clearActiveApplicationActionDialog } from '../src/windows/applicationActionDialogCoordinator';

afterEach(() => {
  clearActiveActionDisplayWindow();
  clearActiveApplicationActionDialog();
  jest.clearAllMocks();
});

test('detached result window opens the production dialog window and retains its backend context', async () => {
  const execute = jest.fn(async () => ({
    status: 'ok', plugin: 'fixture', action_id: 'save',
    result: { display: { format: 'text', title: 'Saved', body: 'Updated', presentation: 'modal' } },
  }));
  const backend = {
    kind: 'fixture',
    getLatestEventId: async () => '0',
    listEvents: async () => ({ events: [], latestEventId: '0' }),
    executeSessionAction: execute,
  } as unknown as AgentBackend;
  const otherBackend = { ...backend, executeSessionAction: jest.fn() };
  const rendered = render(
    <DesktopGlobalDisplayLayer
      openConnectionsById={{
        first: { status: 'open', baseUrl: 'http://fixture', backend: backend as any },
        other: { status: 'open', baseUrl: 'http://other', backend: otherBackend as any },
      }}
      connectionNameById={{ first: 'Fixture', other: 'Other' }}
    >
      <ActionDisplayWindow />
      <ApplicationActionDialogWindow presentation="window" />
    </DesktopGlobalDisplayLayer>,
  );
  act(() => emitDisplayPresentation(backend, normalizeDisplayEnvelope({
    id: 'fixture-display', source: 'action_response', connectionId: 'first',
    sessionId: 'session-1', display: NEUTRAL_FOLLOWUP_DISPLAY,
  })));
  fireEvent.press(screen.getByText('Enter value'));
  expect(screen.getByText('Edit value')).toBeTruthy();
  expect(DesktopWindowManager?.openApplicationActionDialogWindow).toHaveBeenCalledWith({ title: 'Enter value' });
  expect(DesktopWindowManager?.openApplicationActionDialogPopover).not.toHaveBeenCalled();
  expect(execute).not.toHaveBeenCalled();
  fireEvent.press(screen.getByTestId('application-action-dialog-cancel'));
  expect(screen.queryByText('Edit value')).toBeNull();
  expect(screen.getByText('Neutral result')).toBeTruthy();
  await screen.findByText('Enter value');
  fireEvent.press(screen.getByText('Enter value'));
  fireEvent.changeText(screen.getByTestId('action-form-input-value'), 'desktop value');
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  await waitFor(() => expect(screen.getByText('Saved')).toBeTruthy());
  expect(execute).toHaveBeenCalledWith(expect.objectContaining({
    sessionId: 'session-1', actionOwner: 'application',
    inputs: {
      source: 'neutral-result', value: 'desktop value', cleared: '',
      note: 'kept note', session_id: 'session-1',
    },
  }));
  expect(otherBackend.executeSessionAction).not.toHaveBeenCalled();
  rendered.unmount();
});