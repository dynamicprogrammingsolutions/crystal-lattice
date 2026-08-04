import type {
  ApplicationActionDefinition,
  ApplicationActionUiElement,
  ApplicationUiElement,
} from '../types/plugins';

export interface ApplicationActionDiagnostic {
  code: 'invalid_application_action' | 'missing_application_action_definition';
  message: string;
  plugin?: string;
  elementId?: string;
  actionId?: string;
}

export function applicationActionKey(pluginId: string, actionId: string): string {
  return `${pluginId}\u0000${actionId}`;
}

export function buildApplicationActionsByKey(
  actions: readonly ApplicationActionDefinition[],
): Record<string, ApplicationActionDefinition> {
  const byKey: Record<string, ApplicationActionDefinition> = {};
  for (const action of actions) {
    if (
      !action ||
      typeof action.plugin !== 'string' ||
      !action.plugin ||
      typeof action.id !== 'string' ||
      !action.id
    ) {
      continue;
    }
    byKey[applicationActionKey(action.plugin, action.id)] = action;
  }
  return byKey;
}

export function normalizeApplicationActionElements(options: {
  elements: readonly ApplicationUiElement[];
  actionsByKey: Record<string, ApplicationActionDefinition>;
}): {
  actions: ApplicationActionUiElement[];
  diagnostics: ApplicationActionDiagnostic[];
} {
  const actions: ApplicationActionUiElement[] = [];
  const diagnostics: ApplicationActionDiagnostic[] = [];

  for (const raw of options.elements) {
    if (!raw || (raw as any).ui_type !== 'application_action') continue;
    const plugin = (raw as any).plugin;
    const elementId = (raw as any).id;
    const label = (raw as any).label;
    const actionId = (raw as any).action_id;
    if (
      typeof plugin !== 'string' ||
      !plugin ||
      typeof elementId !== 'string' ||
      !elementId ||
      typeof label !== 'string' ||
      !label ||
      typeof actionId !== 'string' ||
      !actionId
    ) {
      diagnostics.push({
        code: 'invalid_application_action',
        message:
          'application_action requires non-empty plugin, id, label, and action_id fields.',
        plugin: typeof plugin === 'string' ? plugin : undefined,
        elementId: typeof elementId === 'string' ? elementId : undefined,
        actionId: typeof actionId === 'string' ? actionId : undefined,
      });
      continue;
    }
    if (!options.actionsByKey[applicationActionKey(plugin, actionId)]) {
      diagnostics.push({
        code: 'missing_application_action_definition',
        message: `No application action definition exists for ${plugin}/${actionId}.`,
        plugin,
        elementId,
        actionId,
      });
      continue;
    }
    actions.push(raw as ApplicationActionUiElement);
  }

  actions.sort((left, right) => (left.order ?? 0) - (right.order ?? 0));
  return { actions, diagnostics };
}