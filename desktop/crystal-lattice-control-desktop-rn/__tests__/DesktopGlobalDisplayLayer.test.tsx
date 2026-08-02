import React from 'react';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
} from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';
import {
  DesktopConnectionDisplayRail,
  DesktopGlobalDisplayLayer,
} from '../src/ui/DesktopGlobalDisplayLayer';

function createBackend(): AgentBackend {
  return {
    kind: 'inProcess',
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

test('aggregates connection displays and excludes session displays', () => {
  jest.useFakeTimers();
  const first = createBackend();
  const second = createBackend();
  const rendered = render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={{
          first: { status: 'open', baseUrl: 'http://first', backend: first as any },
          second: { status: 'open', baseUrl: 'http://second', backend: second as any },
        }}
        connectionNameById={{
          first: 'First connection',
          second: 'Second connection',
        }}
      >
        <DesktopConnectionDisplayRail />
      </DesktopGlobalDisplayLayer>
    </ThemeProvider>,
  );

  act(() => {
    emitDisplayPresentation(
      first,
      normalizeDisplayEnvelope({
        id: 'first-display',
        source: 'action_response',
        ownershipScope: 'connection',
        connectionId: 'first',
        display: {
          format: 'text',
          body: 'First application display',
          presentation: 'banner',
        },
      }),
    );
    emitDisplayPresentation(
      second,
      normalizeDisplayEnvelope({
        id: 'second-display',
        source: 'action_response',
        ownershipScope: 'connection',
        connectionId: 'second',
        display: {
          format: 'text',
          body: 'Second application display',
          presentation: 'modal',
        },
      }),
    );
    emitDisplayPresentation(
      first,
      normalizeDisplayEnvelope({
        id: 'session-display',
        source: 'session_notification',
        connectionId: 'first',
        sessionId: 'session-1',
        display: {
          format: 'text',
          body: 'Session display',
          presentation: 'banner',
        },
      }),
    );
  });

  expect(screen.getByText('First application display')).toBeTruthy();
  expect(screen.getByText('Second application display')).toBeTruthy();
  expect(screen.getByText('First connection')).toBeTruthy();
  expect(screen.getByText('Second connection')).toBeTruthy();
  expect(screen.queryByText('Session display')).toBeNull();

  rendered.unmount();
  jest.useRealTimers();
});

test('hydrates and dismisses an application notification through its connection backend', async () => {
  let notifications = [
    {
      id: 'application-notification',
      key: 'demo',
      kind: 'notification' as const,
      status: 'pending' as const,
      revision: 1,
      severity: 'warning' as const,
      title: 'Application notification',
      body: 'Server-owned desktop notification',
      created_at: '2026-08-01T00:00:00Z',
      updated_at: '2026-08-01T00:00:00Z',
      source: { plugin: 'dummy' },
      display: {
        format: 'text' as const,
        body: 'Server-owned desktop notification',
        presentation: 'banner' as const,
        dismissible: true,
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
    render(
      <ThemeProvider theme={buildDesktopTheme(null)}>
        <DesktopGlobalDisplayLayer
          openConnectionsById={{
            first: {
              status: 'open',
              baseUrl: 'http://first',
              backend: backend as any,
            },
          }}
          connectionNameById={{ first: 'First connection' }}
        >
          <DesktopConnectionDisplayRail />
        </DesktopGlobalDisplayLayer>
      </ThemeProvider>,
    );

  const rendered = renderLayer();
  expect(await screen.findByText('Server-owned desktop notification')).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Dismiss notification'));
  await waitFor(() => {
    expect(dismissApplicationNotification).toHaveBeenCalledWith(
      'application-notification',
      { expectedRevision: 1, reason: 'user' },
    );
    expect(screen.queryByText('Server-owned desktop notification')).toBeNull();
  });

  rendered.unmount();
  const reopened = renderLayer();
  await waitFor(() => {
    expect(screen.queryByText('Server-owned desktop notification')).toBeNull();
  });
  reopened.unmount();
});

test('isolates authoritative dismissal between open desktop connections', async () => {
  const buildNotification = (id: string, body: string) => ({
    id,
    key: `demo:${id}`,
    kind: 'notification' as const,
    status: 'pending' as const,
    revision: 4,
    severity: 'info' as const,
    title: body,
    body,
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
    source: { plugin: 'dummy' },
    display: {
      format: 'text' as const,
      body,
      presentation: 'banner' as const,
      dismissible: true,
    },
    model_visibility: 'hidden' as const,
  });
  let firstNotifications = [buildNotification('first-notification', 'First server')];
  const secondNotifications = [
    buildNotification('second-notification', 'Second server'),
  ];
  const firstDismiss = jest.fn(async () => {
    const dismissed = {
      ...firstNotifications[0],
      status: 'dismissed' as const,
      revision: 5,
      updated_at: '2026-08-01T00:00:01Z',
      dismissal: { dismissed_at: '2026-08-01T00:00:01Z' },
    };
    firstNotifications = [];
    return dismissed;
  });
  const secondDismiss = jest.fn();
  const first = {
    ...createBackend(),
    listApplicationNotifications: jest.fn(async () => firstNotifications),
    dismissApplicationNotification: firstDismiss,
  } as AgentBackend;
  const second = {
    ...createBackend(),
    listApplicationNotifications: jest.fn(async () => secondNotifications),
    dismissApplicationNotification: secondDismiss,
  } as AgentBackend;
  render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={{
          first: {
            status: 'open',
            baseUrl: 'http://first',
            backend: first as any,
          },
          second: {
            status: 'open',
            baseUrl: 'http://second',
            backend: second as any,
          },
        }}
        connectionNameById={{
          first: 'First connection',
          second: 'Second connection',
        }}
      >
        <DesktopConnectionDisplayRail />
      </DesktopGlobalDisplayLayer>
    </ThemeProvider>,
  );

  expect(await screen.findByText('First server')).toBeTruthy();
  expect(await screen.findByText('Second server')).toBeTruthy();
  fireEvent.press(screen.getAllByLabelText('Dismiss notification')[0]);
  await waitFor(() => {
    expect(firstDismiss).toHaveBeenCalledWith('first-notification', {
      expectedRevision: 4,
      reason: 'user',
    });
    expect(secondDismiss).not.toHaveBeenCalled();
    expect(screen.queryByText('First server')).toBeNull();
    expect(screen.getByText('Second server')).toBeTruthy();
  });
});

test('suppresses an elapsed TTL application notification during desktop hydration', async () => {
  const listApplicationNotifications = jest.fn(async () => [
    {
      id: 'elapsed-notification',
      key: 'demo:elapsed',
      kind: 'notification' as const,
      status: 'pending' as const,
      revision: 1,
      severity: 'info' as const,
      title: 'Elapsed notification',
      body: 'Should not be freshly presented',
      created_at: '2020-01-01T00:00:00Z',
      updated_at: '2020-01-01T00:00:00Z',
      retention: {
        version: 1 as const,
        policy: 'ttl' as const,
        expires_at: '2020-01-01T00:01:00Z',
      },
      source: { plugin: 'dummy' },
      display: {
        format: 'text' as const,
        body: 'Should not be freshly presented',
        presentation: 'banner' as const,
      },
      model_visibility: 'hidden' as const,
    },
  ]);
  const backend = {
    ...createBackend(),
    listApplicationNotifications,
    dismissApplicationNotification: jest.fn(),
  } as AgentBackend;
  render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={{
          first: {
            status: 'open',
            baseUrl: 'http://first',
            backend: backend as any,
          },
        }}
        connectionNameById={{ first: 'First connection' }}
      >
        <DesktopConnectionDisplayRail />
      </DesktopGlobalDisplayLayer>
    </ThemeProvider>,
  );

  await waitFor(() => {
    expect(listApplicationNotifications).toHaveBeenCalled();
  });
  expect(screen.queryByText('Should not be freshly presented')).toBeNull();
});