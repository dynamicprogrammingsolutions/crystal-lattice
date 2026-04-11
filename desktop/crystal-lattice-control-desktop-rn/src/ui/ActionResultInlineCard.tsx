import React, { useMemo } from 'react';
import { StyleSheet, View } from 'react-native';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from '@crystal-lattice/frontend-sdk';
import { useTheme } from '@crystal-lattice/frontend-rn-components';

import { ActionDisplayCard } from './ActionDisplayCard';

export interface ActionResultInlineCardProps {
  display: ActionDisplayPayload;
  onDismiss: () => void;
  onFollowupAction?: (action: ActionDisplayFollowupAction) => void;
  activeActionId?: string | null;
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
}: ActionResultInlineCardProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const variant = display.variant ?? 'info';

  return (
    <View style={styles.wrapper}>
      <ActionDisplayCard
        display={display}
        onDismiss={onDismiss}
        onFollowupAction={onFollowupAction}
        activeActionId={activeActionId}
        variantLabel={VARIANT_LABELS[variant]}
        compact
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
  });