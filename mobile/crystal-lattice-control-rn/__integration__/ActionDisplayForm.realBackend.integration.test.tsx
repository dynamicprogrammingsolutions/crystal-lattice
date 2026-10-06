import React, { useState } from 'react';
import { act, fireEvent, screen, waitFor } from '@testing-library/react-native';

import {
  runApplicationAction,
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type ActionDisplayFollowupAction,
  type ActionDisplayPayload,
  type ActionDisplayRunActionAction,
  type ActionUiElement,
  type ApplicationActionDefinition,
} from '@crystal-lattice/frontend-sdk';

jest.mock('@crystal-lattice/frontend-rn-components', () => ({
  ...jest.requireActual('@crystal-lattice/frontend-rn-components'),
}));

import ActionDisplayCard from '../src/components/ActionDisplayCard';
import { ApplicationPluginsProvider } from '../src/ApplicationPluginsContext';
import GlobalDisplayLayer, { MobileDisplayHost } from '../src/components/GlobalDisplayLayer';
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

  it('opens and submits a neutral follow-up dialog through production hosts and HTTP', async () => {
    started = await startMobileComponentBackend({ config: SERVER_CONFIG, startupTimeoutMs: 30000 });
    const sessionId = await createMobileComponentSession(started.backend);
    const schema = await started.backend.getSessionApplicationUiSchema(sessionId, {
      pluginId: 'dummy_action_display_form_app',
    });
    const shown = await runApplicationAction({
      backend: started.backend,
      element: schema.find((item: any) => item.id === 'dummy_show_followup_dialog') as ActionUiElement,
      actionsById: indexActions(await started.backend.listApplicationActions()),
      context: { sessionId },
    });
    const rendered = renderWithMobileProviders(
      <ApplicationPluginsProvider backend={started.backend} connectionId="fixture">
        <GlobalDisplayLayer backend={started.backend} connectionId="fixture">
          <MobileDisplayHost scope="session" sessionId={sessionId} />
        </GlobalDisplayLayer>
      </ApplicationPluginsProvider>,
    );
    act(() => emitDisplayPresentation(started!.backend, normalizeDisplayEnvelope({
      id: 'fixture-result', source: 'action_response', connectionId: 'fixture', sessionId,
      display: shown.display!,
    })));
    fireEvent.press(screen.getByText('Enter value'));
    expect(screen.getByText('Edit value')).toBeTruthy();
    fireEvent.press(screen.getByTestId('application-action-dialog-cancel'));
    expect(screen.getByText('Neutral result')).toBeTruthy();
    fireEvent.press(screen.getByText('Enter value'));
    fireEvent.changeText(screen.getByTestId('action-form-input-value'), 'HTTP dialog value');
    fireEvent.press(screen.getByTestId('application-action-dialog-primary'));
    await waitFor(() => expect(screen.getByText('Follow-up submitted')).toBeTruthy());
    expect(screen.getByText('Value: HTTP dialog value\nNote: ')).toBeTruthy();
    rendered.unmount();
  }, 60000);

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