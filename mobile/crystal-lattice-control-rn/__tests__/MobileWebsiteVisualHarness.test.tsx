import React from 'react';
import {
  fireEvent,
  render,
  waitFor,
  within,
} from '@testing-library/react-native';

import { MobileWebsiteVisualHarness } from '../src/testing/MobileWebsiteVisualHarness';

test.each([
  ['compiled', 'Compiled system message'],
  ['cost', 'Cost report'],
] as const)(
  'renders the generated %s action fixture through the production modal',
  async (kind, title) => {
    const screen = render(
      <MobileWebsiteVisualHarness
        clcWebsiteVisualKind={kind}
        clcWebsiteVisualTheme="light"
      />,
    );

    fireEvent.press(screen.getByTestId(`website-visual-open-${kind}`));

    await waitFor(() => {
      expect(screen.getByTestId(`website-${kind}-action-display`)).toBeTruthy();
      expect(screen.getByText(title)).toBeTruthy();
    });
  },
);

test('renders the authored system template through the production transcript', async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="system-template"
      clcWebsiteVisualTheme="light"
    />,
  );

  fireEvent.press(screen.getByTestId('website-visual-open-system-template'));

  await waitFor(() => {
    expect(
      screen.getByDisplayValue(
        'You are {{AGENT_TITLE}}. Follow the project guidance below before acting.\n\n{{PROJECT_GUIDANCE}}\n\nUse the enabled {{TOOLSET_NAME}} tools and report assumptions explicitly.',
      ),
    ).toBeTruthy();
    expect(screen.getByText('[0] System')).toBeTruthy();
  });
});

test('renders the active request state through the production composer', async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="composer-active"
      clcWebsiteVisualTheme="light"
    />,
  );

  fireEvent.press(screen.getByTestId('website-visual-open-composer-active'));

  await waitFor(() => {
    expect(screen.getByTestId('composer-send-progress')).toBeTruthy();
    expect(
      screen.getByDisplayValue(
        'Append a validation note while the current request finishes.',
      ),
    ).toBeTruthy();
  });
});

test('renders the Starlette message actions through the production action menu', async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="message-actions"
      clcWebsiteVisualTheme="light"
    />,
  );

  fireEvent.press(screen.getByTestId('website-visual-open-message-actions'));

  const terminalMessage = await waitFor(() =>
    screen.getByTestId('message-bubble-6'),
  );
  const terminalMessageActions =
    within(terminalMessage).getByTestId('message-actions-menu');
  fireEvent.press(terminalMessageActions);

  await waitFor(() => {
    expect(screen.getByText('Message actions')).toBeTruthy();
    expect(screen.getByText('Fork here')).toBeTruthy();
    expect(screen.getByText('Copy message')).toBeTruthy();
  });
});

test('renders deterministic request states in the workspace candidate', async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="workspaces"
      clcWebsiteVisualTheme="light"
    />,
  );

  await waitFor(() => {
    expect(
      screen.getByTestId('session-request-status-starlette-compatibility'),
    ).toBeTruthy();
    expect(screen.getByText('Plan a Starlette compatibility fix')).toBeTruthy();
    expect(screen.getByText('In progress')).toBeTruthy();
    expect(screen.getByText('Not started')).toBeTruthy();
    expect(screen.getByText('Completed')).toBeTruthy();
  });
});

test('renders a local Watchlist and recent-session workspace', async () => {
  const screen = render(
    <MobileWebsiteVisualHarness
      clcWebsiteVisualKind="home"
      clcWebsiteVisualTheme="light"
    />,
  );

  await waitFor(() => {
    expect(
      screen.getByTestId(
        'home-watchlist-tile-local-workspace-starlette-compatibility',
      ),
    ).toBeTruthy();
    expect(screen.getByText('Recent Sessions')).toBeTruthy();
  });
});