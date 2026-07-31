import React from 'react';
import { act, render, screen } from '@testing-library/react-native';

import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
} from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';
import {
  DesktopConnectionDisplayRail,
  DesktopGlobalDisplayLayer,
} from '../src/ui/DesktopGlobalDisplayLayer';

function createBackend(): AgentBackend {
  return {
    kind: 'inProcess',
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

test('aggregates connection displays and excludes session displays', () => {
  jest.useFakeTimers();
  const first = createBackend();
  const second = createBackend();
  const rendered = render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={{
          first: { status: 'open', baseUrl: 'http://first', backend: first as any },
          second: { status: 'open', baseUrl: 'http://second', backend: second as any },
        }}
        connectionNameById={{
          first: 'First connection',
          second: 'Second connection',
        }}
      >
        <DesktopConnectionDisplayRail />
      </DesktopGlobalDisplayLayer>
    </ThemeProvider>,
  );

  act(() => {
    emitDisplayPresentation(
      first,
      normalizeDisplayEnvelope({
        id: 'first-display',
        source: 'action_response',
        ownershipScope: 'connection',
        connectionId: 'first',
        display: {
          format: 'text',
          body: 'First application display',
          presentation: 'banner',
        },
      }),
    );
    emitDisplayPresentation(
      second,
      normalizeDisplayEnvelope({
        id: 'second-display',
        source: 'action_response',
        ownershipScope: 'connection',
        connectionId: 'second',
        display: {
          format: 'text',
          body: 'Second application display',
          presentation: 'modal',
        },
      }),
    );
    emitDisplayPresentation(
      first,
      normalizeDisplayEnvelope({
        id: 'session-display',
        source: 'session_notification',
        connectionId: 'first',
        sessionId: 'session-1',
        display: {
          format: 'text',
          body: 'Session display',
          presentation: 'banner',
        },
      }),
    );
  });

  expect(screen.getByText('First application display')).toBeTruthy();
  expect(screen.getByText('Second application display')).toBeTruthy();
  expect(screen.getByText('First connection')).toBeTruthy();
  expect(screen.getByText('Second connection')).toBeTruthy();
  expect(screen.queryByText('Session display')).toBeNull();

  rendered.unmount();
  jest.useRealTimers();
});