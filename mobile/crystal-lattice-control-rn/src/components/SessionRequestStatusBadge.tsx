import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from '../theme';

const LABELS: Record<SessionRequestStatus['state'], string> = {
  idle: 'Idle',
  not_started: 'Not started',
  running: 'In progress',
  succeeded: 'Completed',
  interrupted: 'Interrupted',
};

const SessionRequestStatusBadge: React.FC<{
  status: SessionRequestStatus | null;
  testID?: string;
}> = ({ status, testID }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  if (!status) return null;
  const label = LABELS[status.state];
  return (
    <View
      testID={testID}
      accessibilityLabel={`Request status: ${label}`}
      style={[
        styles.badge,
        status.state === 'running'
          ? styles.running
          : status.state === 'succeeded'
            ? styles.completed
            : status.state === 'interrupted'
              ? styles.interrupted
              : styles.neutral,
      ]}
    >
      <Text style={styles.text}>{label}</Text>
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    badge: {
      alignSelf: 'flex-start',
      borderRadius: 999,
      borderWidth: 1,
      paddingHorizontal: 7,
      paddingVertical: 2,
    },
    running: {
      backgroundColor: theme.primaryMuted,
      borderColor: theme.primary,
    },
    completed: {
      backgroundColor: theme.successMuted,
      borderColor: theme.success,
    },
    interrupted: {
      backgroundColor: theme.warningMuted,
      borderColor: theme.warning,
    },
    neutral: {
      backgroundColor: theme.surfaceAlt,
      borderColor: theme.border,
    },
    text: {
      color: theme.text,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      fontWeight: '600',
    },
  });

export default SessionRequestStatusBadge;