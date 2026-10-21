import { useCallback, useEffect, useRef } from 'react';
import {
  buildDisplayFollowupActionElement,
  type ActionDisplayPayload,
  type ActionDisplayRunActionAction,
  type ActionUiElement,
} from '@crystal-lattice/frontend-sdk';
import { usePluginActionDialog } from './usePluginActionDialog';

export interface DisplayFollowupDialogContext<Source> {
  action: ActionDisplayRunActionAction;
  source: Source;
  formValues?: Record<string, any>;
}

export function useDisplayFollowupDialog<Source>(
  execute: (
    element: ActionUiElement,
    context: DisplayFollowupDialogContext<Source>,
    dialogValues: Record<string, any> | undefined,
  ) => Promise<void>,
) {
  const executeRef = useRef(execute);
  useEffect(() => {
    executeRef.current = execute;
  }, [execute]);
  const runAction = useCallback(
    (
      element: ActionUiElement,
      context: DisplayFollowupDialogContext<Source>,
      values: Record<string, any> | undefined,
    ) => executeRef.current(element, context, values),
    [],
  );
  const dialog = usePluginActionDialog(runAction);
  const openForAction = useCallback(
    (
      action: ActionDisplayRunActionAction,
      display: ActionDisplayPayload,
      source: Source,
      formValues?: Record<string, any>,
    ) => {
      dialog.openForElement(buildDisplayFollowupActionElement(action, display), {
        action,
        source,
        formValues,
      });
    },
    [dialog.openForElement],
  );
  return { ...dialog, openForAction };
}