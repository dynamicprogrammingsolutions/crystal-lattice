import React, { useEffect, useMemo, useState } from 'react';
import {
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
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
  overlayChildren?: React.ReactNode;
  onOverlayRequestClose?: () => void;
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
  overlayChildren,
  onOverlayRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [viewportHeight, setViewportHeight] = useState<number | undefined>();
  const verticalPadding = viewportHeight !== undefined && viewportHeight < 260 ? 4 : 12;
  useEffect(() => {
    if (visible) Keyboard.dismiss();
  }, [visible]);

  const handleClose = () => {
    Keyboard.dismiss();
    onRequestClose();
  };

  const variant = display?.variant ?? 'info';
  const dismissible = display?.dismissible !== false;
  const content = (
    <KeyboardAvoidingView
      testID={testID}
      enabled={!overlayChildren}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      accessibilityViewIsModal={!overlayChildren}
      accessibilityElementsHidden={!!overlayChildren}
      importantForAccessibility={overlayChildren ? 'no-hide-descendants' : 'auto'}
      style={styles.overlay}
    >
      <Pressable
        accessible={false}
        style={StyleSheet.absoluteFill}
        onPress={dismissible ? handleClose : undefined}
      />
      <SafeAreaView style={styles.safeViewport} pointerEvents="box-none">
        <View
          testID="action-result-viewport"
          pointerEvents="box-none"
          style={[styles.viewport, { paddingVertical: verticalPadding }]}
          onLayout={(event) => setViewportHeight(event.nativeEvent.layout.height)}
        >
          <View style={styles.panel}>
            {display ? (
              <ActionDisplayCard
                display={display}
                onDismiss={handleClose}
                onFollowupAction={onFollowupAction}
                activeActionId={activeActionId}
                variantLabel={VARIANT_LABELS[variant]}
                footerDismissLabel={null}
                fieldRenderers={fieldRenderers}
                bounded
                bodyTestID={testID ? `${testID}-body` : 'action-result-body'}
                maxHeight={
                  viewportHeight === undefined
                    ? undefined
                    : Math.max(0, viewportHeight - verticalPadding * 2)
                }
              />
            ) : null}
          </View>
        </View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );

  if (!visible || !display) {
    return null;
  }

  if (presentationMode === 'overlay') {
    return (
      <View style={styles.absoluteOverlay}>
        {content}
        {overlayChildren}
      </View>
    );
  }

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      supportedOrientations={['portrait', 'landscape']}
      onRequestClose={
        overlayChildren && onOverlayRequestClose
          ? () => {
              Keyboard.dismiss();
              onOverlayRequestClose();
            }
          : dismissible
          ? handleClose
          : () => {}
      }
    >
      <View style={styles.modalRoot}>
        {content}
        {overlayChildren}
      </View>
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modalRoot: {
      flex: 1,
    },
    overlay: {
      flex: 1,
      backgroundColor: 'rgba(0, 0, 0, 0.35)',
    },
    safeViewport: {
      flex: 1,
    },
    viewport: {
      flex: 1,
      padding: 12,
      justifyContent: 'center',
      alignItems: 'center',
    },
    absoluteOverlay: {
      ...StyleSheet.absoluteFillObject,
      zIndex: 20000,
      elevation: 20000,
    },
    panel: {
      width: '100%',
      maxWidth: 560,
    },
  });

export default ActionResultModal;
