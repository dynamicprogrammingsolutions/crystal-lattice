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
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

import { AgentPickerWindow } from '../src/windows/AgentPickerWindow';
import { clearActiveAgentPickerWindow } from '../src/windows/agentPickerCoordinator';

describe('AgentPickerWindow', () => {
  beforeEach(() => {
    mockSubmitAgentPicker.mockReset();
    clearActiveAgentPickerWindow();
  });

  it('renders ordered descriptors, effective defaults, and submits the stable id', async () => {
    const listAgentPlugins = jest.fn(async (agentId: string) =>
      agentId === 'claude'
        ? [
            {
              id: 'claude_read_tool',
              kind: 'tools',
              enabled: true,
              active: true,
              source: 'agent',
            },
          ]
        : [
            {
              id: 'openai_responses',
              kind: 'providers',
              enabled: true,
              active: true,
              source: 'agent',
            },
            {
              id: 'apply_patch',
              kind: 'tools',
              enabled: true,
              active: true,
              source: 'agent',
            },
          ],
    );
    const backend = {
      listAgentPlugins,
    } as unknown as AgentBackend;
    const screen = render(
      <AgentPickerWindow
        connectionId="connection-one"
        backend={backend}
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

    expect(screen.getByTestId('agent-picker-row-codex')).toBeTruthy();
    expect(screen.getByTestId('agent-picker-row-claude')).toBeTruthy();
    expect(await screen.findByText('Apply Patch')).toBeTruthy();
    expect(screen.getByTestId('agent-plugin-group-providers')).toBeTruthy();
    expect(screen.getByTestId('agent-plugin-group-extensions')).toBeTruthy();
    expect(screen.getByTestId('agent-plugin-group-features')).toBeTruthy();
    expect(screen.getByTestId('agent-plugin-group-tools')).toBeTruthy();

    fireEvent.press(screen.getByTestId('agent-picker-row-claude'));
    expect(await screen.findByText('Claude Read Tool')).toBeTruthy();
    fireEvent.press(screen.getByText('Create'));

    expect(listAgentPlugins).toHaveBeenNthCalledWith(1, 'codex');
    expect(listAgentPlugins).toHaveBeenNthCalledWith(2, 'claude');
    expect(mockSubmitAgentPicker).toHaveBeenCalledWith({
      connectionId: 'connection-one',
      agentId: 'claude',
      mode: 'createSession',
      sessionId: undefined,
    });
  });

  it('keeps selection usable when the preview contract is unavailable', async () => {
    const screen = render(
      <AgentPickerWindow
        connectionId="legacy-connection"
        agents={['legacy-agent']}
      />,
    );

    expect(await screen.findByText('Plugin preview unavailable')).toBeTruthy();
    fireEvent.press(screen.getByText('Create'));
    expect(mockSubmitAgentPicker).toHaveBeenCalledWith({
      connectionId: 'legacy-connection',
      agentId: 'legacy-agent',
      mode: 'createSession',
      sessionId: undefined,
    });
  });
});