import React from 'react';
import { fireEvent, screen } from '@testing-library/react-native';

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