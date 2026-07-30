import React, { useMemo, useRef } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from '@crystal-lattice/frontend-sdk';
import {
  ApplicationActionForm,
  type ApplicationActionDialogFieldRenderers,
  type ApplicationActionFormHandle,
} from '@crystal-lattice/frontend-rn-components';

import { useTheme, type Theme } from '../theme';
import MarkdownMessageContent from './MarkdownMessageContent';

export interface ActionDisplayCardProps {
  display: ActionDisplayPayload;
  onDismiss?: () => void;
  onFollowupAction?: (
    action: ActionDisplayFollowupAction,
    formValues?: Record<string, any>,
  ) => void;
  activeActionId?: string | null;
  variantLabel?: string;
  footerDismissLabel?: string | null;
  compact?: boolean;
  fieldRenderers?: ApplicationActionDialogFieldRenderers;
}

const ActionDisplayCard: React.FC<ActionDisplayCardProps> = ({
  display,
  onDismiss,
  onFollowupAction,
  activeActionId,
  variantLabel,
  footerDismissLabel,
  compact = false,
  fieldRenderers,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, compact), [theme, compact]);
  const formRef = useRef<ApplicationActionFormHandle | null>(null);

  const body = display.body ?? '';
  const title = display.title ?? 'Action Result';
  const actions = Array.isArray(display.actions) ? display.actions : [];
  const dismissible = display.dismissible !== false;
  const form = display.form && typeof display.form === 'object' ? display.form : null;

  const handleActionPress = (action: ActionDisplayFollowupAction) => {
    if (action.kind === 'dismiss') {
      onDismiss?.();
      return;
    }

    if (action.kind === 'run_action' && form) {
      const formValues = formRef.current?.submit();
      if (formValues === null) {
        return;
      }
      onFollowupAction?.(action, formValues ?? {});
      return;
    }

    onFollowupAction?.(action);
  };

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>{title}</Text>
          {variantLabel ? <Text style={styles.variant}>{variantLabel}</Text> : null}
        </View>
        {dismissible && onDismiss ? (
          <TouchableOpacity style={styles.headerDismiss} onPress={onDismiss}>
            <Text style={styles.headerDismissText}>Close</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <ScrollView style={styles.bodyScroll} contentContainerStyle={styles.bodyContent}>
        {display.format === 'text' ? (
          <Text style={styles.bodyText}>{body}</Text>
        ) : (
          <MarkdownMessageContent text={body} variant="assistant" />
        )}
      </ScrollView>

      {form ? (
        <ApplicationActionForm
          ref={formRef}
          form={form}
          fieldRenderers={fieldRenderers}
          style={styles.formContainer}
        />
      ) : null}

      {actions.length > 0 ? (
        <View style={styles.actionsRow}>
          {actions.map((action) => {
            const loading = activeActionId === action.id;
            return (
              <TouchableOpacity
                key={action.id}
                style={[styles.actionButton, loading && styles.actionButtonDisabled]}
                onPress={() => handleActionPress(action)}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator size="small" color={theme.textOnPrimary} />
                ) : (
                  <Text style={styles.actionButtonText}>{action.label}</Text>
                )}
              </TouchableOpacity>
            );
          })}
        </View>
      ) : null}

      {footerDismissLabel ? (
        <View style={styles.footer}>
          <TouchableOpacity style={[styles.actionButton, styles.footerButton]} onPress={onDismiss}>
            <Text style={styles.actionButtonText}>{footerDismissLabel}</Text>
          </TouchableOpacity>
        </View>
      ) : null}
    </View>
  );
};

const createStyles = (theme: Theme, compact: boolean) =>
  StyleSheet.create({
    card: {
      borderRadius: 16,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      padding: compact ? 14 : 18,
    },
    header: {
      marginBottom: 12,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      gap: 12,
    },
    headerText: {
      flex: 1,
      flexDirection: 'column',
    },
    title: {
      fontSize: compact ? 16 : 18,
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
    headerDismiss: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.background,
      borderWidth: 1,
      borderColor: theme.border,
    },
    headerDismissText: {
      fontSize: 13,
      fontWeight: '600',
      color: theme.textSecondary,
    },
    bodyScroll: {
      flexGrow: 0,
      maxHeight: compact ? 220 : undefined,
    },
    bodyContent: {
      paddingBottom: 8,
    },
    bodyText: {
      fontSize: 14,
      lineHeight: 20,
      color: theme.text,
    },
    actionsRow: {
      marginTop: 8,
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 10,
    },
    formContainer: {
      marginTop: 8,
    },
    actionButton: {
      minWidth: 120,
      borderRadius: 10,
      paddingHorizontal: 16,
      paddingVertical: 10,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.primary,
    },
    actionButtonDisabled: {
      opacity: 0.75,
    },
    actionButtonText: {
      color: theme.textOnPrimary,
      fontSize: 14,
      fontWeight: '600',
    },
    footer: {
      marginTop: 16,
      alignItems: 'flex-end',
    },
    footerButton: {
      minWidth: 120,
    },
  });

export default ActionDisplayCard;