import React, { useMemo } from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';

import type { ActionDisplayPayload } from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from '../theme';
import MarkdownMessageContent from './MarkdownMessageContent';

export interface ActionResultModalProps {
  visible: boolean;
  display: ActionDisplayPayload | null;
  onRequestClose: () => void;
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
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const body = display?.body ?? '';
  const title = display?.title ?? 'Action Result';
  const variant = display?.variant ?? 'info';

  return (
    <Modal
      visible={visible && !!display}
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <TouchableWithoutFeedback onPress={onRequestClose}>
        <View style={styles.overlay}>
          <TouchableWithoutFeedback onPress={() => {}}>
            <View style={styles.panel}>
              <View style={styles.header}>
                <View style={styles.headerText}>
                  <Text style={styles.title}>{title}</Text>
                  <Text style={styles.variant}>{VARIANT_LABELS[variant]}</Text>
                </View>
              </View>

              <ScrollView style={styles.bodyScroll} contentContainerStyle={styles.bodyContent}>
                {display?.format === 'text' ? (
                  <Text style={styles.bodyText}>{body}</Text>
                ) : (
                  <MarkdownMessageContent text={body} variant="assistant" />
                )}
              </ScrollView>

              <View style={styles.footer}>
                <TouchableOpacity
                  style={[styles.button, styles.primaryButton]}
                  onPress={onRequestClose}
                >
                  <Text style={styles.buttonText}>Close</Text>
                </TouchableOpacity>
              </View>
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
      borderRadius: 16,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      padding: 18,
    },
    header: {
      marginBottom: 12,
    },
    headerText: {
      flexDirection: 'column',
    },
    title: {
      fontSize: 18,
      fontWeight: '700',
      color: theme.text,
    },
    variant: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.textSecondary,
      textTransform: 'uppercase',
      letterSpacing: 0.8,
      marginTop: 4,
    },
    bodyScroll: {
      flexGrow: 0,
    },
    bodyContent: {
      paddingBottom: 8,
    },
    bodyText: {
      fontSize: 14,
      lineHeight: 20,
      color: theme.text,
    },
    footer: {
      marginTop: 16,
      alignItems: 'flex-end',
    },
    button: {
      minWidth: 120,
      borderRadius: 10,
      paddingHorizontal: 16,
      paddingVertical: 10,
      alignItems: 'center',
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: 15,
      fontWeight: '600',
    },
  });

export default ActionResultModal;