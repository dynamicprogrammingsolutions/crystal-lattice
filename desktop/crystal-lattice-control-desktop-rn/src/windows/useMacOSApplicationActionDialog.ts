import { useCallback, useEffect, useMemo } from 'react';
import { Platform } from 'react-native';

import { getLastActionsPopoverAnchorTag } from '@crystal-lattice/frontend-rn-components';
import type { ActionUiElement } from '@crystal-lattice/frontend-sdk';

import {
  clearActiveApplicationActionDialog,
  getActiveApplicationActionDialog,
  setActiveApplicationActionDialog,
} from './applicationActionDialogCoordinator';
import { APPLICATION_ACTION_DIALOG_PRESENTATION } from './applicationActionDialogPresentation';
import { DesktopWindowManager, desktopWindowEvents } from './desktopWindowManager';

const DEBUG_ACTION_DIALOG = (globalThis as any).CLC_DEBUG_ACTION_DIALOG === true;

function calculatePopoverHeight(dialog: any): number {
  const dialogInputs = Array.isArray(dialog?.inputs) ? dialog.inputs : [];
  const padding = 24;
  const titleBlock = 34;
  const messageBlock = typeof dialog?.message === 'string' && dialog.message ? 16 : 0;
  const buttonsBlock = 52;
  const fieldHeights = dialogInputs.reduce((sum: number, input: any) => {
    const type = typeof input?.type === 'string' ? input.type : 'string';
    const description = typeof input?.description === 'string' ? input.description : '';
    const descriptionExtra = description ? 18 : 0;
    if (type === 'multiline') {
      return sum + 138 + descriptionExtra;
    }
    return sum + 66 + descriptionExtra;
  }, 0);

  return Math.max(80, Math.min(640, padding + titleBlock + messageBlock + fieldHeights + buttonsBlock));
}

export interface UseMacOSApplicationActionDialogOptions {
  ownerId: string;
  activeElement: ActionUiElement | null;
  prefillContext?: any;
  onSubmit: (payload: { values: Record<string, any>; buttonId?: string }) => void | Promise<void>;
  onCancel: () => void;
}

export function useMacOSApplicationActionDialog({
  ownerId,
  activeElement,
  prefillContext,
  onSubmit,
  onCancel,
}: UseMacOSApplicationActionDialogOptions): void {
  const ownerPrefix = useMemo(() => `${ownerId}:`, [ownerId]);

  const closeNativeDialog = useCallback(() => {
    if (DEBUG_ACTION_DIALOG) {
      console.log('[action-dialog] closeNativeDialog', { ownerId });
    }
    DesktopWindowManager?.closeApplicationActionDialogPopover();
    DesktopWindowManager?.closeApplicationActionDialogWindow();
  }, [ownerId]);

  useEffect(() => {
    if (Platform.OS !== 'macos') {
      return;
    }
    if (!desktopWindowEvents) {
      return;
    }

    const sub = desktopWindowEvents.addListener('applicationActionDialogCancelled', () => {
      const active = getActiveApplicationActionDialog();
      if (!active) {
        return;
      }
      if (!active.state.id.startsWith(ownerPrefix)) {
        return;
      }

      clearActiveApplicationActionDialog(active.state.id);
      closeNativeDialog();
      onCancel();
    });

    return () => {
      sub.remove();
    };
  }, [closeNativeDialog, onCancel, ownerPrefix]);

  useEffect(() => {
    if (Platform.OS !== 'macos') {
      return;
    }

    const dialog: any = (activeElement as any)?.dialog;
    const kind: string = dialog && typeof dialog.kind === 'string' ? dialog.kind : 'none';

    const existing = getActiveApplicationActionDialog();

    if (!activeElement || !dialog || kind === 'none') {
      if (existing) {
        if (existing.state.id.startsWith(ownerPrefix)) {
          clearActiveApplicationActionDialog(existing.state.id);
          closeNativeDialog();
        }
        return;
      }

      // Match the previous behavior: if there is no active dialog state,
      // still close any leftover window/popover.
      closeNativeDialog();
      return;
    }

    const dialogId = `${ownerPrefix}${activeElement.id}`;

    if (DEBUG_ACTION_DIALOG) {
      console.log('[action-dialog] present', {
        ownerId,
        dialogId,
        kind,
        presentation: APPLICATION_ACTION_DIALOG_PRESENTATION,
      });
    }

    if (existing && existing.state.id !== dialogId) {
      try {
        existing.handlers.onCancel();
      } catch {
      }
      clearActiveApplicationActionDialog(existing.state.id);
    }

    setActiveApplicationActionDialog({
      state: {
        id: dialogId,
        dialog,
        titleFallback: activeElement.label,
        prefillContext,
      },
      handlers: {
        onCancel,
        onSubmit: async (payload) => {
          await onSubmit(payload);
        },
      },
    });

    const title = activeElement.label;

    // Ensure the native view is fresh (avoid window reuse / leftover contents).
    closeNativeDialog();

    if (APPLICATION_ACTION_DIALOG_PRESENTATION === 'window') {
      DesktopWindowManager?.openApplicationActionDialogWindow({ title });
      return;
    }

    const anchorTag = getLastActionsPopoverAnchorTag();
    const height = calculatePopoverHeight(dialog);

    if (DEBUG_ACTION_DIALOG) {
      console.log('[action-dialog] openPopover', {
        ownerId,
        dialogId,
        anchorTag,
        width: 420,
        height,
      });
    }

    DesktopWindowManager?.openApplicationActionDialogPopover({
      anchorTag: typeof anchorTag === 'number' ? anchorTag : undefined,
      width: 420,
      height,
    });
  }, [activeElement, closeNativeDialog, onCancel, onSubmit, ownerPrefix, prefillContext]);

  useEffect(() => {
    return () => {
      if (Platform.OS !== 'macos') {
        return;
      }
      const active = getActiveApplicationActionDialog();
      if (active && active.state.id.startsWith(ownerPrefix)) {
        clearActiveApplicationActionDialog(active.state.id);
        closeNativeDialog();
      }
    };
  }, [closeNativeDialog, ownerPrefix]);
}
