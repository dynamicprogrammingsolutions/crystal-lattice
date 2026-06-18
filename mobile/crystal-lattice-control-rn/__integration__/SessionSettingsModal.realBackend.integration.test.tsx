import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';

import SessionSettingsModal from '../src/components/SessionSettingsModal';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import {
  createMobileComponentSession,
  startMobileComponentBackend,
  type StartedMobileComponentBackend,
} from './support/mobileComponentBackend';

const SERVER_CONFIG = {
  providers: {
    test_provider: {
      provider: 'deterministic_stream',
      model: 'test-model',
      timeout: 60,
      stream_chunk_count: 1,
      stream_chunk_delay_ms: 0,
    },
  },
  plugins: [
    'plugins.deterministic_stream_provider.DeterministicStreamProvider',
    'path:${env:BUILTIN_PLUGINS}/feature-request-options',
  ],
  agents: {
    default: {
      provider: 'test_provider',
      request_options: {
        temperature: '0.5',
        max_tokens: '512',
        thinking: {
          clear_thinking: false,
        },
      },
      request_options_ui: {
        temperature: ['0.0', '0.5', '1.0'],
        max_tokens: ['512', '1024'],
        thinking: {
          clear_thinking: 'checkbox',
        },
      },
    },
  },
};

describe('SessionSettingsModal real-backend component integration', () => {
  let started: StartedMobileComponentBackend | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('renders default-config path plugin settings from the real backend and patches overrides', async () => {
    started = await startMobileComponentBackend({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const sessionId = await createMobileComponentSession(started.backend);

    renderWithMobileProviders(
      <SessionSettingsModal
        backend={started.backend}
        sessionId={sessionId}
        visible
        onRequestClose={jest.fn()}
      />,
    );

    expect(await screen.findByText('Temperature')).toBeTruthy();
    expect(screen.getByText('0.0')).toBeTruthy();
    expect(screen.getByText('0.5')).toBeTruthy();
    expect(screen.getByText('1.0')).toBeTruthy();
    expect(screen.getByText('Max Tokens')).toBeTruthy();
    expect(screen.getByText('512')).toBeTruthy();
    expect(screen.getByText('1024')).toBeTruthy();
    expect(screen.getByText('Thinking Clear Thinking')).toBeTruthy();

    fireEvent.press(screen.getByText('1.0'));

    await waitFor(async () => {
      const overrides = await started!.backend.getSessionOverrides(sessionId);
      expect(overrides.request_options__temperature).toBe('1.0');
    });

    fireEvent.press(screen.getByText('1024'));
    await waitFor(async () => {
      const overrides = await started!.backend.getSessionOverrides(sessionId);
      expect(overrides.request_options__max_tokens).toBe('1024');
    });
  });
});
