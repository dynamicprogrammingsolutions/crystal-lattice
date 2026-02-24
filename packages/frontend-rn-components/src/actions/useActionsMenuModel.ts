import { useCallback, useEffect, useMemo, useRef } from 'react';

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
  const pinnedRef = useRef(options.pinned);

  useEffect(() => {
    pinnedRef.current = options.pinned;
  }, [options.pinned]);

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
      const next = togglePinnedKey(pinnedRef.current, key);
      pinnedRef.current = next;
      options.onChangePinned(next);
    },
    [options.onChangePinned],
  );

  return { model, togglePinned };
}
