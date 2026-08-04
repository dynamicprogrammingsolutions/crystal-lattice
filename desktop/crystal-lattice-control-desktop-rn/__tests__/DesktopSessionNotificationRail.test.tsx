import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import type {
  AgentBackend,
  SessionNotification,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { selectSessionNotifications } from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';
import { DesktopSessionNotificationRail } from '../src/ui/DesktopSessionNotificationRail';

const notification: SessionNotification = {
  id: 'session-notification',
  key: 'demo:session',
  kind: 'notification',
  status: 'pending',
  revision: 1,
  severity: 'warning',
  title: 'Session notification',
  body: 'Server-owned session notification',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z',
  source: { plugin: 'dummy' },
  display: {
    format: 'text',
    body: 'Server-owned session notification',
    presentation: 'modal',
    dismissible: true,
  },
  model_visibility: 'hidden',
};

function summary(items: SessionNotification[]): SessionSummary {
  return {
    session_id: 'session-1',
    modified: 0,
    preview: '',
    metadata: { notifications: { items } },
  };
}

test('hydrates, renders modal as inline, and persists session dismissal', async () => {
  let authoritativeSummary = summary([notification]);
  expect(selectSessionNotifications(authoritativeSummary)).toEqual([notification]);
  const dismissSessionNotification = jest.fn(async () => {
    const dismissed: SessionNotification = {
      ...notification,
      status: 'dismissed',
      revision: 2,
      updated_at: '2026-08-01T00:00:01Z',
      dismissal: { dismissed_at: '2026-08-01T00:00:01Z' },
    };
    authoritativeSummary = summary([dismissed]);
    return dismissed;
  });
  const backend = {
    kind: 'inProcess',
    getSessionSummary: jest.fn(async () => authoritativeSummary),
    dismissSessionNotification,
  } as unknown as AgentBackend;
  const renderRail = () =>
    render(
      <ThemeProvider theme={buildDesktopTheme(null)}>
        <DesktopSessionNotificationRail
          backend={backend}
          connectionId="connection-1"
          sessionId="session-1"
          sessionSummary={summary([])}
        />
      </ThemeProvider>,
    );

  const rendered = renderRail();
  expect(
    await screen.findByText('Server-owned session notification', {}, { timeout: 3000 }),
  ).toBeTruthy();
  fireEvent.press(screen.getByText('Close'));
  await waitFor(() => {
    expect(dismissSessionNotification).toHaveBeenCalledWith(
      'session-1',
      'session-notification',
      { expectedRevision: 1, reason: 'user' },
    );
    expect(screen.queryByText('Server-owned session notification')).toBeNull();
  });

  rendered.unmount();
  const reopened = renderRail();
  await waitFor(() => {
    expect(screen.queryByText('Server-owned session notification')).toBeNull();
  });
  reopened.unmount();
});

test('keeps a session notification visible when server dismissal fails', async () => {
  const backend = {
    kind: 'inProcess',
    getSessionSummary: jest.fn(async () => summary([notification])),
    dismissSessionNotification: jest.fn(async () => {
      throw new Error('server unavailable');
    }),
  } as unknown as AgentBackend;
  render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopSessionNotificationRail
        backend={backend}
        connectionId="connection-1"
        sessionId="session-1"
        sessionSummary={summary([notification])}
      />
    </ThemeProvider>,
  );

  expect(await screen.findByText('Server-owned session notification')).toBeTruthy();
  fireEvent.press(screen.getByText('Close'));
  await waitFor(() => {
    expect(backend.dismissSessionNotification).toHaveBeenCalled();
  });
  expect(screen.getByText('Server-owned session notification')).toBeTruthy();
});

test('renders action-created session events immediately with banner presentation', async () => {
  const bannerNotification: SessionNotification = {
    ...notification,
    display: {
      ...notification.display,
      presentation: 'banner',
    },
  };
  const backend = {
    kind: 'inProcess',
    getSessionSummary: jest.fn(async () => summary([])),
  } as unknown as AgentBackend;
  const rendered = render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopSessionNotificationRail
        backend={backend}
        connectionId="connection-1"
        sessionId="session-1"
        sessionSummary={summary([])}
        events={[
          {
            event_id: '1',
            type: 'session_notification_created',
            session_id: 'session-1',
            notification: bannerNotification,
          },
        ]}
      />
    </ThemeProvider>,
  );

  expect(await screen.findByText('Server-owned session notification')).toBeTruthy();
  expect(screen.UNSAFE_getByProps({ accessibilityRole: 'alert' })).toBeTruthy();
  rendered.unmount();
});