import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import {
  FetchTransport,
  RestAgentBackend,
} from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import { startBackendServer, type StartedServer } from '../../../packages/frontend-sdk/src/integration/harness';

import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';
import {
  DesktopConnectionDisplayRail,
  DesktopGlobalDisplayLayer,
} from '../src/ui/DesktopGlobalDisplayLayer';
import { DesktopSessionNotificationRail } from '../src/ui/DesktopSessionNotificationRail';

const CONFIG = {
  providers: {
    echo: { provider: 'echo_openai_like', model: 'test-model' },
  },
  agents: { default: { provider: 'echo' } },
  plugins: [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'path:${env:REPO_ROOT}/plugins/dummy-application-notification-app',
    'path:${env:REPO_ROOT}/plugins/dummy-session-notification-app',
  ],
};

let started: StartedServer | null = null;

afterEach(async () => {
  await started?.stop();
  started = null;
});

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