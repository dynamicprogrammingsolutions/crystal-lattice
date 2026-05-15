import React, { useMemo } from 'react';
import {
  Modal,
  StyleSheet,
  TouchableWithoutFeedback,
  View,
} from 'react-native';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from '../theme';
import ActionDisplayCard from './ActionDisplayCard';

export interface ActionResultModalProps {
  visible: boolean;
  display: ActionDisplayPayload | null;
  onRequestClose: () => void;
  onFollowupAction?: (action: ActionDisplayFollowupAction) => void;
  activeActionId?: string | null;
}

const VARIANT_LABELS: Record<NonNullable<ActionDisplayPayload['variant']>, string> = {
  info: 'Info',
  success: 'Success',
  warning: 'Warning',
  error: 'Error',
};

const ActionResultModal: React.FC<ActionResultModalProps> = ({
  visible,
  display,
  onRequestClose,
  onFollowupAction,
  activeActionId,
}) => {
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
      <TouchableWithoutFeedback onPress={dismissible ? onRequestClose : undefined}>
        <View style={styles.overlay}>
          <TouchableWithoutFeedback onPress={() => {}}>
            <View style={styles.panel}>
              {display ? (
                <ActionDisplayCard
                  display={display}
                  onDismiss={onRequestClose}
                  onFollowupAction={onFollowupAction}
                  activeActionId={activeActionId}
                  variantLabel={VARIANT_LABELS[variant]}
                  footerDismissLabel={null}
                />
              ) : null}
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      flex: 1,
      backgroundColor: 'rgba(0, 0, 0, 0.35)',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
    },
    panel: {
      width: '100%',
      maxWidth: 560,
      maxHeight: '80%',
      justifyContent: 'center',
    },
  });

export default ActionResultModal;