import { useEffect, useMemo } from 'react';
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
  onSubmit: (values: Record<string, any>) => void | Promise<void>;
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
      DesktopWindowManager?.closeApplicationActionDialogPopover();
      DesktopWindowManager?.closeApplicationActionDialogWindow();
      onCancel();
    });

    return () => {
      sub.remove();
    };
  }, [onCancel, ownerPrefix]);

  useEffect(() => {
    if (Platform.OS !== 'macos') {
      return;
    }

    const dialog: any = (activeElement as any)?.dialog;
    const kind: string = dialog && typeof dialog.kind === 'string' ? dialog.kind : 'none';

    if (!activeElement || !dialog || kind === 'none') {
      const active = getActiveApplicationActionDialog();
      if (active && active.state.id.startsWith(ownerPrefix)) {
        clearActiveApplicationActionDialog(active.state.id);
        DesktopWindowManager?.closeApplicationActionDialogPopover();
        DesktopWindowManager?.closeApplicationActionDialogWindow();
      }
      return;
    }

    const dialogId = `${ownerPrefix}${activeElement.id}`;

    const existing = getActiveApplicationActionDialog();
    if (existing && existing.state.id !== dialogId) {
      try {
        existing.handlers.onCancel();
      } catch {
      }
      clearActiveApplicationActionDialog(existing.state.id);
      DesktopWindowManager?.closeApplicationActionDialogPopover();
      DesktopWindowManager?.closeApplicationActionDialogWindow();
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
        onSubmit: async (values) => {
          await onSubmit(values);
        },
      },
    });

    const title = activeElement.label;
    if (APPLICATION_ACTION_DIALOG_PRESENTATION === 'window') {
      DesktopWindowManager?.closeApplicationActionDialogPopover();
      DesktopWindowManager?.openApplicationActionDialogWindow({ title });
      return;
    }

    DesktopWindowManager?.closeApplicationActionDialogWindow();
    const anchorTag = getLastActionsPopoverAnchorTag();
    const height = calculatePopoverHeight(dialog);

    DesktopWindowManager?.openApplicationActionDialogPopover({
      anchorTag: typeof anchorTag === 'number' ? anchorTag : undefined,
      width: 420,
      height,
    });
  }, [activeElement, onCancel, onSubmit, ownerPrefix, prefillContext]);

  useEffect(() => {
    return () => {
      if (Platform.OS !== 'macos') {
        return;
      }
      const active = getActiveApplicationActionDialog();
      if (active && active.state.id.startsWith(ownerPrefix)) {
        clearActiveApplicationActionDialog(active.state.id);
        DesktopWindowManager?.closeApplicationActionDialogPopover();
        DesktopWindowManager?.closeApplicationActionDialogWindow();
      }
    };
  }, [ownerPrefix]);
}
