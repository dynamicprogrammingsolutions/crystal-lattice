import React from 'react';
import { act, fireEvent, screen, within } from '@testing-library/react-native';
import { View } from 'react-native';

import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
} from '@crystal-lattice/frontend-sdk';

import { ApplicationPluginsProvider } from '../src/ApplicationPluginsContext';
import {
  MobileDisplayHost,
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
      >
        <MobileDisplayHost scope="connection" />
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

test('routes connection displays to Sessions and session displays to matching Chat', () => {
  jest.useFakeTimers();
  const backend = createBackend();
  const rendered = renderWithMobileProviders(
    <ApplicationPluginsProvider backend={backend} connectionId="test">
      <GlobalDisplayLayer backend={backend} connectionId="test">
        <View testID="sessions-surface">
          <MobileDisplayHost
            scope="connection"
            testID="sessions-notification-banner-rail"
          />
        </View>
        <View testID="chat-surface">
          <MobileDisplayHost
            scope="session"
            sessionId="session-1"
            testID="messages-notification-banner-rail"
          />
        </View>
      </GlobalDisplayLayer>
    </ApplicationPluginsProvider>,
  );

  act(() => {
    emitDisplayPresentation(
      backend,
      normalizeDisplayEnvelope({
        id: 'application-notification',
        source: 'application_notification',
        connectionId: 'test',
        display: {
          format: 'text',
          body: 'Application only',
          presentation: 'banner',
        },
      }),
    );
  });
  expect(
    within(screen.getByTestId('sessions-surface')).getByText('Application only'),
  ).toBeTruthy();
  expect(
    within(screen.getByTestId('chat-surface')).queryByText('Application only'),
  ).toBeNull();

  act(() => {
    emitDisplayPresentation(
      backend,
      normalizeDisplayEnvelope({
        id: 'session-notification',
        source: 'session_notification',
        connectionId: 'test',
        sessionId: 'session-1',
        display: {
          format: 'text',
          body: 'Matching session only',
          presentation: 'banner',
        },
      }),
    );
    emitDisplayPresentation(
      backend,
      normalizeDisplayEnvelope({
        id: 'other-session-notification',
        source: 'session_notification',
        connectionId: 'test',
        sessionId: 'session-2',
        display: {
          format: 'text',
          body: 'Other session',
          presentation: 'banner',
        },
      }),
    );
  });
  expect(
    within(screen.getByTestId('chat-surface')).getByText('Matching session only'),
  ).toBeTruthy();
  expect(
    within(screen.getByTestId('sessions-surface')).queryByText('Matching session only'),
  ).toBeNull();
  expect(screen.queryByText('Other session')).toBeNull();
  expect(screen.queryByText('test')).toBeNull();
  expect(screen.queryByText('session-1')).toBeNull();

  rendered.unmount();
  jest.useRealTimers();
});