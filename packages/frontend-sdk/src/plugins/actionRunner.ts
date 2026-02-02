import type { AgentBackend } from '../backend/backend';
import type { ApiMessage } from '../types/messages';
import type {
  ActionUiElement,
  StandardActionResult,
  ApplicationActionDefinition,
  ExecuteActionResponse,
  ExecuteActionResponseOk,
} from '../types/plugins';
import type { SessionSummary } from '../types/sessions';

export type ActionEffect =
  | { type: 'navigateToSession'; sessionId: string }
  | { type: 'reloadSession'; sessionId: string }
  | { type: 'reloadSessionsList' };

export interface RunActionContext {
  sessionId?: string;
  sessionSummary?: SessionSummary;
  messageContext?: { index: number; message: ApiMessage };
  dialogValues?: Record<string, any>;
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
  errorMessage?: string;
}

function getFromPath(root: any, path: string): any {
  if (!root) return undefined;
  const parts = path.split('.');
  let current: any = root;
  for (const part of parts) {
    if (current == null) return undefined;
    current = current[part];
  }
  return current;
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
        value = getFromPath(sessionRoot, path);
      } else if (source.startsWith('$message.')) {
        const path = source.slice('$message.'.length);
        const root = context.messageContext
          ? { index: context.messageContext.index, ...(context.messageContext.message as any) }
          : null;
        value = getFromPath(root, path);
      } else if (source.startsWith('$dialog.')) {
        const path = source.slice('$dialog.'.length);
        value = getFromPath(context.dialogValues || {}, path);
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
    return (response as any).message || 'Failed to execute action';
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
    const rawResponse = await backend.executeAction({
      pluginId,
      actionId,
      inputs,
    });

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
