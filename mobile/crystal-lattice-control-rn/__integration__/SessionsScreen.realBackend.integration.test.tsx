import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';

jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-rn-components');
  const ReactModule = require('react');
  const { Text, TouchableOpacity, View } = require('react-native');
  const {
    buildActionDialogInitialValues,
  } = require('@crystal-lattice/frontend-sdk');

  return {
    __esModule: true,
    ...actual,
    SessionActionsBar: ({ extraActions, onAction }: any) =>
      ReactModule.createElement(
        View,
        null,
        (extraActions || []).map((action: any) =>
          ReactModule.createElement(
            TouchableOpacity,
            {
              key: action.key,
              testID: `real-session-action-${action.key}`,
              onPress: () => onAction(action.key),
            },
            ReactModule.createElement(Text, null, action.label),
          ),
        ),
      ),
    ApplicationActionDialog: ({
      visible,
      dialog,
      prefillContext,
      onSubmit,
    }: any) => {
      if (!visible) {
        return null;
      }
      const inputs = dialog?.kind === 'form' && Array.isArray(dialog.inputs)
        ? dialog.inputs
        : [];
      const values = buildActionDialogInitialValues(inputs, prefillContext);
      return ReactModule.createElement(
        View,
        { testID: 'real-application-action-dialog' },
        ReactModule.createElement(
          Text,
          { testID: 'real-dialog-prefill-title' },
          values.title,
        ),
        ReactModule.createElement(
          TouchableOpacity,
          {
            testID: 'real-dialog-submit',
            onPress: () =>
              onSubmit({
                ...values,
                title: 'Updated through SessionsScreen',
              }),
          },
          ReactModule.createElement(Text, null, 'Submit title'),
        ),
      );
    },
  };
});

import { ApplicationPluginsProvider } from '../src/ApplicationPluginsContext';
import { PinnedActionsProvider } from '../src/PinnedActionsContext';
import SessionsScreen from '../src/SessionsScreen';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import {
  createMobileComponentSession,
  startMobileComponentBackend,
  type StartedMobileComponentBackend,
} from './support/mobileComponentBackend';

const SERVER_CONFIG = {
  providers: {
    echo: {
      provider: 'echo_openai_like',
      model: 'test-model',
    },
  },
  plugins: [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'path:${env:REPO_ROOT}/plugins/session-title-app',
    'path:${env:REPO_ROOT}/plugins/session-message-count-meta-app',
  ],
  agents: {
    default: {
      provider: 'echo',
    },
  },
  application: {},
};

describe('SessionsScreen real-backend component integration', () => {
  let started: StartedMobileComponentBackend | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('renders application-derived summaries received through the HTTP backend', async () => {
    started = await startMobileComponentBackend({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const sessionId = await createMobileComponentSession(started.backend);
    await started.backend.appendMessage(sessionId, {
      role: 'user',
      content: 'real backend preview',
    });
    const titleResult = await started.backend.executeSessionAction!({
      sessionId,
      pluginId: 'session_title',
      actionId: 'set_session_title',
      actionOwner: 'application',
      inputs: {
        session_id: sessionId,
        title: 'Real backend title',
        subtitle: 'Real backend subtitle',
      },
    });
    expect(titleResult.status).toBe('ok');

    const summaries = await started.backend.listSessions();
    const summary = summaries.find((item) => item.session_id === sessionId);
    expect(summary).toBeTruthy();
    expect(summary!.presentation).toEqual({
      title: 'Real backend title',
      subtitle: 'Real backend subtitle',
      meta: '1 messages',
    });
    await expect(started.backend.getSessionSummary(sessionId)).resolves.toEqual(
      summary,
    );

    renderWithMobileProviders(
      <PinnedActionsProvider>
        <ApplicationPluginsProvider
          backend={started.backend}
          connectionId="real-backend-session-list"
        >
          <SessionsScreen
            backend={started.backend}
            connectionId="real-backend-session-list"
            cachedSessions={summaries}
            lastLoadedAt={Date.now()}
            isActive={false}
            onUpdateCache={jest.fn()}
            onSelectSession={jest.fn()}
          />
        </ApplicationPluginsProvider>
      </PinnedActionsProvider>,
    );

    expect(
      await screen.findByTestId(`session-title-${sessionId}`),
    ).toHaveTextContent('Real backend title');
    expect(
      screen.getByTestId(`session-subtitle-${sessionId}`),
    ).toHaveTextContent('Real backend subtitle');
    expect(screen.getByTestId(`session-meta-${sessionId}`)).toHaveTextContent(
      '1 messages',
    );
    expect(screen.queryByText('real backend preview')).toBeNull();

    fireEvent.press(
      await screen.findByTestId(
        'real-session-action-edit_title_from_list',
      ),
    );
    expect(await screen.findByTestId('real-application-action-dialog')).toBeTruthy();
    expect(screen.getByTestId('real-dialog-prefill-title')).toHaveTextContent(
      'Real backend title',
    );
    fireEvent.press(screen.getByTestId('real-dialog-submit'));

    await waitFor(async () => {
      const updated = await started!.backend.getSessionSummary(sessionId);
      expect(updated.presentation.title).toBe('Updated through SessionsScreen');
    });
    expect(
      await screen.findByText('Updated through SessionsScreen'),
    ).toBeTruthy();
  }, 60000);
});
