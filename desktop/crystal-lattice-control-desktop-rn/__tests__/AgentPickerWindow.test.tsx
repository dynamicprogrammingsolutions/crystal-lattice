import React from 'react';

jest.mock('../src/theme/useDesktopTheme', () => {
  const { buildDesktopTheme } = jest.requireActual(
    '../src/theme/buildDesktopTheme',
  );
  return {
    useDesktopTheme: () => buildDesktopTheme(null),
  };
});

const mockSubmitAgentPicker = jest.fn();
jest.mock('../src/windows/desktopWindowManager', () => ({
  DesktopWindowManager: {
    submitAgentPicker: (...args: any[]) => mockSubmitAgentPicker(...args),
    cancelAgentPicker: jest.fn(),
  },
}));

import { fireEvent, render } from '@testing-library/react-native';

import { AgentPickerWindow } from '../src/windows/AgentPickerWindow';

describe('AgentPickerWindow', () => {
  beforeEach(() => {
    mockSubmitAgentPicker.mockReset();
  });

  it('renders ordered descriptor copy and submits the stable id', () => {
    const screen = render(
      <AgentPickerWindow
        connectionId="connection-one"
        agents={['codex', 'claude']}
        agentDescriptors={[
          {
            id: 'claude',
            title: 'Claude',
            description: 'Claude-oriented read, edit, and bash tools.',
            order: 20,
          },
          {
            id: 'codex',
            title: 'Codex',
            description: 'Codex-oriented shell and apply patch tools.',
            order: 10,
          },
        ]}
      />,
    );

    expect(screen.getByText('Codex')).toBeTruthy();
    expect(
      screen.getByText('Codex-oriented shell and apply patch tools.'),
    ).toBeTruthy();
    expect(screen.getByText('codex')).toBeTruthy();
    expect(screen.getByText('Claude')).toBeTruthy();

    fireEvent.press(screen.getByText('Claude'));
    fireEvent.press(screen.getByText('Create'));

    expect(mockSubmitAgentPicker).toHaveBeenCalledWith({
      connectionId: 'connection-one',
      agentId: 'claude',
      mode: 'createSession',
      sessionId: undefined,
    });
  });
});