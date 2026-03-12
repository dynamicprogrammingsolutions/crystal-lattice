import type { ActionUiElement } from '../types/plugins';
import type { UiSchemaElement } from '../types/uiSchema';

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
}): ActionUiElement[] {
  const { uiSchemaElements, uiType } = options;
  return (uiSchemaElements || []).filter((element): element is ActionUiElement => {
    return isActionUiElement(element, uiType);
  });
}

export function mergeSessionScopedActionElements(options: {
  applicationActions: ActionUiElement[];
  uiSchemaElements: UiSchemaElement[];
  uiType: SessionScopedActionUiType;
}): ActionUiElement[] {
  const { applicationActions, uiSchemaElements, uiType } = options;

  const mergedById = new Map<string, ActionUiElement>();
  const orderedIds: string[] = [];

  for (const action of applicationActions || []) {
    if (!isActionUiElement(action, uiType)) {
      continue;
    }
    if (!mergedById.has(action.id)) {
      orderedIds.push(action.id);
    }
    mergedById.set(action.id, action);
  }

  for (const action of selectSessionScopedActionElements({ uiSchemaElements, uiType })) {
    if (!mergedById.has(action.id)) {
      orderedIds.push(action.id);
    }
    mergedById.set(action.id, action);
  }

  return orderedIds
    .map((id) => mergedById.get(id) ?? null)
    .filter((action): action is ActionUiElement => action !== null);
}