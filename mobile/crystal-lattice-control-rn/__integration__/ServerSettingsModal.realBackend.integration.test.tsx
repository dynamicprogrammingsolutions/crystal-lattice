import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';

import ServerSettingsModal from '../src/components/ServerSettingsModal';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import {
  startMobileComponentBackend,
  type StartedMobileComponentBackend,
} from './support/mobileComponentBackend';

const SERVER_CONFIG = {
  providers: {
    dummy: {
      provider: 'dummy_provider',
      model: 'test-model',
    },
  },
  plugins: [
    'tests.dummy_provider.DummyProvider',
    'path:${env:BUILTIN_PLUGINS}/dummy-settings-app',
  ],
  agents: {
    default: {
      provider: 'dummy',
    },
  },
};

describe('ServerSettingsModal real-backend component integration', () => {
  let started: StartedMobileComponentBackend | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('renders server-scoped dummy plugin settings and patches live server settings', async () => {
    started = await startMobileComponentBackend({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });

    renderWithMobileProviders(
      <ServerSettingsModal
        backend={started.backend}
        visible
        onRequestClose={jest.fn()}
      />,
    );

    expect(await screen.findByText('Dummy server mode')).toBeTruthy();
    expect(screen.getByText('Fast')).toBeTruthy();
    expect(screen.getByText('Careful')).toBeTruthy();
    expect(screen.getByText('Dummy server enabled')).toBeTruthy();
    expect(screen.getByText('Show more parameters')).toBeTruthy();
    expect(screen.queryByText('Dummy session mode')).toBeNull();
    expect(screen.queryByText('Dummy extra text 01')).toBeNull();
    expect(screen.getByTestId('server-settings-scroll')).toBeTruthy();

    fireEvent.press(screen.getByText('Careful'));

    await waitFor(async () => {
      const settings = await started!.backend.getServerSettings();
      expect(settings.dummy_server_mode).toBe('careful');
    });

    fireEvent(screen.getByLabelText('Show more parameters'), 'valueChange', true);

    await waitFor(async () => {
      const settings = await started!.backend.getServerSettings();
      expect(settings.dummy_show_more_parameters).toBe(true);
    });

    expect(await screen.findByText('Dummy extra text 01')).toBeTruthy();
    expect(await screen.findByText('Dummy extra text 16')).toBeTruthy();
  });
});