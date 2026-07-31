import React from 'react';
import { act, fireEvent, screen } from '@testing-library/react-native';

import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
} from '@crystal-lattice/frontend-sdk';

import { ApplicationPluginsProvider } from '../src/ApplicationPluginsContext';
import {
  GlobalNotificationBannerSlot,
} from '../src/components/GlobalDisplayLayer';
import GlobalDisplayLayer from '../src/components/GlobalDisplayLayer';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

function createBackend(): AgentBackend {
  return {
    kind: 'inProcess',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => [],
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

test('presents a later revision after dismissing the same lifecycle id', () => {
  jest.useFakeTimers();
  const backend = createBackend();
  const rendered = renderWithMobileProviders(
    <ApplicationPluginsProvider backend={backend} connectionId="test">
      <GlobalDisplayLayer
        backend={backend}
        connectionId="test"
        connectionName="Test connection"
      >
        <GlobalNotificationBannerSlot />
      </GlobalDisplayLayer>
    </ApplicationPluginsProvider>,
  );

  act(() => {
    emitDisplayPresentation(
      backend,
      normalizeDisplayEnvelope({
        id: 'same-notification',
        source: 'application_notification',
        connectionId: 'test',
        updatedAt: '2026-07-30T00:00:00Z',
        display: {
          format: 'text',
          body: 'First revision',
          presentation: 'banner',
        },
      }),
    );
  });
  expect(screen.getByText('First revision')).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Dismiss notification'));
  expect(screen.queryByText('First revision')).toBeNull();

  act(() => {
    emitDisplayPresentation(
      backend,
      normalizeDisplayEnvelope({
        id: 'same-notification',
        source: 'application_notification',
        connectionId: 'test',
        updatedAt: '2026-07-30T00:00:01Z',
        display: {
          format: 'text',
          title: 'Updated revision',
          body: 'Second revision',
          presentation: 'modal',
        },
      }),
    );
  });
  expect(screen.getByText('Updated revision')).toBeTruthy();
  expect(screen.getByText('Second revision')).toBeTruthy();

  rendered.unmount();
  jest.useRealTimers();
});