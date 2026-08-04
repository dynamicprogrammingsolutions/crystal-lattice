import React, { useMemo } from 'react';
import {
  Modal,
  StyleSheet,
  Pressable,
} from 'react-native';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from '@crystal-lattice/frontend-sdk';
import {
  type ApplicationActionDialogFieldRenderers,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import { ActionDisplayCard } from './ActionDisplayCard';

export interface ActionResultModalProps {
  visible: boolean;
  display: ActionDisplayPayload | null;
  onRequestClose: () => void;
  onFollowupAction?: (
    action: ActionDisplayFollowupAction,
    formValues?: Record<string, any>,
  ) => void;
  activeActionId?: string | null;
  fieldRenderers?: ApplicationActionDialogFieldRenderers;
}

const VARIANT_LABELS: Record<NonNullable<ActionDisplayPayload['variant']>, string> = {
  info: 'Info',
  success: 'Success',
  warning: 'Warning',
  error: 'Error',
};

export function ActionResultModal({
  visible,
  display,
  onRequestClose,
  onFollowupAction,
  activeActionId,
  fieldRenderers,
}: ActionResultModalProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const variant = display?.variant ?? 'info';
  const dismissible = display?.dismissible !== false;

  return (
    <Modal
      visible={visible && !!display}
      transparent
      animationType="fade"
      onRequestClose={dismissible ? onRequestClose : () => {}}
    >
      <Pressable style={styles.overlay} onPress={dismissible ? onRequestClose : undefined}>
        <Pressable style={styles.panel} onPress={() => {}}>
          {display ? (
            <ActionDisplayCard
              display={display}
              onDismiss={onRequestClose}
              onFollowupAction={onFollowupAction}
              activeActionId={activeActionId}
              variantLabel={VARIANT_LABELS[variant]}
              footerDismissLabel={null}
              fieldRenderers={fieldRenderers}
            />
          ) : null}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const createStyles = (_theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    overlay: {
      flex: 1,
      backgroundColor: 'rgba(0, 0, 0, 0.35)',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 24,
    },
    panel: {
      width: '100%',
      maxWidth: 620,
      maxHeight: '82%',
      justifyContent: 'center',
    },
  });