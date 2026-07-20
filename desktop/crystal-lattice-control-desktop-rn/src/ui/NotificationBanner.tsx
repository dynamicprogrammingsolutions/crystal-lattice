import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export type NotificationVariant = 'info' | 'success' | 'warning' | 'error';

export interface NotificationBannerProps {
  variant: NotificationVariant;
  title?: string;
  message?: string;
  onDismiss?: () => void | Promise<void>;
  dismissLabel?: string;
}

interface VariantColors {
  accent: string;
  background: string;
}

function useVariantColors(variant: NotificationVariant): VariantColors {
  const theme = useTheme();
  switch (variant) {
    case 'success':
      return { accent: theme.success, background: theme.successMuted };
    case 'warning':
      return { accent: theme.warning, background: theme.warningMuted };
    case 'error':
      return { accent: theme.danger, background: theme.dangerMuted };
    case 'info':
    default:
      return { accent: theme.notification, background: theme.notificationMuted };
  }
}

export function NotificationBanner({
  variant,
  title,
  message,
  onDismiss,
  dismissLabel = 'Dismiss',
}: NotificationBannerProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const colors = useVariantColors(variant);

  return (
    <View style={[styles.banner, { backgroundColor: colors.background, borderColor: colors.accent }]}>
      <View style={[styles.accentBar, { backgroundColor: colors.accent }]} />
      <View style={styles.content}>
        {title ? <Text style={styles.title} numberOfLines={1}>{title}</Text> : null}
        {message ? <Text style={styles.message}>{message}</Text> : null}
      </View>
      {onDismiss ? (
        <Pressable
          style={(state) => {
            const hovered = (state as any).hovered as boolean | undefined;
            return [
              styles.dismissButton,
              { borderColor: colors.accent },
              (hovered || state.pressed) && styles.dismissButtonPressed,
            ];
          }}
          onPress={() => {
            void onDismiss();
          }}
        >
          <Text style={styles.dismissText}>{dismissLabel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    banner: {
      flexDirection: 'row',
      alignItems: 'stretch',
      borderWidth: 1,
      borderRadius: 10,
      overflow: 'hidden',
    },
    accentBar: {
      width: 4,
    },
    content: {
      flex: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
      gap: 2,
    },
    title: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    message: {
      fontSize: 12,
      color: theme.text,
    },
    dismissButton: {
      borderWidth: 1,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      marginHorizontal: 10,
      marginVertical: 8,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.surface,
    },
    dismissButtonPressed: {
      opacity: 0.85,
    },
    dismissText: {
      fontSize: 11,
      fontWeight: '700',
      color: theme.text,
    },
  });
}