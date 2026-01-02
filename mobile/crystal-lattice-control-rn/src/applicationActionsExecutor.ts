import { Alert } from 'react-native';
import type { ConnectionAdapter } from '../App';
import {
  apiExecuteAction,
  type ActionUiElement,
  type ApiMessage,
  type ApplicationActionDefinition,
  type ExecuteActionResponseOk,
  type SessionSummary,
} from './api';

export interface ApplicationActionExecutionContext {
  sessionId?: string;
  sessionSummary?: SessionSummary;
  messageContext?: { index: number; message: ApiMessage };
  dialogValues?: Record<string, any>;
}

export interface ApplicationActionExecutionResult {
  ok: boolean;
  response?: ExecuteActionResponseOk;
}

export async function executeApplicationAction(
  adapter: ConnectionAdapter,
  element: ActionUiElement,
  actionDefsById: Record<string, ApplicationActionDefinition>,
  context: ApplicationActionExecutionContext,
): Promise<ApplicationActionExecutionResult> {
  const actionId = element.action_id;
  const pluginId = element.plugin;
  const def = actionDefsById[actionId];
  const inputs: Record<string, any> = {};

  if (element.fixed_params && typeof element.fixed_params === 'object') {
    Object.entries(element.fixed_params).forEach(([k, v]) => {
      inputs[k] = v;
    });
  }

  const getFromPath = (root: any, path: string): any => {
    if (!root) return undefined;
    const parts = path.split('.');
    let current: any = root;
    for (const part of parts) {
      if (current == null) return undefined;
      current = current[part];
    }
    return current;
  };

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

  try {
    const resp = await apiExecuteAction(adapter, pluginId, actionId, inputs);
    if (resp.status !== 'ok') {
      const msg = (resp as any).message || 'Failed to execute action';
      Alert.alert('Action error', msg);
      return { ok: false };
    }
    return { ok: true, response: resp as ExecuteActionResponseOk };
  } catch (err: any) {
    console.log('Failed to execute application action', err);
    const msg = err?.message || 'Failed to execute action';
    Alert.alert('Action error', msg);
    return { ok: false };
  }
}
