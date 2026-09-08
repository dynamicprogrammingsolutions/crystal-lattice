import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { SessionRequestStatus } from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from './theme';
import {
  getSessionRequestStatusPresentation,
  type SessionRequestStatusTone,
} from './sessionRequestStatus';

export interface SessionRequestStatusIndicatorProps {
  status: SessionRequestStatus | null;
  variant?: 'badge' | 'inline' | 'dot';
  testID?: string;
}

export function SessionRequestStatusIndicator({
  status,
  variant = 'badge',
  testID,
}: SessionRequestStatusIndicatorProps): React.JSX.Element | null {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const presentation = getSessionRequestStatusPresentation(status);
  if (!presentation) return null;
  const colors = toneColors(theme, presentation.tone);
  const showLabel = variant !== 'dot';

  return (
    <View
      testID={testID}
      accessible
      accessibilityLabel={`Request status: ${presentation.label}`}
      accessibilityValue={{ text: presentation.label }}
      style={[
        styles.base,
        variant === 'badge' && styles.badge,
        variant === 'inline' && styles.inline,
        variant === 'dot' && styles.dotOnly,
        variant === 'badge' && {
          backgroundColor: colors.background,
          borderColor: colors.foreground,
        },
      ]}
    >
      {variant !== 'badge' ? (
        <View
          testID={testID ? `${testID}-dot` : undefined}
          style={[styles.dot, { backgroundColor: colors.foreground }]}
        />
      ) : null}
      {showLabel ? <Text style={styles.text}>{presentation.label}</Text> : null}
    </View>
  );
}

function toneColors(theme: Theme, tone: SessionRequestStatusTone) {
  if (tone === 'primary') {
    return { foreground: theme.primary, background: theme.primaryMuted };
  }
  if (tone === 'success') {
    return { foreground: theme.success, background: theme.successMuted };
  }
  if (tone === 'warning') {
    return { foreground: theme.warning, background: theme.warningMuted };
  }
  return { foreground: theme.textMuted, background: theme.surfaceAlt };
}

function createStyles(theme: Theme) {
  return StyleSheet.create({
    base: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    badge: {
      alignSelf: 'flex-start',
      borderRadius: 999,
      borderWidth: 1,
      paddingHorizontal: 7,
      paddingVertical: 2,
    },
    inline: {
      gap: 5,
    },
    dotOnly: {
      width: 10,
      height: 10,
      alignItems: 'center',
      justifyContent: 'center',
    },
    dot: {
      width: 7,
      height: 7,
      borderRadius: 999,
    },
    text: {
      color: theme.text,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      fontWeight: '600',
    },
  });
}
