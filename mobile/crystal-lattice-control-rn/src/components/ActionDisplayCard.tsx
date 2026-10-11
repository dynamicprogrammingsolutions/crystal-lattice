import React, { useMemo, useRef, useState } from 'react';
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
  useActionFormScroll,
  type ApplicationActionDialogFieldRenderers,
  type ApplicationActionFormHandle,
} from '@crystal-lattice/frontend-rn-components';

import { useTheme, type Theme } from '../theme';
import ConfiguredMarkdownMessageContent from './ConfiguredMarkdownMessageContent';

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
  bounded?: boolean;
  bodyTestID?: string;
  fieldRenderers?: ApplicationActionDialogFieldRenderers;
  maxHeight?: number;
}

const ActionDisplayCard: React.FC<ActionDisplayCardProps> = ({
  display,
  onDismiss,
  onFollowupAction,
  activeActionId,
  variantLabel,
  footerDismissLabel,
  compact = false,
  bounded = false,
  bodyTestID,
  fieldRenderers,
  maxHeight,
}) => {
  const theme = useTheme();
  const shortViewport = maxHeight !== undefined && maxHeight < 260;
  const styles = useMemo(
    () => createStyles(theme, compact, bounded, shortViewport),
    [theme, compact, bounded, shortViewport],
  );
  const formRef = useRef<ApplicationActionFormHandle | null>(null);
  const formScroll = useActionFormScroll();
  const [headerHeight, setHeaderHeight] = useState(0);
  const [actionsHeight, setActionsHeight] = useState(0);
  const [footerHeight, setFooterHeight] = useState(0);
  const [formHeight, setFormHeight] = useState<number | undefined>();

  const body = display.body ?? '';
  const title = display.title ?? 'Action Result';
  const actions = Array.isArray(display.actions) ? display.actions : [];
  const dismissible = display.dismissible !== false;
  const form = display.form && typeof display.form === 'object' ? display.form : null;
  const availableContentHeight =
    maxHeight === undefined
      ? undefined
      : Math.max(
          0,
          maxHeight -
            (shortViewport ? 16 : compact ? 28 : 36) -
            headerHeight -
            (shortViewport ? 4 : 12) -
            (actions.length ? actionsHeight + (shortViewport ? 4 : 8) : 0) -
            (footerDismissLabel ? footerHeight + 16 : 0),
        );
  const formMaxHeight =
    availableContentHeight === undefined
      ? undefined
      : Math.max(
          0,
          Math.min(
            availableContentHeight - theme.typography.lineHeight.normal,
            Math.max(40, availableContentHeight / 3),
          ),
        );
  const bodyMaxHeight =
    availableContentHeight === undefined
      ? undefined
      : availableContentHeight -
        (form ? Math.min(formHeight ?? formMaxHeight!, formMaxHeight!) : 0);
  const formContent = form ? (
    <ApplicationActionForm
      ref={formRef}
      form={form}
      fieldRenderers={fieldRenderers}
      onFieldFocus={formScroll.onFieldFocus}
      style={maxHeight === undefined ? styles.formContainer : undefined}
    />
  ) : null;

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
    <View
      testID="action-result-card"
      style={[styles.card, maxHeight !== undefined && { maxHeight }]}
    >
      <View
        testID="action-result-header"
        style={styles.header}
        onLayout={(event) => setHeaderHeight(event.nativeEvent.layout.height)}
      >
        <View style={[styles.headerText, maxHeight !== undefined && styles.viewportHeaderText]}>
          <Text style={[styles.title, maxHeight !== undefined && styles.viewportTitle]}>
            {title}
          </Text>
          {variantLabel ? (
            <Text style={[styles.variant, maxHeight !== undefined && styles.viewportVariant]}>
              {variantLabel}
            </Text>
          ) : null}
        </View>
        {dismissible && onDismiss ? (
          <TouchableOpacity
            testID="action-result-close"
            accessibilityRole="button"
            style={styles.headerDismiss}
            onPress={onDismiss}
          >
            <Text style={styles.headerDismissText}>Close</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <ScrollView
        testID={bodyTestID}
        style={[styles.bodyScroll, bodyMaxHeight !== undefined && { maxHeight: bodyMaxHeight }]}
        contentContainerStyle={styles.bodyContent}
        nestedScrollEnabled
        contentInsetAdjustmentBehavior="never"
      >
        {display.format === 'text' ? (
          <Text style={styles.bodyText}>{body}</Text>
        ) : (
          <ConfiguredMarkdownMessageContent
            text={body}
            variant="assistant"
            testID={bodyTestID ? `${bodyTestID}-content` : undefined}
          />
        )}
      </ScrollView>

      {form ? (
        maxHeight === undefined ? (
          formContent
        ) : (
          <ScrollView
            ref={formScroll.scrollRef}
            testID={`${bodyTestID ?? 'action-result-body'}-form`}
            style={[styles.formScroll, formMaxHeight !== undefined && { maxHeight: formMaxHeight }]}
            contentContainerStyle={styles.formContainer}
            onContentSizeChange={(_width, height) => setFormHeight(height)}
            keyboardShouldPersistTaps="handled"
            nestedScrollEnabled
            removeClippedSubviews={false}
            contentInsetAdjustmentBehavior="never"
            onLayout={formScroll.onLayout}
            onScroll={formScroll.onScroll}
            scrollEventThrottle={16}
          >
            {formContent}
          </ScrollView>
        )
      ) : null}

      {actions.length > 0 ? (
        <View
          testID="action-result-controls"
          style={styles.actionsRow}
          onLayout={(event) => setActionsHeight(event.nativeEvent.layout.height)}
        >
          {actions.map((action) => {
            const loading = activeActionId === action.id;
            return (
              <TouchableOpacity
                key={action.id}
                testID={`action-display-action-${action.id}`}
                accessibilityRole="button"
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
        <View
          style={styles.footer}
          onLayout={(event) => setFooterHeight(event.nativeEvent.layout.height)}
        >
          <TouchableOpacity style={[styles.actionButton, styles.footerButton]} onPress={onDismiss}>
            <Text style={styles.actionButtonText}>{footerDismissLabel}</Text>
          </TouchableOpacity>
        </View>
      ) : null}
    </View>
  );
};

const createStyles = (theme: Theme, compact: boolean, bounded: boolean, shortViewport: boolean) =>
  StyleSheet.create({
    card: {
      borderRadius: 16,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      paddingHorizontal: compact ? 14 : 18,
      paddingVertical: shortViewport ? 8 : compact ? 14 : 18,
      flexShrink: bounded ? 1 : 0,
      maxHeight: bounded ? '100%' : undefined,
    },
    header: {
      marginBottom: shortViewport ? 4 : 12,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      gap: 12,
      flexShrink: 0,
    },
    headerText: {
      flex: 1,
      flexDirection: 'column',
    },
    viewportHeaderText: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      alignItems: 'center',
      columnGap: 8,
    },
    viewportTitle: {
      flexShrink: 1,
    },
    viewportVariant: {
      marginTop: 0,
    },
    title: {
      fontSize: compact ? 16 : 18,
      fontWeight: '700',
      color: theme.text,
    },
    variant: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '600',
      color: theme.textSecondary,
      textTransform: 'uppercase',
      letterSpacing: 0.8,
      marginTop: 4,
    },
    headerDismiss: {
      paddingHorizontal: 10,
      paddingVertical: shortViewport ? 4 : 6,
      borderRadius: 8,
      backgroundColor: theme.background,
      borderWidth: 1,
      borderColor: theme.border,
    },
    headerDismissText: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '600',
      color: theme.textSecondary,
    },
    bodyScroll: {
      flexGrow: 0,
      flexShrink: bounded ? 1 : 0,
      maxHeight: compact ? 220 : bounded ? 420 : undefined,
    },
    bodyContent: {
      paddingBottom: 8,
    },
    bodyText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
    },
    actionsRow: {
      marginTop: shortViewport ? 4 : 8,
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 10,
      flexShrink: 0,
    },
    formContainer: {
      paddingTop: 8,
    },
    formScroll: {
      flexGrow: 0,
      flexShrink: 0,
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
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    footer: {
      marginTop: 16,
      alignItems: 'flex-end',
      flexShrink: 0,
    },
    footerButton: {
      minWidth: 120,
    },
  });

export default ActionDisplayCard;
