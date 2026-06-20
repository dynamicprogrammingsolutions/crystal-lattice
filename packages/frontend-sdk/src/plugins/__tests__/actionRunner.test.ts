import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../../backend/backend';
import type { ActionUiElement, ApplicationActionDefinition, ExecuteActionResponseOk } from '../../types/plugins';
import { runApplicationAction } from '../actionRunner';

function buildBackend(response: ExecuteActionResponseOk): AgentBackend {
  return {
    kind: 'test',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    executeAction: async () => response,
  } as any;
}

function buildBackendWithSessionAction(response: ExecuteActionResponseOk): AgentBackend {
  return {
    kind: 'test',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    executeAction: async () => response,
    executeSessionAction: async () => response,
  } as any;
}

const ACTION_DEF: ApplicationActionDefinition = {
  plugin: 'session_actions',
  id: 'copy_session',
  label: 'Copy session',
  inputs: {},
};

const ELEMENT: ActionUiElement = {
  ui_type: 'session_action',
  plugin: 'session_actions',
  id: 'copy_session_from_view',
  label: 'Copy',
  action_id: 'copy_session',
};

describe('runApplicationAction effect derivation', () => {
  it('uses the session-scoped action endpoint when a session context is available', async () => {
    const executeAction = vi.fn(async () => ({
      status: 'ok',
      plugin: 'session_title',
      action_id: 'set_session_title',
      result: { mutations: {}, ui_effects: {} },
    }));
    const executeSessionAction = vi.fn(async () => ({
      status: 'ok',
      plugin: 'session_title',
      action_id: 'set_session_title',
      result: { mutations: {}, ui_effects: {} },
    }));
    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction,
      executeSessionAction,
    } as any;

    const res = await runApplicationAction({
      backend,
      element: {
        ui_type: 'session_action',
        plugin: 'session_title',
        id: 'edit_title',
        label: 'Edit title',
        action_id: 'set_session_title',
      },
      actionsById: {},
      context: { sessionId: 's1' },
    });

    expect(res.ok).toBe(true);
    expect(executeSessionAction).toHaveBeenCalledWith({
      sessionId: 's1',
      pluginId: 'session_title',
      actionId: 'set_session_title',
      actionOwner: undefined,
      inputs: {},
    });
    expect(executeAction).not.toHaveBeenCalled();
  });

  it('maps connection id from generic action context', async () => {
    const executeSessionAction = vi.fn(async () => ({
      status: 'ok',
      plugin: 'generic_callback_app',
      action_id: 'start_external_flow',
      result: { mutations: {}, ui_effects: {} },
    }));
    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction: vi.fn(),
      executeSessionAction,
    } as any;

    const res = await runApplicationAction({
      backend,
      element: {
        ui_type: 'session_action',
        plugin: 'generic_callback_app',
        id: 'generic_callback_start_external_flow',
        label: 'Create callback link',
        action_id: 'start_external_flow',
        param_map: {
          connection_id: '$context.connectionId',
        },
      },
      actionsById: {},
      context: { sessionId: 's1', connectionId: 'test-connection' },
    });

    expect(res.ok).toBe(true);
    expect(executeSessionAction).toHaveBeenCalledWith({
      sessionId: 's1',
      pluginId: 'generic_callback_app',
      actionId: 'start_external_flow',
      actionOwner: undefined,
      inputs: { connection_id: 'test-connection' },
    });
  });

  it('falls back to the generic action endpoint without a session context', async () => {
    const executeAction = vi.fn(async () => ({
      status: 'ok',
      plugin: 'cloud',
      action_id: 'cloud.start_session_agent',
      result: { mutations: {}, ui_effects: {} },
    }));
    const executeSessionAction = vi.fn(async () => ({
      status: 'ok',
      plugin: 'cloud',
      action_id: 'cloud.start_session_agent',
      result: { mutations: {}, ui_effects: {} },
    }));
    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction,
      executeSessionAction,
    } as any;

    const res = await runApplicationAction({
      backend,
      element: {
        ui_type: 'application_action',
        plugin: 'cloud',
        id: 'start_cloud',
        label: 'Start cloud agent',
        action_id: 'cloud.start_session_agent',
      },
      actionsById: {},
      context: {},
    });

    expect(res.ok).toBe(true);
    expect(executeAction).toHaveBeenCalledWith({
      pluginId: 'cloud',
      actionId: 'cloud.start_session_agent',
      actionOwner: undefined,
      inputs: {},
    });
    expect(executeSessionAction).not.toHaveBeenCalled();
  });

  it('forwards action_owner to backend execution for provider-extension actions', async () => {
    const executeAction = vi.fn(async () => ({
      status: 'ok',
      plugin: 'provider_ext',
      action_id: 'compact_native_history',
      result: { mutations: {}, ui_effects: {} },
    }));
    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction,
    } as any;

    const res = await runApplicationAction({
      backend,
      element: {
        ui_type: 'session_action',
        plugin: 'provider_ext',
        id: 'compact',
        label: 'Compact',
        action_id: 'compact_native_history',
        action_owner: 'provider_extension',
      },
      actionsById: {},
      context: { sessionId: 's1' },
    });

    expect(res.ok).toBe(true);
    expect(executeAction).toHaveBeenCalledWith({
      pluginId: 'provider_ext',
      actionId: 'compact_native_history',
      actionOwner: 'provider_extension',
      inputs: {},
    });
  });

  it('does not reload the current session just because it was updated', async () => {
    const backend = buildBackend({
      status: 'ok',
      plugin: 'session_actions',
      action_id: 'copy_session',
      result: {
        mutations: {
          created_session_ids: [],
          updated_session_ids: ['s1'],
          deleted_session_ids: [],
        },
        ui_effects: {},
      },
    });

    const res = await runApplicationAction({
      backend,
      element: ELEMENT,
      actionsById: { copy_session: ACTION_DEF },
      context: { sessionId: 's1' },
      effects: { currentSessionId: 's1' },
    });

    expect(res.ok).toBe(true);
    expect(res.effects.some((e) => e.type === 'reloadSession')).toBe(false);
  });

  it('renders display payloads for pollable starting action results', async () => {
    const display = {
      format: 'markdown' as const,
      title: 'Cloud Agent Starting',
      body: 'The cloud runtime is starting.',
      variant: 'warning' as const,
      actions: [
        {
          kind: 'copy_text' as const,
          id: 'copy-cloud-connection-link',
          label: 'Copy connection link',
          text: 'crystal-lattice-cloud://connect?instance_id=inst_test',
        },
        {
          kind: 'run_action' as const,
          id: 'refresh-cloud-agent-status',
          label: 'Refresh status',
          plugin: 'cloud',
          action_id: 'cloud.check_session_agent',
        },
      ],
    };
    const backend = buildBackendWithSessionAction({
      status: 'ok',
      plugin: 'cloud',
      action_id: 'cloud.start_session_agent',
      result: {
        state: 'starting',
        connection_link: 'crystal-lattice-cloud://connect?instance_id=inst_test',
        display,
      },
    });

    const res = await runApplicationAction({
      backend,
      element: {
        ui_type: 'session_action',
        plugin: 'cloud',
        id: 'cloud_start_session_agent',
        label: 'Start cloud agent',
        action_id: 'cloud.start_session_agent',
      },
      actionsById: {},
      context: { sessionId: 's1' },
    });

    expect(res.ok).toBe(true);
    expect(res.display).toEqual(display);
  });

  it('reloads the current session only when explicitly requested via ui_effects', async () => {
    const backend = buildBackend({
      status: 'ok',
      plugin: 'rebuild_native',
      action_id: 'rebuild_native_history',
      result: {
        mutations: {
          created_session_ids: [],
          updated_session_ids: ['s1'],
          deleted_session_ids: [],
        },
        ui_effects: { reload_session_ids: ['s1'] },
      },
    });

    const res = await runApplicationAction({
      backend,
      element: { ...ELEMENT, plugin: 'rebuild_native', action_id: 'rebuild_native_history' },
      actionsById: { rebuild_native_history: { ...ACTION_DEF, plugin: 'rebuild_native', id: 'rebuild_native_history' } },
      context: { sessionId: 's1' },
      effects: { currentSessionId: 's1' },
    });

    expect(res.ok).toBe(true);
    expect(res.effects).toEqual([{ type: 'reloadSession', sessionId: 's1' }]);
  });

  it('suppresses auto-navigation when navigate_to_session_id is explicitly null', async () => {
    const backend = buildBackend({
      status: 'ok',
      plugin: 'session_actions',
      action_id: 'copy_session',
      result: {
        mutations: {
          created_session_ids: ['s2'],
          updated_session_ids: [],
          deleted_session_ids: [],
        },
        ui_effects: { navigate_to_session_id: null },
      },
    });

    const res = await runApplicationAction({
      backend,
      element: ELEMENT,
      actionsById: { copy_session: ACTION_DEF },
      context: { sessionId: 's1' },
      effects: { currentSessionId: 's1', navigateOnCreatedSession: true },
    });

    expect(res.ok).toBe(true);
    expect(res.effects.some((e) => e.type === 'navigateToSession')).toBe(false);
  });

  it('reloads sessions list based on client policy or explicit request', async () => {
    const backend = buildBackend({
      status: 'ok',
      plugin: 'session_title',
      action_id: 'set_session_title',
      result: {
        mutations: {
          created_session_ids: [],
          updated_session_ids: ['s1'],
          deleted_session_ids: [],
        },
        ui_effects: { reload_sessions_list: true },
      },
    });

    const res = await runApplicationAction({
      backend,
      element: { ...ELEMENT, plugin: 'session_title', action_id: 'set_session_title' },
      actionsById: { set_session_title: { ...ACTION_DEF, plugin: 'session_title', id: 'set_session_title' } },
      context: { sessionId: 's1' },
      effects: { reloadSessionsListOnMutations: true },
    });

    expect(res.ok).toBe(true);
    expect(res.effects).toEqual([{ type: 'reloadSessionsList' }]);
  });

  it('passes through generic display payloads for frontend rendering', async () => {
    const backend = buildBackend({
      status: 'ok',
      plugin: 'chatgpt_auth',
      action_id: 'login_start',
      result: {
        display: {
          format: 'markdown',
          title: 'ChatGPT Login',
          body: 'Open [this link](https://auth.openai.com/codex/device)',
          variant: 'info',
          presentation: 'inline',
          dismissible: true,
          display_id: 'chatgpt-auth-login',
          actions: [
            {
              kind: 'open_url',
              id: 'open-login',
              label: 'Open link',
              url: 'https://auth.openai.com/codex/device',
            },
          ],
        },
        auth_status: {
          state: 'pending',
        },
      },
    });

    const res = await runApplicationAction({
      backend,
      element: { ...ELEMENT, plugin: 'chatgpt_auth', action_id: 'login_start' },
      actionsById: {
        login_start: { ...ACTION_DEF, plugin: 'chatgpt_auth', id: 'login_start' },
      },
      context: { sessionId: 's1' },
    });

    expect(res.ok).toBe(true);
    expect(res.display).toEqual({
      format: 'markdown',
      title: 'ChatGPT Login',
      body: 'Open [this link](https://auth.openai.com/codex/device)',
      variant: 'info',
      presentation: 'inline',
      dismissible: true,
      display_id: 'chatgpt-auth-login',
      actions: [
        {
          kind: 'open_url',
          id: 'open-login',
          label: 'Open link',
          url: 'https://auth.openai.com/codex/device',
        },
      ],
    });
  });
});

