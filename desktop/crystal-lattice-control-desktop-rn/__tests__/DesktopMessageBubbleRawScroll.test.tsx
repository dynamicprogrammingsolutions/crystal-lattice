import React from 'react';
import { render } from '@testing-library/react-native';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import { MacTextView } from '@crystal-lattice/react-native-mac-text-view';

import DesktopMessageBubble from '../src/chat/DesktopMessageBubble';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

test('raw assistant text stays read-only and cannot scroll inside the transcript', () => {
  const screen = render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopMessageBubble
        index={1}
        message={{ role: 'assistant', content: 'long raw answer\n'.repeat(40) }}
        renderMode="raw"
      />
    </ThemeProvider>,
  );

  const input = screen.UNSAFE_getByType(MacTextView);
  expect(input.props.editable).toBe(false);
  expect(input.props.autoGrow).toBe(true);
  expect(input.props.initialText).toBe('long raw answer\n'.repeat(40));
  expect(input.props.fontFamily).toBe('Menlo');
  expect(input.props.textContainerInset).toBe(0);
});