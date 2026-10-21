import React from 'react';

jest.mock('../src/windows/desktopWindowManager', () => {
  const emitter = new (require('events').EventEmitter)();
  return {
    DesktopWindowManager: {
      openReactWindow: jest.fn(),
      closeReactWindow: jest.fn(),
      closeApplicationActionDialogPopover: jest.fn(),
      closeApplicationActionDialogWindow: jest.fn(),
    },
    desktopWindowEvents: {
      addListener: (event: string, listener: (...args: any[]) => void) => {
        emitter.on(event, listener);
        return { remove: () => emitter.removeListener(event, listener) };
      },
      emit: (event: string, payload: any) => emitter.emit(event, payload),
    },
  };
});

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
import {
  clearActiveActionDisplayWindow,
  getActiveActionDisplayWindow,
} from '../src/windows/actionDisplayWindowCoordinator';
import { ActionDisplayWindow } from '../src/windows/ActionDisplayWindow';
import {
  desktopWindowEvents,
  DesktopWindowManager,
} from '../src/windows/desktopWindowManager';

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

test.each(['Close button', 'window close'])(
  'reopens a duration report with the same display ID after %s',
  async closeMethod => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    const backend = createBackend();
    const rendered = render(
      <ThemeProvider theme={buildDesktopTheme(null)}>
        <DesktopGlobalDisplayLayer
          openConnectionsById={{
            local: {
              status: 'open',
              baseUrl: 'http://local',
              backend: backend as any,
            },
          }}
          connectionNameById={{ local: 'Local project' }}
        >
          <ActionDisplayWindow />
        </DesktopGlobalDisplayLayer>
      </ThemeProvider>,
    );
    const present = (body: string) => {
      emitDisplayPresentation(
        backend,
        normalizeDisplayEnvelope({
          source: 'action_response',
          connectionId: 'local',
          sessionId: 'session-1',
          display: {
            display_id: 'duration-tracking-report',
            title: 'Duration report',
            format: 'text',
            body,
            presentation: 'modal',
            dismissible: true,
          },
        }),
      );
    };
    await act(async () => {});

    for (const body of ['First report', 'Updated report', 'Updated report']) {
      act(() => present(body));
      expect(screen.getByText(body)).toBeTruthy();
      expect(getActiveActionDisplayWindow()?.state.display.body).toBe(body);
      expect(DesktopWindowManager?.openReactWindow).toHaveBeenLastCalledWith(
        expect.objectContaining({
          windowKey: 'actionDisplay',
          title: 'Duration report',
        }),
      );

      act(() => {
        if (closeMethod === 'Close button') {
          fireEvent.press(screen.getByText('Close'));
        } else {
          desktopWindowEvents?.emit('reactWindowCancelled', {
            windowKey: 'actionDisplay',
          });
        }
      });
      expect(getActiveActionDisplayWindow()).toBeNull();
      expect(screen.queryByText(body)).toBeNull();
    }

    expect(DesktopWindowManager?.openReactWindow).toHaveBeenCalledTimes(3);
    rendered.unmount();
    clearActiveActionDisplayWindow();
    jest.useRealTimers();
  },
);

test('aggregates connection displays and routes direct modals to the action window', () => {
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
  expect(screen.getByText('First connection')).toBeTruthy();
  expect(screen.queryByText('Second application display')).toBeNull();
  expect(screen.queryByText('Session display')).toBeNull();
  expect(getActiveActionDisplayWindow()?.state).toEqual(
    expect.objectContaining({
      display: expect.objectContaining({
        body: 'Second application display',
        presentation: 'modal',
      }),
      contextLabel: 'Second connection',
    }),
  );

  rendered.unmount();
  clearActiveActionDisplayWindow();
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