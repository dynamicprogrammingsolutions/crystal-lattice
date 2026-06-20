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
  action_owner?: string;
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

export interface ActionDisplayOpenUrlAction {
  kind: 'open_url';
  id: string;
  label: string;
  url: string;
}

export interface ActionDisplayCopyTextAction {
  kind: 'copy_text';
  id: string;
  label: string;
  text: string;
  copied_label?: string;
}

export interface ActionDisplayRunActionAction {
  kind: 'run_action';
  id: string;
  label: string;
  plugin: string;
  action_id: string;
  action_owner?: string;
  fixed_params?: Record<string, unknown>;
  param_map?: Record<string, string>;
  preserve_display?: boolean;
}

export interface ActionDisplayDismissAction {
  kind: 'dismiss';
  id: string;
  label: string;
}

export interface ActionDisplayDownloadAttachmentAssetAction {
  kind: 'download_attachment_asset';
  id: string;
  label: string;
  session_id: string;
  asset_id: string;
  filename: string;
  mime_type: string;
  plugin?: string;
  action_owner?: string;
  behavior?: 'platform_default' | 'share' | 'save';
}

export type ActionDisplayFollowupAction =
  | ActionDisplayOpenUrlAction
  | ActionDisplayCopyTextAction
  | ActionDisplayRunActionAction
  | ActionDisplayDismissAction
  | ActionDisplayDownloadAttachmentAssetAction;

export interface ActionDisplayFormPayload {
  kind: 'form';
  title?: string;
  message?: string;
  inputs?: any[];
  [k: string]: any;
}

export interface ActionDisplayPayload {
  format: 'markdown' | 'text';
  body: string;
  title?: string;
  variant?: 'info' | 'success' | 'warning' | 'error';
  presentation?: 'modal' | 'inline' | 'banner';
  dismissible?: boolean;
  form?: ActionDisplayFormPayload;
  actions?: ActionDisplayFollowupAction[];
  display_id?: string;
}

export interface StandardActionResult {
  mutations?: ActionMutations;
  ui_effects?: ActionUiEffects;
  display?: ActionDisplayPayload;
  message?: string;
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
  action_owner?: string;
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
