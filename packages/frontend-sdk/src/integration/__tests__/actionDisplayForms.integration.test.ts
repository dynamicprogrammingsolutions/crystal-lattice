import { afterEach, describe, expect, it } from 'vitest';

import { RestAgentBackend } from '../../backend/restBackend';
import { FetchTransport } from '../../transport/fetchTransport';
import { runApplicationAction } from '../../plugins/actionRunner';
import { buildDisplayFollowupActionElement } from '../../plugins/displayFollowupAction';
import type {
  ActionDisplayRunActionAction,
  ActionUiElement,
  ApplicationActionDefinition,
} from '../../types/plugins';
import { startBackendServer, type StartedServer } from '../harness';

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

function actionsById(actions: ApplicationActionDefinition[]): Record<string, ApplicationActionDefinition> {
  const indexed: Record<string, ApplicationActionDefinition> = {};
  for (const action of actions) {
    indexed[action.id] = action;
  }
  return indexed;
}

describe('action display embedded forms against a real backend', () => {
  let started: StartedServer | null = null;

  afterEach(async () => {
    if (started) {
      await started.stop();
      started = null;
    }
  });

  it('submits a neutral follow-up dialog through the public backend', async () => {
    started = await startBackendServer({ config: SERVER_CONFIG, startupTimeoutMs: 30000 });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;
    const actions = actionsById(await backend.listApplicationActions());
    const schema = await backend.getSessionApplicationUiSchema(sessionId, {
      pluginId: 'dummy_action_display_form_app',
    });
    const shown = await runApplicationAction({
      backend, actionsById: actions, context: { sessionId },
      element: schema.find((item: any) => item.id === 'dummy_show_followup_dialog') as ActionUiElement,
    });
    const action = shown.display!.actions![0] as ActionDisplayRunActionAction;
    expect(action.dialog?.kind).toBe('form');
    const submitted = await runApplicationAction({
      backend, actionsById: actions,
      element: buildDisplayFollowupActionElement(action, shown.display!),
      context: { sessionId, dialogValues: { value: 'neutral value', note: '' } },
    });
    expect(submitted.ok).toBe(true);
    expect(submitted.response?.result.submitted_values).toEqual({
      source: 'followup_dialog', value: 'neutral value', note: '',
    });
    expect(submitted.display?.title).toBe('Follow-up submitted');
  }, 60000);

  it('executes a display form follow-up action through the SDK runner', async () => {
    started = await startBackendServer({
      config: SERVER_CONFIG,
      startupTimeoutMs: 30000,
    });
    const backend = new RestAgentBackend({
      transport: new FetchTransport({ baseUrl: started.baseUrl }),
    });
    const created = await backend.createSession({ agentId: 'default' });
    const sessionId = created.session.session_id;

    const actions = actionsById(await backend.listApplicationActions());
    const uiSchema = await backend.getSessionApplicationUiSchema(sessionId, {
      pluginId: 'dummy_action_display_form_app',
    });
    const showElement = uiSchema.find(
      (element: any) => element.id === 'dummy_show_display_form',
    ) as ActionUiElement | undefined;

    expect(showElement).toBeTruthy();

    const shown = await runApplicationAction({
      backend,
      element: showElement!,
      actionsById: actions,
      context: { sessionId, connectionId: 'test-connection' },
    });

    expect(shown.ok).toBe(true);
    expect(shown.display?.form?.kind).toBe('form');
    const submitAction = shown.display?.actions?.find(
      (action): action is ActionDisplayRunActionAction =>
        action.kind === 'run_action' && action.id === 'dummy-submit-display-form',
    );
    expect(submitAction).toBeTruthy();

    const submitted = await runApplicationAction({
      backend,
      element: {
        ui_type: 'action_result_followup',
        plugin: submitAction!.plugin,
        id: submitAction!.id,
        label: submitAction!.label,
        action_id: submitAction!.action_id,
        action_owner: submitAction!.action_owner,
        fixed_params: submitAction!.fixed_params,
        param_map: submitAction!.param_map,
        form: shown.display!.form,
      } as ActionUiElement,
      actionsById: actions,
      context: {
        sessionId,
        connectionId: 'test-connection',
        formValues: {
          callback_url: 'https://example.test/callback?code=abc&state=xyz',
          note: 'integration test',
          mode: 'manual',
        },
      },
    });

    expect(submitted.ok).toBe(true);
    expect(submitted.display?.title).toBe('Dummy Form Submitted');
    expect(submitted.display?.body).toContain('https://example.test/callback?code=abc&state=xyz');
    expect(submitted.display?.body).toContain('integration test');
    expect(submitted.display?.body).toContain('manual');
  }, 60000);
});