import React from 'react';
import {
  act,
  fireEvent,
  screen,
  waitFor,
} from '@testing-library/react-native';

import {
  SessionNotificationsHost,
} from '@crystal-lattice/frontend-rn-components';
import type { SessionNotification } from '@crystal-lattice/frontend-sdk';

import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import { ThemeProvider, lightTheme } from '../src/theme';

const notification: SessionNotification = {
  id: 'notification-1',
  key: 'dummy:session',
  kind: 'notification',
  status: 'pending',
  revision: 1,
  severity: 'warning',
  title: 'Session notification',
  body: 'Persistent body',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  source: { plugin: 'dummy' },
  display: {
    format: 'text',
    title: 'Session notification',
    body: 'Persistent body',
    presentation: 'inline',
    actions: [
      {
        kind: 'run_action',
        id: 'followup',
        label: 'Run follow-up',
        plugin: 'dummy',
        action_id: 'followup',
      },
    ],
  },
  model_visibility: 'hidden',
};

test('renders persistent inline session notifications and follow-up actions', () => {
  const onFollowupAction = jest.fn();
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [notification] } },
      }}
      onBanner={() => {}}
      onModal={() => {}}
      onFollowupAction={onFollowupAction}
    />,
  );

  expect(screen.getByText('Session notification')).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Run follow-up'));
  expect(onFollowupAction).toHaveBeenCalledWith(
    notification.display.actions?.[0],
    notification,
  );
});

test('routes banner and modal notifications without rendering them inline', () => {
  const onBanner = jest.fn();
  const onModal = jest.fn();
  const banner = {
    ...notification,
    id: 'banner',
    display: { ...notification.display, presentation: 'banner' as const },
  };
  const modal = {
    ...notification,
    id: 'modal',
    display: { ...notification.display, presentation: 'modal' as const },
  };
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [banner, modal] } },
      }}
      onBanner={onBanner}
      onModal={onModal}
    />,
  );

  expect(onBanner).toHaveBeenCalledWith(banner);
  expect(onModal).toHaveBeenCalledWith(modal);
  expect(screen.queryByText('Persistent body')).toBeNull();
});

test('can render every presentation inline for desktop-style hosts', () => {
  const onBanner = jest.fn();
  const banner = {
    ...notification,
    id: 'banner-inline-fallback',
    display: { ...notification.display, presentation: 'banner' as const },
  };
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [banner] } },
      }}
      inlinePresentations={['inline', 'banner', 'modal']}
      onBanner={onBanner}
    />,
  );

  expect(screen.getByText('Persistent body')).toBeTruthy();
  expect(onBanner).not.toHaveBeenCalled();
});

test('shows an updated revision after the previous revision was dismissed', () => {
  const summary = {
    session_id: 'session-1',
    modified: 0,
    preview: '',
    metadata: { notifications: { items: [notification] } },
  };
  const rendered = renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={summary}
      onBanner={() => {}}
      onModal={() => {}}
    />,
  );

  fireEvent.press(screen.getByLabelText('Dismiss notification'));
  expect(screen.queryByText('Persistent body')).toBeNull();

  const updated = {
    ...notification,
    body: 'Updated persistent body',
    revision: 2,
    updated_at: '2026-01-01T00:00:01Z',
    display: {
      ...notification.display,
      body: 'Updated persistent body',
    },
  };
  rendered.rerender(
    <ThemeProvider theme={lightTheme}>
      <SessionNotificationsHost
        sessionSummary={{
          ...summary,
          metadata: { notifications: { items: [updated] } },
        }}
        onBanner={() => {}}
        onModal={() => {}}
      />
    </ThemeProvider>,
  );

  expect(screen.getByText('Updated persistent body')).toBeTruthy();
});

test('suppresses an inline notification only after server dismissal succeeds', async () => {
  const onDismissNotification = jest.fn(async () => {});
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [notification] } },
      }}
      onDismissNotification={onDismissNotification}
    />,
  );

  await act(async () => {
    fireEvent.press(screen.getByLabelText('Dismiss notification'));
  });
  await waitFor(() => {
    expect(onDismissNotification).toHaveBeenCalledWith(notification);
    expect(screen.queryByText('Persistent body')).toBeNull();
  });
});

test('keeps an inline notification visible when server dismissal fails', async () => {
  const onDismissNotification = jest.fn(async () => {
    throw new Error('server unavailable');
  });
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [notification] } },
      }}
      onDismissNotification={onDismissNotification}
    />,
  );

  await act(async () => {
    fireEvent.press(screen.getByLabelText('Dismiss notification'));
  });
  await waitFor(() => {
    expect(onDismissNotification).toHaveBeenCalledWith(notification);
  });
  expect(screen.getByText('Persistent body')).toBeTruthy();
});

test('keeps an optimistic inline dismissal hidden when synchronization fails', async () => {
  const onDismissNotification = jest.fn(async () => {
    throw new Error('server unavailable');
  });
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [notification] } },
      }}
      optimisticDismiss
      onDismissNotification={onDismissNotification}
    />,
  );

  fireEvent.press(screen.getByLabelText('Dismiss notification'));
  expect(screen.queryByText('Persistent body')).toBeNull();
  await waitFor(() => {
    expect(onDismissNotification).toHaveBeenCalledWith(notification);
  });
  expect(screen.queryByText('Persistent body')).toBeNull();
});

test('suppresses a revision provided by a persistent dismissal cache', () => {
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [notification] } },
      }}
      suppressedRevisionKeys={['notification-1:1']}
    />,
  );

  expect(screen.queryByText('Persistent body')).toBeNull();
});

test('does not resurrect a terminal session record from an older event', () => {
  const dismissed = {
    ...notification,
    status: 'dismissed' as const,
    revision: 2,
    updated_at: '2026-01-01T00:00:01Z',
    dismissal: { dismissed_at: '2026-01-01T00:00:01Z' },
  };
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [dismissed] } },
      }}
      events={[
        {
          event_id: 'event-1',
          type: 'session_notification_created',
          session_id: 'session-1',
          notification,
        },
      ]}
    />,
  );

  expect(screen.queryByText('Persistent body')).toBeNull();
});

test('does not force an already-open host to apply a remote dismissal event', () => {
  const dismissed = {
    ...notification,
    status: 'dismissed' as const,
    revision: 2,
    updated_at: '2026-01-01T00:00:01Z',
    dismissal: { dismissed_at: '2026-01-01T00:00:01Z' },
  };
  renderWithMobileProviders(
    <SessionNotificationsHost
      sessionSummary={{
        session_id: 'session-1',
        modified: 0,
        preview: '',
        metadata: { notifications: { items: [notification] } },
      }}
      events={[
        {
          event_id: 'event-2',
          type: 'session_notification_dismissed',
          session_id: 'session-1',
          notification: dismissed,
        },
      ]}
    />,
  );

  expect(screen.getByText('Persistent body')).toBeTruthy();
});