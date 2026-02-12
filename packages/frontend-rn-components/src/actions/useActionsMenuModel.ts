import { useCallback, useMemo } from 'react';

import { buildActionsMenuModel, togglePinnedKey } from './model';
import type { ActionDefinition, ActionKey, ActionsMenuModel } from './types';

export interface UseActionsMenuModelOptions<TDef extends ActionDefinition = ActionDefinition> {
  baseActions: readonly TDef[];
  extraActions?: readonly TDef[];
  availableActions?: readonly ActionKey[];
  pinned: readonly ActionKey[];
  onChangePinned?: (nextPinned: ActionKey[]) => void;
  isActionDisabled?: (key: ActionKey) => boolean;
}

export interface UseActionsMenuModelResult<TDef extends ActionDefinition = ActionDefinition> {
  model: ActionsMenuModel<TDef>;
  togglePinned: (key: ActionKey) => void;
}

export function useActionsMenuModel<TDef extends ActionDefinition>(
  options: UseActionsMenuModelOptions<TDef>,
): UseActionsMenuModelResult<TDef> {
  const model = useMemo(() => {
    return buildActionsMenuModel({
      baseActions: options.baseActions,
      extraActions: options.extraActions,
      availableActions: options.availableActions,
      pinned: options.pinned,
      isActionDisabled: options.isActionDisabled,
    });
  }, [
    options.baseActions,
    options.extraActions,
    options.availableActions,
    options.pinned,
    options.isActionDisabled,
  ]);

  const togglePinned = useCallback(
    (key: ActionKey) => {
      if (!options.onChangePinned) {
        return;
      }
      const next = togglePinnedKey(options.pinned, key);
      options.onChangePinned(next);
    },
    [options.pinned, options.onChangePinned],
  );

  return { model, togglePinned };
}
