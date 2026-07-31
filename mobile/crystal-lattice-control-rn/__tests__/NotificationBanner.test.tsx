import React from 'react';
import { fireEvent, screen } from '@testing-library/react-native';

import {
  NotificationBanner,
  NotificationBannerHost,
} from '@crystal-lattice/frontend-rn-components';

import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

test.each(['info', 'success', 'warning', 'error'] as const)(
  'renders the shared %s notification banner',
  (variant) => {
    renderWithMobileProviders(
      <NotificationBanner
        display={{
          format: 'text',
          title: `${variant} title`,
          body: `${variant} body`,
          variant,
        }}
      />,
    );
    expect(screen.getByText(`${variant} title`)).toBeTruthy();
    expect(screen.getByText(`${variant} body`)).toBeTruthy();
  },
);

test('executes banner actions and local dismissal', () => {
  const onAction = jest.fn();
  const onDismiss = jest.fn();
  renderWithMobileProviders(
    <NotificationBanner
      display={{
        format: 'text',
        body: 'Body',
        actions: [{ kind: 'copy_text', id: 'copy', label: 'Copy', text: 'Body' }],
      }}
      onFollowupAction={onAction}
      onDismiss={onDismiss}
    />,
  );

  fireEvent.press(screen.getByLabelText('Copy'));
  fireEvent.press(screen.getByLabelText('Dismiss notification'));
  expect(onAction).toHaveBeenCalledTimes(1);
  expect(onDismiss).toHaveBeenCalledTimes(1);
});

test('bounds the global banner stack to three items', () => {
  const items = [1, 2, 3, 4].map((id) => ({
    envelope: {
      id: String(id),
      source: 'action_response' as const,
      display: {
        format: 'text' as const,
        body: `Body ${id}`,
        presentation: 'banner' as const,
      },
    },
  }));
  renderWithMobileProviders(
    <NotificationBannerHost items={items} onDismiss={() => {}} />,
  );
  expect(screen.queryByText('Body 1')).toBeNull();
  expect(screen.getByText('Body 4')).toBeTruthy();
});