describe('runApplicationAction input building', () => {
  it('maps the current session id for session-scoped actions', async () => {
    let capturedInputs: Record<string, any> | null = null;

    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction: async ({ inputs }) => {
        capturedInputs = inputs;
        return {
          status: 'ok',
          plugin: 'cloud',
          action_id: 'cloud.start_session_agent',
          result: { mutations: {}, ui_effects: {} },
        } as any;
      },
    } as any;

    await runApplicationAction({
      backend,
      element: {
        ui_type: 'session_action',
        plugin: 'cloud',
        id: 'cloud_start_session_agent',
        label: 'Start cloud agent',
        action_id: 'cloud.start_session_agent',
        param_map: { session_id: '$session.session_id' },
      } as any,
      actionsById: {
        'cloud.start_session_agent': {
          plugin: 'cloud',
          id: 'cloud.start_session_agent',
          label: 'Start cloud agent',
          inputs: {
            session_id: { type: 'string', required: true },
          },
        } as any,
      },
      context: { sessionId: 's1' },
    });

    expect(capturedInputs).toEqual({ session_id: 's1' });
  });

  it('maps cloud instance inputs from dialog values', async () => {
    let capturedInputs: Record<string, any> | null = null;

    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction: async ({ inputs }) => {
        capturedInputs = inputs;
        return {
          status: 'ok',
          plugin: 'cloud',
          action_id: 'cloud.check_session_agent',
          result: { mutations: {}, ui_effects: {} },
        } as any;
      },
    } as any;

    await runApplicationAction({
      backend,
      element: {
        ui_type: 'session_action',
        plugin: 'cloud',
        id: 'cloud_check_session_agent',
        label: 'Check cloud status',
        action_id: 'cloud.check_session_agent',
        param_map: {
          instance_id: '$dialog.instance_id',
          session_id: '$session.session_id',
          token: '$dialog.token',
        },
      } as any,
      actionsById: {
        'cloud.check_session_agent': {
          plugin: 'cloud',
          id: 'cloud.check_session_agent',
          label: 'Check cloud status',
          inputs: {
            instance_id: { type: 'string', required: true },
            session_id: { type: 'string', required: false },
            token: { type: 'string', required: false },
          },
        } as any,
      },
      context: {
        sessionId: 's1',
        sessionSummary: {
          session_id: 's1',
          modified: 1,
          preview: '',
          metadata: {
            cloud_agent: {
              instance_id: 'inst_test',
              token: 'tok_test',
            },
          },
        },
        dialogValues: {
          instance_id: 'inst_test',
          token: 'tok_test',
        },
      },
    });

    expect(capturedInputs).toEqual({
      instance_id: 'inst_test',
      session_id: 's1',
      token: 'tok_test',
    });
  });

  it('allows dialog values to supply cloud status inputs when session metadata is missing', async () => {
    let capturedInputs: Record<string, any> | null = null;

    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction: async ({ inputs }) => {
        capturedInputs = inputs;
        return {
          status: 'ok',
          plugin: 'cloud',
          action_id: 'cloud.check_session_agent',
          result: { mutations: {}, ui_effects: {} },
        } as any;
      },
    } as any;

    await runApplicationAction({
      backend,
      element: {
        ui_type: 'session_action',
        plugin: 'cloud',
        id: 'cloud_check_session_agent',
        label: 'Check cloud status',
        action_id: 'cloud.check_session_agent',
        param_map: {
          instance_id: '$dialog.instance_id',
          session_id: '$session.session_id',
          token: '$dialog.token',
        },
      } as any,
      actionsById: {
        'cloud.check_session_agent': {
          plugin: 'cloud',
          id: 'cloud.check_session_agent',
          label: 'Check cloud status',
          inputs: {
            instance_id: { type: 'string', required: true },
            session_id: { type: 'string', required: false },
            token: { type: 'string', required: false },
          },
        } as any,
      },
      context: {
        sessionId: 's1',
        sessionSummary: {
          session_id: 's1',
          modified: 1,
          preview: '',
          metadata: {},
        },
        dialogValues: {
          instance_id: 'inst_manual',
          token: 'tok_manual',
        },
      },
    });

    expect(capturedInputs).toEqual({
      instance_id: 'inst_manual',
      session_id: 's1',
      token: 'tok_manual',
    });
  });

  it('includes empty dialog fields when submit_empty is true', async () => {
    let capturedInputs: Record<string, any> | null = null;

    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction: async ({ inputs }) => {
        capturedInputs = inputs;
        return {
          status: 'ok',
          plugin: 'session_title',
          action_id: 'set_session_title',
          result: { mutations: { created_session_ids: [], updated_session_ids: [], deleted_session_ids: [] }, ui_effects: {} },
        } as any;
      },
    } as any;

    const element: ActionUiElement = {
      ui_type: 'session_action',
      plugin: 'session_title',
      id: 'edit_title_from_view',
      label: 'Edit title',
      action_id: 'set_session_title',
      fixed_params: { source: 'session_view' } as any,
      param_map: {
        session_id: '$session.session_id',
        title: '$dialog.title',
        subtitle: '$dialog.subtitle',
      } as any,
      dialog: {
        kind: 'form',
        inputs: [
          { name: 'title', type: 'string', required: false, submit_empty: true },
          { name: 'subtitle', type: 'string', required: false, submit_empty: true },
        ],
      } as any,
    } as any;

    await runApplicationAction({
      backend,
      element,
      actionsById: {
        set_session_title: {
          plugin: 'session_title',
          id: 'set_session_title',
          label: 'Set session title',
          inputs: {
            session_id: { type: 'string', required: true },
            title: { type: 'string', required: false },
            subtitle: { type: 'string', required: false },
            source: { type: 'string', required: false },
          },
        } as any,
      },
      context: {
        sessionId: 's1',
        dialogValues: { subtitle: 'hello' },
      },
    });

    expect(capturedInputs).toEqual({
      source: 'session_view',
      session_id: 's1',
      title: '',
      subtitle: 'hello',
    });
  });

  it('maps embedded display form values into follow-up action inputs', async () => {
    let capturedInputs: Record<string, any> | null = null;

    const backend: AgentBackend = {
      kind: 'test',
      getCapabilities: () => ({
        featureCompletions: false,
        sessionUiSchema: false,
        sessionConfigOverrides: false,
        sessionPlugins: false,
        applicationActions: true,
        applicationConfig: false,
      }),
      executeAction: async ({ inputs }) => {
        capturedInputs = inputs;
        return {
          status: 'ok',
          plugin: 'dummy_display_form_app',
          action_id: 'submit_display_form',
          result: { mutations: {}, ui_effects: {} },
        } as any;
      },
    } as any;

    await runApplicationAction({
      backend,
      element: {
        ui_type: 'action_result_followup',
        plugin: 'dummy_display_form_app',
        id: 'submit-display-form',
        label: 'Submit',
        action_id: 'submit_display_form',
        fixed_params: { source: 'display' } as any,
        param_map: {
          callback_url: '$form.callback_url',
          note: '$form.note',
        },
        form: {
          kind: 'form',
          inputs: [
            { name: 'callback_url', type: 'multiline', required: true },
            { name: 'note', type: 'string', required: false, submit_empty: true },
          ],
        },
      } as any,
      actionsById: {
        submit_display_form: {
          plugin: 'dummy_display_form_app',
          id: 'submit_display_form',
          label: 'Submit display form',
          inputs: {
            source: { type: 'string', required: true },
            callback_url: { type: 'string', required: true },
            note: { type: 'string', required: false },
          },
        } as any,
      },
      context: {
        formValues: {
          callback_url: 'http://127.0.0.1:41793/callback?code=abc&state=xyz',
        },
      },
    });

    expect(capturedInputs).toEqual({
      source: 'display',
      callback_url: 'http://127.0.0.1:41793/callback?code=abc&state=xyz',
      note: '',
    });
  });
});
