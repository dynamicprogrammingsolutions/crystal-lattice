import React from 'react';
import { render } from '@testing-library/react-native';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import DesktopMessageBubble from '../src/chat/DesktopMessageBubble';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

test('raw assistant text uses normal selectable paragraph layout', () => {
  const content = 'long raw answer\n'.repeat(40);
  const screen = render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopMessageBubble
        index={1}
        message={{ role: 'assistant', content }}
        renderMode="raw"
      />
    </ThemeProvider>,
  );

  expect(screen.getByTestId('assistant-raw-message-1')).toBeTruthy();
  const text = screen.getByText(content);
  expect(text.props.selectable).toBe(true);
});