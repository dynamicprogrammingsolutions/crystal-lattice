import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export interface ChatPanePlaceholderProps {
  visible: boolean;
  title: string;
  subtitle?: string;
}

export function ChatPanePlaceholder({
  visible,
  title,
  subtitle,
}: ChatPanePlaceholderProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View style={[styles.root, visible ? styles.visible : styles.hidden]}>
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>
        {subtitle ? (
          <Text style={styles.subtitle} numberOfLines={1}>
            {subtitle}
          </Text>
        ) : null}
      </View>

      <View style={styles.body}>
        <Text style={styles.hint}>
          Chat UI is implemented in task 080.
        </Text>
        <Text style={styles.hintSecondary}>
          This pane stays mounted when tabs are hidden.
        </Text>
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    visible: {
      display: 'flex',
    },
    hidden: {
      display: 'none',
    },
    header: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
      gap: 2,
    },
    title: {
      fontSize: 14,
      fontWeight: '700',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    body: {
      flex: 1,
      padding: 12,
      justifyContent: 'center',
      alignItems: 'center',
      gap: 6,
    },
    hint: {
      fontSize: 13,
      color: theme.text,
    },
    hintSecondary: {
      fontSize: 12,
      color: theme.textSecondary,
    },
  });
}
