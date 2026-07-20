import type { AgentBackend } from '../backend/backend';
import type { ApiMessage } from '../types/messages';
import type {
  ActionUiElement,
  StandardActionResult,
  ActionDisplayPayload,
  ApplicationActionDefinition,
  ExecuteActionResponse,
  ExecuteActionResponseOk,
} from '../types/plugins';
import type { SessionSummary } from '../types/sessions';
import { resolveSessionListPath } from '../sessions/sessionListContracts';

export type ActionEffect =
  | { type: 'navigateToSession'; sessionId: string }
  | { type: 'reloadSession'; sessionId: string }
  | { type: 'reloadSessionsList' };

export interface RunActionContext {
  sessionId?: string;
  connectionId?: string;
  sessionSummary?: SessionSummary;
  messageContext?: { index: number; message: ApiMessage };
  dialogValues?: Record<string, any>;
  formValues?: Record<string, any>;
}

export interface RunActionEffectsOptions {
  currentSessionId?: string | null;
  navigateOnCreatedSession?: boolean;
  reloadSessionsListOnMutations?: boolean;
}

export interface RunActionResult {
  ok: boolean;
  rawResponse: ExecuteActionResponse;
  response?: ExecuteActionResponseOk;
  effects: ActionEffect[];
  display?: ActionDisplayPayload;
  errorMessage?: string;
}

function shouldUseSessionScopedActionEndpoint(
  element: ActionUiElement,
  context: RunActionContext,
  backend: AgentBackend,
): boolean {
  return (
    typeof context.sessionId === 'string' &&
    context.sessionId.length > 0 &&
    typeof backend.executeSessionAction === 'function' &&
    typeof element.ui_type === 'string' &&
    element.ui_type.length > 0
  );
}

function getFormFieldSubmitEmpty(form: any, fieldName: string): boolean {
  if (!form || typeof form !== 'object') return false;
  if (form.kind !== 'form') return false;
  const inputs: any = form.inputs;
  if (!Array.isArray(inputs)) return false;
  const field = inputs.find((f: any) => f && typeof f === 'object' && f.name === fieldName);
  return field?.submit_empty === true;
}

function buildActionInputs(options: {
  element: ActionUiElement;
  actionDefsById: Record<string, ApplicationActionDefinition>;
  context: RunActionContext;
}): Record<string, any> {
  const { element, actionDefsById, context } = options;
  const def = actionDefsById[element.action_id];
  const inputs: Record<string, any> = {};

  if (element.fixed_params && typeof element.fixed_params === 'object') {
    Object.entries(element.fixed_params).forEach(([key, value]) => {
      inputs[key] = value;
    });
  }

  if (element.param_map && typeof element.param_map === 'object') {
    for (const [paramName, source] of Object.entries(element.param_map)) {
      if (typeof source !== 'string') continue;
      let value: any;
      if (source.startsWith('$session.')) {
        const path = source.slice('$session.'.length);
        const sessionRoot =
          (context.sessionSummary as any) ||
          (context.sessionId ? ({ session_id: context.sessionId } as any) : null);
        const resolved = resolveSessionListPath(sessionRoot, path);
        value = resolved.found ? resolved.value : undefined;
      } else if (source.startsWith('$message.')) {
        const path = source.slice('$message.'.length);
        const root = context.messageContext
          ? { index: context.messageContext.index, ...(context.messageContext.message as any) }
          : null;
        const resolved = resolveSessionListPath(root, path);
        value = resolved.found ? resolved.value : undefined;
      } else if (source.startsWith('$dialog.')) {
        const path = source.slice('$dialog.'.length);
        const resolved = resolveSessionListPath(context.dialogValues || {}, path);
        value = resolved.found ? resolved.value : undefined;
        if (
          value === undefined &&
          context.dialogValues &&
          getFormFieldSubmitEmpty((element as any).dialog, path)
        ) {
          value = '';
        }
      } else if (source.startsWith('$form.')) {
        const path = source.slice('$form.'.length);
        const resolved = resolveSessionListPath(context.formValues || {}, path);
        value = resolved.found ? resolved.value : undefined;
        if (
          value === undefined &&
          context.formValues &&
          getFormFieldSubmitEmpty((element as any).form, path)
        ) {
          value = '';
        }
      } else if (source.startsWith('$context.')) {
        const path = source.slice('$context.'.length);
        const resolved = resolveSessionListPath(context, path);
        value = resolved.found ? resolved.value : undefined;
      }

      if (value !== undefined) {
        inputs[paramName] = value;
      }
    }
  }

  if (def && def.inputs) {
    Object.entries(def.inputs).forEach(([name, spec]) => {
      if ((spec as any).type === 'array' && name in inputs && !Array.isArray(inputs[name])) {
        inputs[name] = [inputs[name]];
      }
    });
  }

  return inputs;
}

