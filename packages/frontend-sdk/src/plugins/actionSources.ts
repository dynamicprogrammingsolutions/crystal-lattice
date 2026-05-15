import type { ActionUiElement } from '../types/plugins';
import type { UiSchemaElement } from '../types/uiSchema';
import { evaluateCondition } from '../utils/uiSchema';

export type SessionScopedActionUiType = 'session_action' | 'message_action';

function isActionUiElement(value: unknown, uiType?: SessionScopedActionUiType): value is ActionUiElement {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const typed = value as ActionUiElement;
  if (typeof typed.id !== 'string' || !typed.id.trim()) {
    return false;
  }
  if (typeof typed.plugin !== 'string' || !typed.plugin.trim()) {
    return false;
  }
  if (typeof typed.action_id !== 'string' || !typed.action_id.trim()) {
    return false;
  }
  if (typeof typed.label !== 'string' || !typed.label.trim()) {
    return false;
  }
  if (typeof typed.ui_type !== 'string' || !typed.ui_type.trim()) {
    return false;
  }
  if (uiType && typed.ui_type !== uiType) {
    return false;
  }

  return true;
}

export function selectSessionScopedActionElements(options: {
  uiSchemaElements: UiSchemaElement[];
  uiType: SessionScopedActionUiType;
  context?: object | null;
}): ActionUiElement[] {
  const { uiSchemaElements, uiType, context } = options;
  return (uiSchemaElements || []).filter((element): element is ActionUiElement => {
    if (!isActionUiElement(element, uiType)) {
      return false;
    }
    const condition = (element as any).condition;
    return context ? evaluateCondition(condition, context) : true;
  });
}

export function mergeSessionScopedActionElements(options: {
  applicationActions: ActionUiElement[];
  uiSchemaElements: UiSchemaElement[];
  uiType: SessionScopedActionUiType;
  context?: object | null;
}): ActionUiElement[] {
  const { applicationActions, uiSchemaElements, uiType, context } = options;

  const mergedById = new Map<string, ActionUiElement>();
  const orderedIds: string[] = [];

  for (const action of applicationActions || []) {
    if (!isActionUiElement(action, uiType)) {
      continue;
    }
    if (context && !evaluateCondition((action as any).condition, context)) {
      continue;
    }
    if (!mergedById.has(action.id)) {
      orderedIds.push(action.id);
    }
    mergedById.set(action.id, action);
  }

  for (const action of selectSessionScopedActionElements({ uiSchemaElements, uiType, context })) {
    if (!mergedById.has(action.id)) {
      orderedIds.push(action.id);
    }
    mergedById.set(action.id, action);
  }

  return orderedIds
    .map((id) => mergedById.get(id) ?? null)
    .filter((action): action is ActionUiElement => action !== null);
}