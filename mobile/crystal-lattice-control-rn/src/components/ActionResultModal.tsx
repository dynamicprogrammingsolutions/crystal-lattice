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
import type { ApplicationActionDialogFieldRenderers } from '@crystal-lattice/frontend-rn-components';

import { useTheme, type Theme } from '../theme';
import ActionDisplayCard from './ActionDisplayCard';

export interface ActionResultModalProps {
  visible: boolean;
  display: ActionDisplayPayload | null;
  onRequestClose: () => void;
  presentationMode?: 'native' | 'overlay';
  testID?: string;
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

const ActionResultModal: React.FC<ActionResultModalProps> = ({
  visible,
  display,
  onRequestClose,
  presentationMode = 'native',
  testID,
  onFollowupAction,
  activeActionId,
  fieldRenderers,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const variant = display?.variant ?? 'info';
  const dismissible = display?.dismissible !== false;
  const content = (
    <TouchableWithoutFeedback onPress={dismissible ? onRequestClose : undefined}>
      <View
        testID={testID}
        accessibilityViewIsModal
        style={[
          styles.overlay,
          presentationMode === 'overlay' && styles.absoluteOverlay,
        ]}
      >
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
                fieldRenderers={fieldRenderers}
              />
            ) : null}
          </View>
        </TouchableWithoutFeedback>
      </View>
    </TouchableWithoutFeedback>
  );

  if (!visible || !display) {
    return null;
  }

  if (presentationMode === 'overlay') {
    return content;
  }

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      onRequestClose={dismissible ? onRequestClose : () => {}}
    >
      {content}
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
    absoluteOverlay: {
      ...StyleSheet.absoluteFillObject,
      zIndex: 20000,
      elevation: 20000,
    },
    panel: {
      width: '100%',
      maxWidth: 560,
      maxHeight: '80%',
      justifyContent: 'center',
    },
  });

export default ActionResultModal;