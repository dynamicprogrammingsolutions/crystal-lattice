import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import DebugEventsView from '../src/components/DebugEventsView';
import { ThemeProvider, lightTheme } from '../src/theme';

jest.mock('../src/theme', () => {
  const actual = jest.requireActual('../src/theme');
  return {
    ...actual,
    ThemeProvider: ({ children }: any) => <>{children}</>,
    useTheme: () => actual.lightTheme,
  };
});

test('DebugEventsView renders mobile timeline notes alongside streamed events', () => {
  let renderer: ReactTestRenderer.ReactTestRenderer;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ThemeProvider theme={lightTheme}>
        <DebugEventsView
          notes={[
            {
              id: 'note-1',
              scope: 'chat',
              title: 'Resume recovery started',
              detail: 'app_foreground',
              meta: { sessionId: 's1' },
              timestampMs: Date.UTC(2026, 3, 8, 10, 11, 12),
            },
          ]}
          events={[
            {
              event_id: '1',
              type: 'request_started',
              session_id: 's1',
              request_id: 'req-1',
            } as any,
          ]}
          onClose={() => {}}
        />
      </ThemeProvider>,
    );
  });

  expect(
    renderer!.root.findAll((node) => node.props?.children === 'Mobile timeline'),
  ).not.toHaveLength(0);
  expect(
    renderer!.root.findAll((node) => node.props?.children === 'Streamed events'),
  ).not.toHaveLength(0);
  expect(
    renderer!.root.findAll((node) => node.props?.children === 'Tap a mobile timeline entry or streamed event to inspect its JSON payload.'),
  ).not.toHaveLength(0);
});