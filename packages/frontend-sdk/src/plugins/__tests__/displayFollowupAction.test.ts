import { describe, expect, it } from 'vitest';
import { buildDisplayFollowupActionElement } from '../displayFollowupAction';
import { runApplicationAction } from '../actionRunner';
import type { AgentBackend } from '../../backend/backend';
import type { ActionDisplayPayload, ActionDisplayRunActionAction } from '../../types/plugins';

describe('display follow-up action adapter', () => {
  it('preserves dialog and embedded form values through the action runner', async () => {
    const form = { kind: 'form' as const, inputs: [{ name: 'note', submit_empty: true }] };
    const action: ActionDisplayRunActionAction = {
      kind: 'run_action', id: 'edit', label: 'Edit', plugin: 'fixture',
      action_id: 'save', action_owner: 'application',
      fixed_params: { source: 'result' },
      param_map: { value: '$dialog.value', cleared: '$dialog.cleared', note: '$form.note' },
      dialog: {
        kind: 'form',
        inputs: [{ name: 'value' }, { name: 'cleared', submit_empty: true }],
      },
    };
    const display: ActionDisplayPayload = { format: 'text', body: 'Result', form };
    const element = buildDisplayFollowupActionElement(action, display);
    expect(element.dialog).toBe(action.dialog);
    expect(element.form).toBe(form);
    let captured: unknown;
    const backend = {
      executeAction: async (params: any) => {
        captured = params;
        return { status: 'ok', plugin: 'fixture', action_id: 'save', result: {} };
      },
    } as AgentBackend;
    const result = await runApplicationAction({
      backend, element, actionsById: {},
      context: { dialogValues: { value: 'updated' }, formValues: {} },
    });
    expect(result.ok).toBe(true);
    expect(captured).toMatchObject({
      actionOwner: 'application',
      inputs: { source: 'result', value: 'updated', cleared: '', note: '' },
    });
  });
});