import React, { useMemo, useRef } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  Pressable,
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
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import MarkdownMessageContent from '../chat/MarkdownMessageContent';

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

export function ActionDisplayCard({
  display,
  onDismiss,
  onFollowupAction,
  activeActionId,
  variantLabel,
  footerDismissLabel,
  compact = false,
  fieldRenderers,
}: ActionDisplayCardProps): React.JSX.Element {
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
          <Pressable style={styles.headerDismiss} onPress={onDismiss}>
            <Text style={styles.headerDismissText}>Close</Text>
          </Pressable>
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
              <Pressable
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
              </Pressable>
            );
          })}
        </View>
      ) : null}

      {footerDismissLabel ? (
        <View style={styles.footer}>
          <Pressable style={[styles.actionButton, styles.footerButton]} onPress={onDismiss}>
            <Text style={styles.actionButtonText}>{footerDismissLabel}</Text>
          </Pressable>
        </View>
      ) : null}
    </View>
  );
}

const createStyles = (theme: ReturnType<typeof useTheme>, compact: boolean) =>
  StyleSheet.create({
    card: {
      borderRadius: 14,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
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
    },
    title: {
      fontSize: compact ? 16 : 18,
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
    headerDismiss: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.background,
    },
    headerDismissText: {
      fontSize: 12,
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
      fontSize: 13,
      lineHeight: 19,
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