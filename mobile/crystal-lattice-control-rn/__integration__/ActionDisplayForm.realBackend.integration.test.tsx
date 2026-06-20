import React, { useState } from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';

import {
  runApplicationAction,
  type ActionDisplayFollowupAction,
  type ActionDisplayPayload,
  type ActionDisplayRunActionAction,
  type ActionUiElement,
  type ApplicationActionDefinition,
} from '@crystal-lattice/frontend-sdk';

import ActionDisplayCard from '../src/components/ActionDisplayCard';
import { useMobileApplicationActionDialogFieldRenderers } from '../src/components/applicationActionDialogRenderers';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import {
  createMobileComponentSession,
  startMobileComponentBackend,
  type StartedMobileComponentBackend,
} from './support/mobileComponentBackend';

const SERVER_CONFIG = {
  providers: {
    echo: { provider: 'echo_openai_like', model: 'test-model' },
  },
  plugins: [
    'plugins.echo_openai_like_provider.EchoOpenAILikeProvider',
    'path:${env:REPO_ROOT}/plugins/dummy-action-display-form-app',
  ],
  agents: {
    default: { provider: 'echo' },
  },
  application: {},
};

function indexActions(actions: ApplicationActionDefinition[]): Record<string, ApplicationActionDefinition> {
  const indexed: Record<string, ApplicationActionDefinition> = {};
  for (const action of actions) {
    indexed[action.id] = action;
  }
  return indexed;
}

function DisplayHarness({
  started,
  sessionId,
  actionsById,
  initialDisplay,
}: {
  started: StartedMobileComponentBackend;
  sessionId: string;
  actionsById: Record<string, ApplicationActionDefinition>;
  initialDisplay: ActionDisplayPayload;
}) {
  const [display, setDisplay] = useState(initialDisplay);
  const fieldRenderers = useMobileApplicationActionDialogFieldRenderers();

  const handleFollowupAction = async (
    action: ActionDisplayFollowupAction,
    formValues?: Record<string, any>,
  ) => {
    if (action.kind !== 'run_action') {
      return;
    }
    const runAction = action as ActionDisplayRunActionAction;
    const result = await runApplicationAction({
      backend: started.backend,
      element: {
        ui_type: 'action_result_followup',
        plugin: runAction.plugin,
        id: runAction.id,
        label: runAction.label,
        action_id: runAction.action_id,
        action_owner: runAction.action_owner,
        fixed_params: runAction.fixed_params,
        param_map: runAction.param_map,
        form: display.form,
      } as ActionUiElement,
      actionsById,
      context: {
        sessionId,
        formValues,
      },
    });
    if (result.display) {
      setDisplay(result.display);
    }
  };

  return (
    <ActionDisplayCard
      display={display}
      fieldRenderers={fieldRenderers}
      onFollowupAction={handleFollowupAction}
    />
  );
}

describe('ActionDisplayCard real-backend component integration', () => {
  let started: StartedMobileComponentBackend | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('submits an embedded display form to a real backend action', async () => {
    started = await startMobileComponentBackend({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const sessionId = await createMobileComponentSession(started.backend);
    const actionsById = indexActions(await started.backend.listApplicationActions());
    const uiSchema = await started.backend.getSessionApplicationUiSchema(sessionId, {
      pluginId: 'dummy_action_display_form_app',
    });
    const showElement = uiSchema.find(
      (element: any) => element.id === 'dummy_show_display_form',
    ) as ActionUiElement | undefined;

    expect(showElement).toBeTruthy();

    const shown = await runApplicationAction({
      backend: started.backend,
      element: showElement!,
      actionsById,
      context: { sessionId },
    });

    expect(shown.display).toBeTruthy();

    renderWithMobileProviders(
      <DisplayHarness
        started={started}
        sessionId={sessionId}
        actionsById={actionsById}
        initialDisplay={shown.display!}
      />,
    );

    fireEvent.changeText(
      screen.getByPlaceholderText('https://example.test/callback?code=abc&state=xyz'),
      'https://example.test/callback?code=abc&state=xyz',
    );
    fireEvent.changeText(screen.getByPlaceholderText('Optional note'), 'mobile integration');
    fireEvent.press(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Dummy Form Submitted')).toBeTruthy();
    });
  }, 60000);
});