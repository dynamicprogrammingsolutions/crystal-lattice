import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import MessageBubble from '../src/components/MessageBubble';
import { ThemeProvider, lightTheme } from '../src/theme';


jest.mock('../src/theme', () => {
  const actual = jest.requireActual('../src/theme');
  return {
    ...actual,
    ThemeProvider: ({ children }: any) => <>{children}</>,
    useTheme: () => actual.lightTheme,
  };
});


function renderMessageBubble(message: any) {
  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ThemeProvider theme={lightTheme}>
        <MessageBubble
          index={0}
          message={message}
        />
      </ThemeProvider>
    );
  });
  return renderer!;
}


test('system message hides compiled content panel when metadata is absent', () => {
  const renderer = renderMessageBubble({
    role: 'system',
    content: 'Template content',
    metadata: {},
  });

  const toggleButtons = renderer.root.findAllByProps({ testID: 'system-compiled-toggle' });
  const compiledContent = renderer.root.findAllByProps({ testID: 'system-compiled-content' });

  expect(toggleButtons).toHaveLength(0);
  expect(compiledContent).toHaveLength(0);
});


test('system message shows collapsible compiled content when metadata is present', () => {
  const renderer = renderMessageBubble({
    role: 'system',
    content: 'Template {{NAME}}',
    metadata: { compiled_content: 'Template Alice' },
  });

  const toggle = renderer.root.findByProps({ testID: 'system-compiled-toggle' });
  const hiddenHint = renderer.root.findAll((node) => {
    return node.props?.children === 'Compiled system prompt hidden (tap chevron to expand).';
  });
  expect(hiddenHint.length).toBeGreaterThan(0);

  ReactTestRenderer.act(() => {
    toggle.props.onPress();
  });

  const compiledContent = renderer.root.findByProps({ testID: 'system-compiled-content' });
  expect(compiledContent.props.children).toBe('Template Alice');
});