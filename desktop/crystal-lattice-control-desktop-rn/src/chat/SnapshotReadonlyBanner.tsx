import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export interface SnapshotReadonlyBannerProps {
  snapshotId: string;
  onClear: () => void | Promise<void>;
  disabled?: boolean;
}

export function SnapshotReadonlyBanner({
  snapshotId,
  onClear,
  disabled,
}: SnapshotReadonlyBannerProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View style={styles.banner}>
      <Text style={styles.text} numberOfLines={1}>
        Viewing snapshot {snapshotId} · Read-only
      </Text>
      <Pressable
        style={(state) => {
          const hovered = (state as any).hovered as boolean | undefined;
          return [
            styles.button,
            (hovered || state.pressed) && styles.buttonPressed,
            disabled && styles.buttonDisabled,
          ];
        }}
        onPress={() => {
          void onClear();
        }}
        disabled={disabled}
      >
        <Text style={styles.buttonText}>Live</Text>
      </Pressable>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;
  return StyleSheet.create({
    banner: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10,
      marginHorizontal: 8,
      marginVertical: 6,
      paddingHorizontal: 12,
      paddingVertical: 8,
      backgroundColor: theme.notificationMuted,
      borderWidth,
      borderColor: theme.notification,
      borderRadius: 8,
    },
    text: {
      flex: 1,
      fontSize: 12,
      fontWeight: '600',
      color: theme.text,
    },
    button: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.surface,
      borderWidth,
      borderColor: theme.border,
      minWidth: 60,
      alignItems: 'center',
      justifyContent: 'center',
    },
    buttonPressed: {
      opacity: 0.85,
    },
    buttonDisabled: {
      opacity: 0.5,
    },
    buttonText: {
      fontSize: 11,
      fontWeight: '700',
      color: theme.text,
    },
  });
}