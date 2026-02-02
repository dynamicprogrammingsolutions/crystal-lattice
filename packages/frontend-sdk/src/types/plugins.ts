export interface ActionInputParam {
  type?: string;
  required?: boolean;
  default?: any;
  description?: string;
  [k: string]: any;
}

export interface ApplicationActionDefinition {
  plugin: string;
  id: string;
  label?: string;
  description?: string;
  inputs?: Record<string, ActionInputParam>;
  [k: string]: any;
}

export interface ActionUiElement {
  ui_type: string;
  plugin: string;
  id: string;
  label: string;
  icon?: string;
  order?: number;
  action_id: string;
  fixed_params?: Record<string, any>;
  param_map?: Record<string, string>;
  dialog?: any;
  metadata?: Record<string, any>;
  [k: string]: any;
}

export interface ActionMutations {
  created_session_ids?: string[];
  updated_session_ids?: string[];
  deleted_session_ids?: string[];
}

export interface ActionUiEffects {
  navigate_to_session_id?: string | null;
  reload_session_ids?: string[];
  reload_sessions_list?: boolean;
}

export interface StandardActionResult {
  mutations?: ActionMutations;
  ui_effects?: ActionUiEffects;
  [k: string]: any;
}

export interface SessionListFieldElement {
  ui_type: string;
  plugin: string;
  key?: string;
  label?: string;
  description?: string;
  role?: string;
  data: string;
  template?: string;
  order?: number;
  metadata?: Record<string, any>;
  [k: string]: any;
}

export type ApplicationUiElement = ActionUiElement | SessionListFieldElement | Record<string, any>;

export interface ExecuteActionResponseOk {
  status: 'ok';
  plugin: string;
  action_id: string;
  result: StandardActionResult;
}

export interface ExecuteActionResponseError {
  status: 'error';
  plugin?: string;
  action_id?: string;
  error_type?: string;
  message?: string;
  details?: any;
}

export type ExecuteActionResponse = ExecuteActionResponseOk | ExecuteActionResponseError;
