import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from '@crystal-lattice/frontend-sdk';
import {
  type ApplicationActionDialogFieldRenderers,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import { ActionDisplayCard } from './ActionDisplayCard';

export interface ActionResultInlineCardProps {
  display: ActionDisplayPayload;
  onDismiss: () => void;
  onFollowupAction?: (
    action: ActionDisplayFollowupAction,
    formValues?: Record<string, any>,
  ) => void;
  activeActionId?: string | null;
  fieldRenderers?: ApplicationActionDialogFieldRenderers;
  contextLabel?: string;
}

const VARIANT_LABELS: Record<NonNullable<ActionDisplayPayload['variant']>, string> = {
  info: 'Info',
  success: 'Success',
  warning: 'Warning',
  error: 'Error',
};

export function ActionResultInlineCard({
  display,
  onDismiss,
  onFollowupAction,
  activeActionId,
  fieldRenderers,
  contextLabel,
}: ActionResultInlineCardProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const variant = display.variant ?? 'info';

  return (
    <View style={styles.wrapper}>
      {contextLabel ? (
        <Text style={styles.contextLabel} numberOfLines={1}>
          {contextLabel}
        </Text>
      ) : null}
      <ActionDisplayCard
        display={display}
        onDismiss={onDismiss}
        onFollowupAction={onFollowupAction}
        activeActionId={activeActionId}
        variantLabel={VARIANT_LABELS[variant]}
        compact
        fieldRenderers={fieldRenderers}
      />
    </View>
  );
}

const createStyles = (theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    wrapper: {
      marginHorizontal: 12,
      marginBottom: 10,
      shadowColor: theme.shadow,
      shadowOpacity: 0.1,
      shadowRadius: 8,
      shadowOffset: { width: 0, height: 3 },
      elevation: 2,
    },
    contextLabel: {
      color: theme.textSecondary,
      fontSize: 11,
      fontWeight: '600',
      marginBottom: 4,
      marginHorizontal: 4,
    },
  });