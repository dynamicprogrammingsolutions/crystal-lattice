import { useCallback, useState } from 'react';
import type { ActionUiElement } from '@crystal-lattice/frontend-sdk';

interface ActiveDialogState<Context> {
  element: ActionUiElement;
  context: Context;
}

export interface UsePluginActionDialogResult<Context> {
  activeElement: ActionUiElement | null;
  context: Context | null;
  openForElement: (element: ActionUiElement, context: Context) => void;
  handleSubmit: (values: Record<string, any>) => Promise<void>;
  handleCancel: () => void;
}

export function usePluginActionDialog<Context = any>(
  runAction: (
    element: ActionUiElement,
    context: Context,
    values: Record<string, any> | undefined,
  ) => Promise<void>,
): UsePluginActionDialogResult<Context> {
  const [active, setActive] = useState<ActiveDialogState<Context> | null>(null);

  const openForElement = useCallback(
    (element: ActionUiElement, context: Context) => {
      const dialog: any = (element as any).dialog || {};
      if (!dialog || dialog.kind === 'none') {
        runAction(element, context, undefined).catch(() => {
          // Errors are handled inside runAction.
        });
        return;
      }

      setActive({ element, context });
    },
    [runAction],
  );

  const handleSubmit = useCallback(
    async (values: Record<string, any>) => {
      const current = active;
      if (!current) return;
      setActive(null);
      await runAction(current.element, current.context, values);
    },
    [active, runAction],
  );

  const handleCancel = useCallback(() => {
    setActive(null);
  }, []);

  return {
    activeElement: active ? active.element : null,
    context: active ? active.context : null,
    openForElement,
    handleSubmit,
    handleCancel,
  };
}
