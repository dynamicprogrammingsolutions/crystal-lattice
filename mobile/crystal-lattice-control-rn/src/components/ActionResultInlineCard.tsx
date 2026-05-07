import React, { useMemo } from 'react';
import { StyleSheet, View } from 'react-native';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
} from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from '../theme';
import ActionDisplayCard from './ActionDisplayCard';

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

const ActionResultInlineCard: React.FC<ActionResultInlineCardProps> = ({
  display,
  onDismiss,
  onFollowupAction,
  activeActionId,
}) => {
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
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    wrapper: {
      marginHorizontal: 16,
      marginTop: 12,
      marginBottom: 4,
      shadowColor: theme.shadow,
      shadowOpacity: 0.12,
      shadowRadius: 10,
      shadowOffset: { width: 0, height: 4 },
      elevation: 3,
    },
  });

export default ActionResultInlineCard;