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
      const fieldName = inputs[0]?.name || 'unknown';
      const submittedValues =
        fieldName === 'status'
          ? { ...values, status: 'blocked' }
          : { ...values, title: 'Updated through SessionsScreen' };
      return ReactModule.createElement(
        View,
        { testID: 'real-application-action-dialog' },
        ReactModule.createElement(
          Text,
          { testID: `real-dialog-prefill-${fieldName}` },
          values[fieldName],
        ),
        ReactModule.createElement(
          TouchableOpacity,
          {
            testID: `real-dialog-submit-${fieldName}`,
            onPress: () => onSubmit(submittedValues),
          },
          ReactModule.createElement(Text, null, `Submit ${fieldName}`),
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
    'path:${env:REPO_ROOT}/plugins/session-main-search-app',
    'path:${env:REPO_ROOT}/plugins/session-pinned-app',
    'path:${env:REPO_ROOT}/plugins/session-status-app',
    'path:${env:REPO_ROOT}/plugins/session-ordering-buckets-app',
  ],
  agents: {
    default: {
      provider: 'echo',
    },
  },
  application: {
    session_pinned_metadata_key: 'favorite',
  },
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
    const otherSessionId = await createMobileComponentSession(started.backend);
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
    await started.backend.appendMessage(otherSessionId, {
      role: 'user',
      content: 'other backend preview',
    });
    const pinResult = await started.backend.executeSessionAction!({
      sessionId,
      pluginId: 'session_pinned',
      actionId: 'toggle_session_pinned',
      actionOwner: 'application',
      inputs: {
        session_id: sessionId,
      },
    });
    expect(pinResult.status).toBe('ok');
    await started.backend.appendMessage(otherSessionId, {
      role: 'user',
      content: 'newer unpinned update',
    });

    const summaries = await started.backend.listSessions();
    const summary = summaries.find((item) => item.session_id === sessionId);
    const otherSummary = summaries.find(
      (item) => item.session_id === otherSessionId,
    );
    expect(summary).toBeTruthy();
    expect(otherSummary).toBeTruthy();
    expect(summaries.map((item) => item.session_id)).toEqual([
      sessionId,
      otherSessionId,
    ]);
    expect(summary).toEqual(
      expect.objectContaining({
        metadata: expect.objectContaining({ favorite: true }),
        pinned_rank: 0,
      }),
    );
    expect(summary).not.toHaveProperty('pinned');
    expect(otherSummary).toEqual(
      expect.objectContaining({
        pinned_rank: 1,
      }),
    );
    expect(summary!.presentation).toEqual({
      title: 'Real backend title',
      subtitle: 'Real backend subtitle',
      meta: '1 messages',
    });
    await expect(started.backend.getSessionSummary(sessionId)).resolves.toEqual(
      summary,
    );
    const applicationUi = await started.backend.listApplicationUiSchema();
    expect(applicationUi).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          plugin: 'session_main_search',
          ui_type: 'session_list_filter',
          id: 'session_search',
          main_search: true,
        }),
        expect.objectContaining({
          plugin: 'session_pinned',
          ui_type: 'session_list_toggle_pinned',
          id: 'toggle_session_pinned_star',
          data: 'metadata.favorite',
          missing_value: false,
        }),
        expect.objectContaining({
          plugin: 'session_pinned',
          ui_type: 'session_list_filter',
          id: 'pinned_state',
          data: 'metadata.favorite',
          default: null,
        }),
        expect.objectContaining({
          plugin: 'session_status',
          ui_type: 'session_list_filter',
          id: 'session_status',
          multiple: true,
          missing_value: 'todo',
        }),
      ]),
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
    expect(
      (await screen.findByTestId(`session-pin-toggle-${sessionId}`)).props
        .accessibilityState.selected,
    ).toBe(true);
    expect(screen.getByTestId(`session-pin-icon-${sessionId}`).props.color).toBe(
      '#FFCC00',
    );
    expect(
      screen.getByTestId(`session-pin-toggle-${otherSessionId}`).props
        .accessibilityState.selected,
    ).toBe(false);
    expect(screen.queryByText('real backend preview')).toBeNull();

    await waitFor(() => {
      expect(
        screen.getAllByTestId('real-session-action-edit_title_from_list'),
      ).toHaveLength(2);
    });
    fireEvent.changeText(
      await screen.findByTestId('session-main-search'),
      'Real backend title',
    );
    expect(screen.getByTestId(`session-row-${sessionId}`)).toBeTruthy();
    expect(screen.queryByTestId(`session-row-${otherSessionId}`)).toBeNull();

    fireEvent.press(
      await screen.findByTestId(
        'real-session-action-edit_title_from_list',
      ),
    );
    expect(await screen.findByTestId('real-application-action-dialog')).toBeTruthy();
    expect(screen.getByTestId('real-dialog-prefill-title')).toHaveTextContent(
      'Real backend title',
    );
    fireEvent.changeText(screen.getByTestId('session-main-search'), '');
    fireEvent.press(screen.getByTestId('real-dialog-submit-title'));

    await waitFor(async () => {
      const updated = await started!.backend.getSessionSummary(sessionId);
      expect(updated.presentation.title).toBe('Updated through SessionsScreen');
    });
    expect(
      await screen.findByText('Updated through SessionsScreen'),
    ).toBeTruthy();

    fireEvent.press(
      screen.getAllByTestId('real-session-action-set_session_status')[0],
    );
    expect(await screen.findByTestId('real-application-action-dialog')).toBeTruthy();
    expect(screen.getByTestId('real-dialog-prefill-status')).toHaveTextContent(
      'todo',
    );
    fireEvent.press(screen.getByTestId('real-dialog-submit-status'));

    await waitFor(async () => {
      const updated = await started!.backend.getSessionSummary(sessionId);
      expect(updated.metadata.status).toBe('blocked');
    });

    fireEvent.press(await screen.findByTestId('session-filters-open'));
    fireEvent.press(
      await screen.findByTestId('session-filter-pinned_state-option-true'),
    );
    expect(screen.getByTestId(`session-row-${sessionId}`)).toBeTruthy();
    expect(screen.queryByTestId(`session-row-${otherSessionId}`)).toBeNull();
    fireEvent.press(
      screen.getByTestId('session-filter-session_status-option-2'),
    );
    expect(screen.getByTestId('session-filters-active-count')).toHaveTextContent(
      '2',
    );
    fireEvent.press(screen.getByTestId('session-filters-show-all'));
    expect(screen.getByTestId(`session-row-${sessionId}`)).toBeTruthy();
    expect(screen.getByTestId(`session-row-${otherSessionId}`)).toBeTruthy();
  }, 60000);
});
