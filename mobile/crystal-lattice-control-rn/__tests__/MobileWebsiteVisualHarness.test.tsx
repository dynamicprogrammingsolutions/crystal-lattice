import React from 'react';
import { fireEvent, render, waitFor } from '@testing-library/react-native';

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