import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type {
  ActionDisplayFollowupAction,
  ActionDisplayPayload,
  NotificationSeverity,
} from '@crystal-lattice/frontend-sdk';

import { useTheme } from '../theme';

export interface NotificationBannerProps {
  display: ActionDisplayPayload;
  severity?: NotificationSeverity;
  connectionLabel?: string | null;
  sessionLabel?: string | null;
  onDismiss?: () => void;
  onFollowupAction?: (action: ActionDisplayFollowupAction) => void;
  disabledActionIds?: readonly string[];
  testID?: string;
}

export function NotificationBanner({
  display,
  severity,
  connectionLabel,
  sessionLabel,
  onDismiss,
  onFollowupAction,
  disabledActionIds = [],
  testID,
}: NotificationBannerProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const variant = display.variant ?? severity ?? 'info';
  const colors =
    variant === 'success'
      ? { accent: theme.success, background: opaqueTint(theme.surface, theme.success) }
      : variant === 'warning'
        ? { accent: theme.warning, background: opaqueTint(theme.surface, theme.warning) }
        : variant === 'error'
          ? { accent: theme.danger, background: opaqueTint(theme.surface, theme.danger) }
          : {
              accent: theme.notification,
              background: opaqueTint(theme.surface, theme.notification),
            };
  const labels = [connectionLabel, sessionLabel].filter(Boolean).join(' • ');

  return (
    <View
      testID={testID}
      accessibilityRole="alert"
      style={[styles.banner, { backgroundColor: colors.background, borderColor: colors.accent }]}
    >
      <View style={[styles.accent, { backgroundColor: colors.accent }]} />
      <View style={styles.content}>
        {labels ? <Text style={styles.context}>{labels}</Text> : null}
        {display.title ? <Text style={styles.title}>{display.title}</Text> : null}
        <Text style={styles.body}>{display.body}</Text>
        {display.actions?.length ? (
          <View style={styles.actions}>
            {display.actions.map((action) => (
              <Pressable
                key={action.id}
                accessibilityRole="button"
                accessibilityLabel={action.label}
                disabled={disabledActionIds.includes(action.id)}
                style={[styles.action, { borderColor: colors.accent }]}
                onPress={() => {
                  if (action.kind === 'dismiss') {
                    onDismiss?.();
                  } else {
                    onFollowupAction?.(action);
                  }
                }}
              >
                <Text style={styles.actionText}>{action.label}</Text>
              </Pressable>
            ))}
          </View>
        ) : null}
      </View>
      {display.dismissible !== false && onDismiss ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Dismiss notification"
          style={styles.dismiss}
          onPress={onDismiss}
        >
          <Text style={styles.dismissText}>×</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

function opaqueTint(base: string, accent: string): string {
  const parse = (value: string): [number, number, number] | null => {
    const match = /^#([0-9a-f]{6})$/i.exec(value);
    if (!match) return null;
    const raw = match[1];
    return [
      Number.parseInt(raw.slice(0, 2), 16),
      Number.parseInt(raw.slice(2, 4), 16),
      Number.parseInt(raw.slice(4, 6), 16),
    ];
  };
  const baseRgb = parse(base);
  const accentRgb = parse(accent);
  if (!baseRgb || !accentRgb) {
    return base;
  }
  const amount = 0.14;
  const mixed = baseRgb.map((value, index) =>
    Math.round(value * (1 - amount) + accentRgb[index] * amount),
  );
  return `#${mixed.map((value) => value.toString(16).padStart(2, '0')).join('')}`;
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    banner: {
      flexDirection: 'row',
      alignItems: 'stretch',
      borderWidth: 1,
      borderRadius: 10,
      overflow: 'hidden',
      shadowColor: '#000',
      shadowOpacity: 0.16,
      shadowRadius: 8,
      shadowOffset: { width: 0, height: 3 },
      elevation: 5,
    },
    accent: { width: 4 },
    content: { flex: 1, paddingHorizontal: 12, paddingVertical: 10, gap: 3 },
    context: { color: theme.textSecondary, fontSize: 10, fontWeight: '700' },
    title: { color: theme.text, fontSize: 13, fontWeight: '700' },
    body: { color: theme.text, fontSize: 12 },
    actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 6 },
    action: {
      borderWidth: 1,
      borderRadius: 7,
      backgroundColor: theme.surface,
      paddingHorizontal: 9,
      paddingVertical: 5,
    },
    actionText: { color: theme.text, fontSize: 11, fontWeight: '700' },
    dismiss: { paddingHorizontal: 10, justifyContent: 'center' },
    dismissText: { color: theme.text, fontSize: 22, lineHeight: 24 },
  });
}