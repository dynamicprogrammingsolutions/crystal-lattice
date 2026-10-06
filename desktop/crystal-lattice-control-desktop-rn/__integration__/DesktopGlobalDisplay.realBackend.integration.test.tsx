import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import {
  FetchTransport,
  RestAgentBackend,
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  runApplicationAction,
  type ActionUiElement,
} from '@crystal-lattice/frontend-sdk';
jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  default: { OS: 'macos', select: (values: any) => values.macos ?? values.default },
}));
jest.mock('@crystal-lattice/frontend-rn-components', () => ({
  ...jest.requireActual('@crystal-lattice/frontend-rn-components'),
}));
jest.mock('../src/windows/desktopWindowManager', () => ({
  DesktopWindowManager: {
    openReactWindow: jest.fn(), closeReactWindow: jest.fn(),
    openApplicationActionDialogWindow: jest.fn(), closeApplicationActionDialogWindow: jest.fn(),
    openApplicationActionDialogPopover: jest.fn(), closeApplicationActionDialogPopover: jest.fn(),
  },
  desktopWindowEvents: null,
}));
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import { startBackendServer, type StartedServer } from '../../../packages/frontend-sdk/src/integration/harness';

import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';
import {
  DesktopConnectionDisplayRail,
  DesktopGlobalDisplayLayer,
} from '../src/ui/DesktopGlobalDisplayLayer';
import { DesktopSessionNotificationRail } from '../src/ui/DesktopSessionNotificationRail';
import { ApplicationActionDialogWindow } from '../src/windows/ApplicationActionDialogWindow';
import { clearActiveApplicationActionDialog } from '../src/windows/applicationActionDialogCoordinator';

const CONFIG = {
  providers: {
    echo: { provider: 'echo_openai_like', model: 'test-model' },
  },
  agents: { default: { provider: 'echo' } },
  plugins: [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'path:${env:REPO_ROOT}/plugins/dummy-application-notification-app',
    'path:${env:REPO_ROOT}/plugins/dummy-session-notification-app',
    'path:${env:REPO_ROOT}/plugins/dummy-action-display-form-app',
  ],
};

let started: StartedServer | null = null;

afterEach(async () => {
  clearActiveApplicationActionDialog();
  await started?.stop();
  started = null;
});

test('submits a neutral follow-up through the production desktop dialog and real HTTP backend', async () => {
  started = await startBackendServer({ config: CONFIG, startupTimeoutMs: 30000 });
  const backend = new RestAgentBackend({ transport: new FetchTransport({ baseUrl: started.baseUrl }) });
  const created = await backend.createSession({ agentId: 'default' });
  const sessionId = created.session.session_id;
  const schema = await backend.getSessionApplicationUiSchema(sessionId, {
    pluginId: 'dummy_action_display_form_app',
  });
  const shown = await runApplicationAction({
    backend,
    element: schema.find((item: any) => item.id === 'dummy_show_followup_dialog') as ActionUiElement,
    actionsById: {}, context: { sessionId },
  });
  const rendered = render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={{ local: { status: 'open', baseUrl: started.baseUrl, backend } }}
        connectionNameById={{ local: 'Fixture backend' }}
      >
        <DesktopConnectionDisplayRail />
        <ApplicationActionDialogWindow presentation="window" />
      </DesktopGlobalDisplayLayer>
    </ThemeProvider>,
  );
  act(() => emitDisplayPresentation(backend, normalizeDisplayEnvelope({
    source: 'action_response', connectionId: 'local', sessionId,
    ownershipScope: 'connection', display: shown.display!,
  })));
  fireEvent.press(screen.getByText('Enter value'));
  fireEvent.changeText(screen.getByTestId('action-form-input-value'), 'Desktop HTTP value');
  fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
  await waitFor(() => expect(screen.getByText('Follow-up submitted')).toBeTruthy());
  expect(screen.getByText('Value: Desktop HTTP value\nNote: ')).toBeTruthy();
  rendered.unmount();
}, 60000);

test(
  'hydrates and dismisses a real application notification in the desktop rail',
  async () => {
    started = await startBackendServer({ config: CONFIG, startupTimeoutMs: 30000 });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    await backend.executeAction({
      pluginId: 'dummy_application_notification',
      actionId: 'emit_application_notification',
      inputs: { presentation: 'banner', variant: 'success' },
    });
    const renderRail = () =>
      render(
      <ThemeProvider theme={buildDesktopTheme(null)}>
        <DesktopGlobalDisplayLayer
          openConnectionsById={{
            local: {
              status: 'open',
              baseUrl: started.baseUrl,
              backend,
            },
          }}
          connectionNameById={{ local: 'Local integration server' }}
        >
          <DesktopConnectionDisplayRail />
        </DesktopGlobalDisplayLayer>
      </ThemeProvider>,
    );

    const rendered = renderRail();
    expect(
      await screen.findByText('Application notification demo', {}, { timeout: 10000 }),
    ).toBeTruthy();
    expect(screen.getByText('Local integration server')).toBeTruthy();
    fireEvent.press(screen.getByLabelText('Dismiss notification'));
    await waitFor(async () => {
      expect(await backend.listApplicationNotifications!()).toEqual([]);
      expect(screen.queryByText('Application notification demo')).toBeNull();
    });

    rendered.unmount();
    const reopened = renderRail();
    await waitFor(() => {
      expect(screen.queryByText('Application notification demo')).toBeNull();
    });

    const modalResponse = await backend.executeAction({
      pluginId: 'dummy_application_notification',
      actionId: 'emit_application_notification',
      inputs: { presentation: 'modal', variant: 'warning' },
    });
    expect(modalResponse.status).toBe('ok');
    expect(
      await screen.findByText(
        'warning notification using modal presentation.',
        {},
        { timeout: 10000 },
      ),
    ).toBeTruthy();
    reopened.unmount();
  },
  60000,
);

test(
  'hydrates and dismisses a real session notification with desktop inline fallback',
  async () => {
    started = await startBackendServer({ config: CONFIG, startupTimeoutMs: 30000 });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    await backend.executeSessionAction!({
      sessionId,
      pluginId: 'dummy_session_notification',
      actionId: 'emit_session_notification',
      actionOwner: 'application',
      inputs: { presentation: 'modal', variant: 'warning' },
    });
    const renderRail = () =>
      render(
        <ThemeProvider theme={buildDesktopTheme(null)}>
          <DesktopSessionNotificationRail
            backend={backend}
            connectionId="local"
            sessionId={sessionId}
            sessionSummary={null}
          />
        </ThemeProvider>,
      );

    const rendered = renderRail();
    expect(
      await screen.findByText(
        'warning notification using modal presentation.',
        {},
        { timeout: 10000 },
      ),
    ).toBeTruthy();
    fireEvent.press(screen.getByText('Close'));
    await waitFor(async () => {
      expect(await backend.listSessionNotifications!(sessionId)).toEqual([]);
      expect(
        screen.queryByText('warning notification using modal presentation.'),
      ).toBeNull();
    });

    rendered.unmount();
    const reopened = renderRail();
    await waitFor(() => {
      expect(
        screen.queryByText('warning notification using modal presentation.'),
      ).toBeNull();
    });
    reopened.unmount();
  },
  60000,
);