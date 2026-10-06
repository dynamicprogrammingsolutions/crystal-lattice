import type { ActionDisplayPayload } from '../../packages/frontend-sdk/src';

export const NEUTRAL_FOLLOWUP_DISPLAY: ActionDisplayPayload = {
  format: 'text',
  title: 'Neutral result',
  body: 'Open a dialog to enter a value.',
  presentation: 'modal',
  form: {
    kind: 'form',
    inputs: [{ name: 'note', label: 'Embedded note', type: 'string', default: 'kept note' }],
  },
  actions: [{
    kind: 'run_action',
    id: 'edit-neutral-value',
    label: 'Enter value',
    plugin: 'fixture',
    action_id: 'save',
    action_owner: 'application',
    fixed_params: { source: 'neutral-result' },
    param_map: {
      value: '$dialog.value',
      cleared: '$dialog.cleared',
      note: '$form.note',
      session_id: '$session.session_id',
    },
    preserve_display: true,
    dialog: {
      kind: 'form',
      title: 'Edit value',
      inputs: [
        { name: 'value', label: 'Value', type: 'string', required: true },
        { name: 'cleared', label: 'Optional value', type: 'string', submit_empty: true },
      ],
    },
  }],
};