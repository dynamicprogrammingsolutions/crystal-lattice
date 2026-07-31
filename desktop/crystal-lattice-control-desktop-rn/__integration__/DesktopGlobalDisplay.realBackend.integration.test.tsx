import React from 'react';
import { render, screen } from '@testing-library/react-native';

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

const CONFIG = {
  providers: {
    echo: { provider: 'echo_openai_like', model: 'test-model' },
  },
  agents: { default: { provider: 'echo' } },
  plugins: [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'path:${env:REPO_ROOT}/plugins/dummy-application-notification-app',
  ],
};

let started: StartedServer | null = null;

afterEach(async () => {
  await started?.stop();
  started = null;
});

test(
  'renders a real owner-memory application notification in the desktop banner rail',
  async () => {
    started = await startBackendServer({ config: CONFIG, startupTimeoutMs: 30000 });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
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

    await new Promise<void>((resolve) => setTimeout(resolve, 500));
    const response = await backend.executeAction({
      pluginId: 'dummy_application_notification',
      actionId: 'emit_application_notification',
      inputs: { presentation: 'banner', variant: 'success' },
    });
    expect(response.status).toBe('ok');
    expect(
      await screen.findByText('Application notification demo', {}, { timeout: 10000 }),
    ).toBeTruthy();
    expect(screen.getByText('Local integration server')).toBeTruthy();

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
  },
  60000,
);