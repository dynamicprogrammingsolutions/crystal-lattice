import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import { MacTextView } from '@crystal-lattice/react-native-mac-text-view';

import DesktopMessageBubble from '../src/chat/DesktopMessageBubble';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

function renderBubble(element: React.ReactElement) {
  return render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      {element}
    </ThemeProvider>,
  );
}

test('expanded tool results use the read-only auto-growing native text view', () => {
  const screen = renderBubble(
    <DesktopMessageBubble
      index={3}
      message={{ role: 'tool', content: 'tool result\n'.repeat(40) }}
    />,
  );

  fireEvent.press(screen.getByTestId('tool-result-disclosure-3'));

  const result = screen.UNSAFE_getAllByType(MacTextView).find(
    node => node.props.testID === 'tool-result-3',
  );
  expect(result).toBeDefined();
  expect(result!.props.editable).toBe(false);
  expect(result!.props.autoGrow).toBe(true);
  expect(result!.props.initialText).toBe('tool result\n'.repeat(40));
  expect(result!.props.textContainerInset).toBe(0);
});

test('expanded reasoning uses the read-only native text view and keeps italic presentation', () => {
  const reasoning = 'reasoning detail\n'.repeat(35);
  const screen = renderBubble(
    <DesktopMessageBubble
      index={4}
      message={{
        role: 'assistant',
        content: 'answer',
        metadata: { reasoning },
      }}
    />,
  );

  fireEvent.press(screen.getByTestId('assistant-reasoning-disclosure-4'));

  const result = screen.UNSAFE_getAllByType(MacTextView).find(
    node => node.props.testID === 'assistant-reasoning-4',
  );
  expect(result).toBeDefined();
  expect(result!.props.editable).toBe(false);
  expect(result!.props.autoGrow).toBe(true);
  expect(result!.props.initialText).toBe(reasoning);
  expect(result!.props.italic).toBe(true);
});

test('expanded tool-call arguments use read-only native text views', () => {
  const screen = renderBubble(
    <DesktopMessageBubble
      index={5}
      message={{
        role: 'assistant',
        content: 'answer',
        metadata: {
          tool_calls: [
            {
              id: 'call-1',
              function: {
                name: 'lookup',
                arguments: '{"query":"selectable text"}',
              },
            },
          ],
        },
      }}
    />,
  );

  fireEvent.press(screen.getByTestId('assistant-tool-calls-disclosure-5'));

  const result = screen.UNSAFE_getAllByType(MacTextView).find(
    node => node.props.testID === 'assistant-tool-call-5-0',
  );
  expect(result).toBeDefined();
  expect(result!.props.editable).toBe(false);
  expect(result!.props.autoGrow).toBe(true);
  expect(result!.props.initialText).toBe('{"query":"selectable text"}');
});