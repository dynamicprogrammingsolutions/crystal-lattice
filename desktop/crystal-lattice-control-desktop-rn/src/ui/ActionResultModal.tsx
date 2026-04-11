import React, { useMemo } from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  Pressable,
  View,
} from 'react-native';

import type { ActionDisplayPayload } from '@crystal-lattice/frontend-sdk';
import { useTheme } from '@crystal-lattice/frontend-rn-components';

import MarkdownMessageContent from '../chat/MarkdownMessageContent';

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

export function ActionResultModal({
  visible,
  display,
  onRequestClose,
}: ActionResultModalProps): React.JSX.Element {
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
      <Pressable style={styles.overlay} onPress={onRequestClose}>
        <Pressable style={styles.panel} onPress={() => {}}>
          <View style={styles.header}>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.variant}>{VARIANT_LABELS[variant]}</Text>
          </View>

          <ScrollView style={styles.bodyScroll} contentContainerStyle={styles.bodyContent}>
            {display?.format === 'text' ? (
              <Text style={styles.bodyText}>{body}</Text>
            ) : (
              <MarkdownMessageContent text={body} variant="assistant" />
            )}
          </ScrollView>

          <View style={styles.footer}>
            <Pressable style={styles.button} onPress={onRequestClose}>
              <Text style={styles.buttonText}>Close</Text>
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const createStyles = (theme: ReturnType<typeof useTheme>) =>
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
      borderRadius: 14,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      padding: 18,
    },
    header: {
      marginBottom: 12,
    },
    title: {
      fontSize: 18,
      fontWeight: '700',
      color: theme.text,
      marginBottom: 4,
    },
    variant: {
      fontSize: 11,
      fontWeight: '700',
      textTransform: 'uppercase',
      letterSpacing: 0.8,
      color: theme.textSecondary,
    },
    bodyScroll: {
      flexGrow: 0,
    },
    bodyContent: {
      paddingBottom: 8,
    },
    bodyText: {
      fontSize: 13,
      lineHeight: 19,
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
      backgroundColor: theme.primary,
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: 14,
      fontWeight: '600',
    },
  });