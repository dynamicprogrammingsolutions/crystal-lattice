import type {
  ActionDisplayPayload,
  ActionDisplayRunActionAction,
  ActionUiElement,
} from '../types/plugins';

export function buildDisplayFollowupActionElement(
  action: ActionDisplayRunActionAction,
  display: ActionDisplayPayload,
): ActionUiElement {
  return {
    ui_type: 'action_result_followup',
    plugin: action.plugin,
    id: action.id,
    label: action.label,
    action_id: action.action_id,
    action_owner: action.action_owner,
    fixed_params: action.fixed_params,
    param_map: action.param_map,
    dialog: action.dialog,
    form: display.form,
  };
}