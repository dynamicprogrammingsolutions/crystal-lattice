import React from 'react';
import { fireEvent, render } from '@testing-library/react-native';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import DesktopMessageBubble from '../src/chat/DesktopMessageBubble';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

function renderBubble(element: React.ReactElement) {
  return render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      {element}
    </ThemeProvider>,
  );
}

test('expanded tool results use selectable text inside the bounded scroll view', () => {
  const content = 'tool result\n'.repeat(40);
  const screen = renderBubble(
    <DesktopMessageBubble
      index={3}
      message={{ role: 'tool', content }}
    />,
  );

  fireEvent.press(screen.getByTestId('tool-result-disclosure-3'));

  expect(screen.getByTestId('tool-result-3')).toBeTruthy();
  const result = screen.getByText(content);
  expect(result.props.selectable).toBe(true);
});

test('expanded reasoning uses selectable text and keeps italic presentation', () => {
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

  expect(screen.getByTestId('assistant-reasoning-4')).toBeTruthy();
  const result = screen.getByText(reasoning);
  expect(result.props.selectable).toBe(true);
  expect(result.props.style).toEqual(
    expect.objectContaining({ fontStyle: 'italic' }),
  );
});

test('expanded tool-call arguments use selectable text', () => {
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

  const result = screen.getByTestId('assistant-tool-call-5-0');
  expect(result.props.selectable).toBe(true);
  expect(result.props.children).toBe('{"query":"selectable text"}');
});

test.each(['user', 'system', 'tool', 'assistant'])(
  '%s message footers are selectable',
  role => {
    const screen = renderBubble(
      <DesktopMessageBubble
        index={6}
        message={{
          role,
          content: role === 'tool' ? '' : 'message',
          metadata: { footer_value: `${role} footer` },
        }}
        footerElements={[
          {
            ui_type: 'message_footer',
            data: 'metadata.footer_value',
            template: '{{data}}',
          } as any,
        ]}
      />,
    );

    expect(screen.getByText(`${role} footer`).props.selectable).toBe(true);
  },
);