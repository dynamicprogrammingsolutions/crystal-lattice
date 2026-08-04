import React from 'react';
import {
  act,
  fireEvent,
  screen,
  waitFor,
  within,
} from '@testing-library/react-native';
import { Alert, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

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

beforeEach(async () => {
  await AsyncStorage.clear();
});

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
        source: 'action_response',
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
        source: 'action_response',
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

test('persists application notification dismissal and does not rehydrate it', async () => {
  let notifications = [
    {
      id: 'application-notification',
      key: 'demo',
      kind: 'notification' as const,
      status: 'pending' as const,
      revision: 1,
      severity: 'info' as const,
      title: 'Application notification',
      body: 'Persisted application notification',
      created_at: '2026-08-01T00:00:00Z',
      updated_at: '2026-08-01T00:00:00Z',
      source: { plugin: 'dummy' },
      display: {
        format: 'text' as const,
        body: 'Persisted application notification',
        presentation: 'banner' as const,
      },
      model_visibility: 'hidden' as const,
    },
  ];
  const dismissApplicationNotification = jest.fn(async () => {
    const dismissed = {
      ...notifications[0],
      status: 'dismissed' as const,
      revision: 2,
      updated_at: '2026-08-01T00:00:01Z',
      dismissal: { dismissed_at: '2026-08-01T00:00:01Z' },
    };
    notifications = [];
    return dismissed;
  });
  const backend = {
    ...createBackend(),
    listApplicationNotifications: jest.fn(async () => notifications),
    dismissApplicationNotification,
  } as AgentBackend;

  const renderLayer = () =>
    renderWithMobileProviders(
      <ApplicationPluginsProvider backend={backend} connectionId="test">
        <GlobalDisplayLayer backend={backend} connectionId="test">
          <MobileDisplayHost scope="connection" />
        </GlobalDisplayLayer>
      </ApplicationPluginsProvider>,
    );

  const rendered = renderLayer();
  expect(
    await screen.findByText('Persisted application notification'),
  ).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Dismiss notification'));
  await waitFor(() => {
    expect(dismissApplicationNotification).toHaveBeenCalledWith(
      'application-notification',
      { expectedRevision: 1, reason: 'user' },
    );
    expect(
      screen.queryByText('Persisted application notification'),
    ).toBeNull();
  });

  rendered.unmount();
  const reopened = renderLayer();
  await waitFor(() => {
    expect(
      screen.queryByText('Persisted application notification'),
    ).toBeNull();
  });
  reopened.unmount();
});

test('keeps a failed application dismissal hidden and presents a newer revision', async () => {
  let notification = {
    id: 'application-notification',
    key: 'demo',
    kind: 'notification' as const,
    status: 'pending' as const,
    revision: 1,
    severity: 'info' as const,
    title: 'Application notification',
    body: 'Cached application notification',
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
    source: { plugin: 'dummy' },
    display: {
      format: 'text' as const,
      body: 'Cached application notification',
      presentation: 'banner' as const,
    },
    model_visibility: 'hidden' as const,
  };
  const dismissApplicationNotification = jest.fn(async () => {
    throw new Error('server unavailable');
  });
  const backend = {
    ...createBackend(),
    listApplicationNotifications: jest.fn(async () => [notification]),
    dismissApplicationNotification,
  } as AgentBackend;
  const alert = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  const renderLayer = () =>
    renderWithMobileProviders(
      <ApplicationPluginsProvider backend={backend} connectionId="test">
        <GlobalDisplayLayer backend={backend} connectionId="test">
          <MobileDisplayHost scope="connection" />
        </GlobalDisplayLayer>
      </ApplicationPluginsProvider>,
    );

  const rendered = renderLayer();
  expect(await screen.findByText('Cached application notification')).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Dismiss notification'));
  await waitFor(() => {
    expect(screen.queryByText('Cached application notification')).toBeNull();
    expect(dismissApplicationNotification).toHaveBeenCalledWith(
      'application-notification',
      { expectedRevision: 1, reason: 'user' },
    );
  });
  expect(alert).not.toHaveBeenCalled();

  rendered.unmount();
  const reopened = renderLayer();
  await waitFor(() => {
    expect(screen.queryByText('Cached application notification')).toBeNull();
    expect(dismissApplicationNotification.mock.calls.length).toBeGreaterThan(1);
  });

  notification = {
    ...notification,
    revision: 2,
    body: 'New application revision',
    updated_at: '2026-08-01T00:00:01Z',
    display: {
      ...notification.display,
      body: 'New application revision',
    },
  };
  reopened.unmount();
  const updated = renderLayer();
  expect(await screen.findByText('New application revision')).toBeTruthy();

  updated.unmount();
  alert.mockRestore();
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