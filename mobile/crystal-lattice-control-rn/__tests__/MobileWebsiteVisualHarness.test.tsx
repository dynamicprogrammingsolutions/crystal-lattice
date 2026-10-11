import React from 'react';
import { fireEvent, render, waitFor } from '@testing-library/react-native';
import * as sharedComponents from '@crystal-lattice/frontend-rn-components';
import Icon from 'react-native-vector-icons/Feather';

import { MobileWebsiteVisualHarness } from '../src/testing/MobileWebsiteVisualHarness';

test('the Vibe illustration renders a first System message, user request, and initial reasoning', async () => {
  const screen = render(
    <MobileWebsiteVisualHarness clcWebsiteVisualKind="vibe" clcWebsiteVisualTheme="light" />,
  );
  fireEvent.press(screen.getByTestId('website-visual-open-vibe'));
  expect(await screen.findByText('[0] System')).toBeTruthy();
  expect(screen.getByTestId('message-bubble-1')).toBeTruthy();
  fireEvent.press(screen.getByTestId('assistant-reasoning-disclosure-2'));
  expect(await screen.findByTestId('assistant-reasoning-content-2')).toBeTruthy();
});

test('the refreshed runtime fixture reaches the real session menu with its supported title icon', async () => {
  // The suite default stubs this whole bar. Use its actual public consumer
  // for this fixture regression, retaining the suite's native-package mocks.
  const bar = jest.spyOn(sharedComponents, 'SessionActionsBar').mockImplementation(
    jest.requireActual('@crystal-lattice/frontend-rn-components').SessionActionsBar,
  );
  try {
    const screen = render(
      <MobileWebsiteVisualHarness
        clcWebsiteVisualKind="actions"
        clcWebsiteVisualTheme="light"
      />,
    );
    fireEvent.press(screen.getByTestId('website-visual-open-actions'));
    fireEvent.press(await screen.findByTestId('session-actions-menu'));
    const action = await screen.findByTestId('actions-menu-action-generate_title_from_view');
    expect(screen.getByText('Generate title')).toBeTruthy();
    expect(action.findAll(node => node.type === Icon && node.props.name === 'zap')).toHaveLength(1);
  } finally {
    bar.mockRestore();
  }
});

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