function deriveActionEffectsFromResult(options: {
  okResponse: ExecuteActionResponseOk;
  effects: RunActionEffectsOptions;
}): ActionEffect[] {
  const { okResponse, effects } = options;
  const result: StandardActionResult = okResponse.result || {};

  const mutations: any =
    result && typeof result.mutations === 'object' && result.mutations
      ? result.mutations
      : {};
  const uiEffects: any =
    result && typeof result.ui_effects === 'object' && result.ui_effects
      ? result.ui_effects
      : {};

  const createdSessionIds: string[] = Array.isArray(mutations.created_session_ids)
    ? (mutations.created_session_ids as any[]).filter((id) => typeof id === 'string')
    : [];
  const updatedSessionIds: string[] = Array.isArray(mutations.updated_session_ids)
    ? (mutations.updated_session_ids as any[]).filter((id) => typeof id === 'string')
    : [];
  const deletedSessionIds: string[] = Array.isArray(mutations.deleted_session_ids)
    ? (mutations.deleted_session_ids as any[]).filter((id) => typeof id === 'string')
    : [];

  const hasExplicitNavigateTarget = Object.prototype.hasOwnProperty.call(
    uiEffects,
    'navigate_to_session_id',
  );
  const navigateToSessionId =
    typeof uiEffects.navigate_to_session_id === 'string' && uiEffects.navigate_to_session_id
      ? uiEffects.navigate_to_session_id
      : null;

  const reloadSessionIds: string[] = Array.isArray(uiEffects.reload_session_ids)
    ? (uiEffects.reload_session_ids as any[]).filter((id) => typeof id === 'string')
    : [];
  const reloadSessionsList = uiEffects.reload_sessions_list === true;

  const effectList: ActionEffect[] = [];

  if (navigateToSessionId) {
    effectList.push({ type: 'navigateToSession', sessionId: navigateToSessionId });
  } else if (!hasExplicitNavigateTarget && effects.navigateOnCreatedSession && createdSessionIds.length > 0) {
    effectList.push({ type: 'navigateToSession', sessionId: createdSessionIds[0] });
  }

  if (reloadSessionsList) {
    effectList.push({ type: 'reloadSessionsList' });
  } else if (effects.reloadSessionsListOnMutations) {
    if (createdSessionIds.length > 0 || updatedSessionIds.length > 0 || deletedSessionIds.length > 0) {
      effectList.push({ type: 'reloadSessionsList' });
    }
  }

  if (effects.currentSessionId) {
    if (reloadSessionIds.includes(effects.currentSessionId)) {
      effectList.push({ type: 'reloadSession', sessionId: effects.currentSessionId });
    }
  }

  return effectList;
}

export function getRunActionErrorMessage(response: ExecuteActionResponse): string {
  if (!response) return 'Failed to execute action';
  if (response.status !== 'ok') {
    const msg = (response as any).message || 'Failed to execute action';
    const details: any = (response as any).details;
    if (details && typeof details === 'object') {
      const missing = Array.isArray(details.missing_params) ? details.missing_params : [];
      const extra = Array.isArray(details.extra_params) ? details.extra_params : [];
      const invalid = details.invalid_types && typeof details.invalid_types === 'object'
        ? Object.keys(details.invalid_types)
        : [];

      const parts: string[] = [];
      if (missing.length) parts.push(`missing: ${missing.join(', ')}`);
      if (invalid.length) parts.push(`invalid: ${invalid.join(', ')}`);
      if (extra.length) parts.push(`extra: ${extra.join(', ')}`);
      if (parts.length) return `${msg} (${parts.join('; ')})`;
    }

    return msg;
  }

  const okResp = response as ExecuteActionResponseOk;
  const result: any = okResp.result || {};
  if (result && typeof result.status === 'string' && result.status !== 'ok') {
    return result.message || 'Action failed';
  }

  return 'Failed to execute action';
}

export async function runApplicationAction(options: {
  backend: AgentBackend;
  element: ActionUiElement;
  actionsById: Record<string, ApplicationActionDefinition>;
  context: RunActionContext;
  effects?: RunActionEffectsOptions;
}): Promise<RunActionResult> {
  const { backend, element, actionsById, context, effects } = options;

  const actionId = element.action_id;
  const pluginId = element.plugin;
  const inputs = buildActionInputs({ element, actionDefsById: actionsById, context });

  try {
    const executeParams = {
      pluginId,
      actionId,
      actionOwner:
        typeof element.action_owner === 'string' && element.action_owner
          ? element.action_owner
          : undefined,
      inputs,
    };
    const rawResponse = shouldUseSessionScopedActionEndpoint(element, context, backend)
      ? await backend.executeSessionAction!({
          sessionId: context.sessionId!,
          ...executeParams,
        })
      : await backend.executeAction(executeParams);

    if (!rawResponse || rawResponse.status !== 'ok') {
      return {
        ok: false,
        rawResponse,
        effects: [],
        errorMessage: getRunActionErrorMessage(rawResponse),
      };
    }

    const okResponse = rawResponse as ExecuteActionResponseOk;
    const result: any = okResponse.result || {};
    if (result && typeof result.status === 'string' && result.status !== 'ok') {
      return {
        ok: false,
        rawResponse,
        response: okResponse,
        effects: [],
        errorMessage: getRunActionErrorMessage(rawResponse),
      };
    }

    return {
      ok: true,
      rawResponse,
      response: okResponse,
      display:
        result && typeof result.display === 'object' && result.display
          ? (result.display as ActionDisplayPayload)
          : undefined,
      effects: deriveActionEffectsFromResult({
        okResponse,
        effects: {
          currentSessionId: effects?.currentSessionId ?? null,
          navigateOnCreatedSession: effects?.navigateOnCreatedSession ?? false,
          reloadSessionsListOnMutations: effects?.reloadSessionsListOnMutations ?? false,
        },
      }),
    };
  } catch (err: any) {
    return {
      ok: false,
      rawResponse: {
        status: 'error',
        message: err?.message || 'Failed to execute action',
      } as any,
      effects: [],
      errorMessage: err?.message || 'Failed to execute action',
    };
  }
}
