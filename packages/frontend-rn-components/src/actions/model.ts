import type { ActionDefinition, ActionKey, ActionsMenuModel } from './types';

export function limitPinnedActionsForBar<TDef>(
  actions: readonly TDef[],
  maximum: number | undefined,
): readonly TDef[] {
  if (maximum == null || !Number.isFinite(maximum)) {
    return actions;
  }
  return actions.slice(0, Math.max(0, Math.floor(maximum)));
}

export function togglePinnedKey(pinned: readonly ActionKey[], key: ActionKey): ActionKey[] {
  if (pinned.includes(key)) {
    return pinned.filter((k) => k !== key);
  }
  return [...pinned, key];
}

export function normalizeActionDefinitions<TDef extends ActionDefinition>(options: {
  baseActions: readonly TDef[];
  extraActions?: readonly TDef[];
  availableActions?: readonly ActionKey[];
}): {
  actionsByKey: Record<ActionKey, TDef>;
  orderedActions: TDef[];
} {
  const baseActions =
    options.availableActions && options.availableActions.length > 0
      ? options.baseActions.filter((def) => options.availableActions!.includes(def.key))
      : options.baseActions;

  const combined: TDef[] = [...baseActions, ...(options.extraActions ?? [])];

  const actionsByKey: Record<ActionKey, TDef> = Object.create(null);
  const seenKeys = new Set<ActionKey>();
  const orderedKeys: ActionKey[] = [];

  for (const def of combined) {
    if (!def || typeof def.key !== 'string') continue;
    actionsByKey[def.key] = def;
    if (!seenKeys.has(def.key)) {
      seenKeys.add(def.key);
      orderedKeys.push(def.key);
    }
  }

  const orderedActions = orderedKeys
    .map((key) => actionsByKey[key])
    .filter((def): def is TDef => Boolean(def));

  return { actionsByKey, orderedActions };
}

export function buildActionsMenuModel<TDef extends ActionDefinition>(options: {
  baseActions: readonly TDef[];
  extraActions?: readonly TDef[];
  availableActions?: readonly ActionKey[];
  pinned: readonly ActionKey[];
  isActionDisabled?: (key: ActionKey) => boolean;
}): ActionsMenuModel<TDef> {
  const isActionDisabled = options.isActionDisabled ?? (() => false);
  const { actionsByKey, orderedActions } = normalizeActionDefinitions({
    baseActions: options.baseActions,
    extraActions: options.extraActions,
    availableActions: options.availableActions,
  });

  const pinnedSet = new Set(options.pinned);
  const visiblePinned = orderedActions.filter((def) => pinnedSet.has(def.key));

  const visibleOverflow = orderedActions.filter((def) => !pinnedSet.has(def.key));

  return {
    actionsByKey,
    orderedActions,
    visiblePinned,
    visibleOverflow,
    isActionDisabled,
  };
}
