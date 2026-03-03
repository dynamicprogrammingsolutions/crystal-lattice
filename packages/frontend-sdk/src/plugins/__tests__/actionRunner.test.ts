import { describe, expect, it } from 'vitest';

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
});

describe('runApplicationAction input building', () => {
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
});
