import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

import type { TabStripStyle } from '../tabs/tabStripStyle';
import { DesktopConnectionDisplayRail } from '../ui/DesktopGlobalDisplayLayer';

export interface ChatPanePlaceholderProps {
  visible: boolean;
  title: string;
  subtitle?: string;
  styleVariant?: TabStripStyle;
}

export function ChatPanePlaceholder({
  visible,
  title,
  subtitle,
  styleVariant = 'toolbarTabs',
}: ChatPanePlaceholderProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, styleVariant), [theme, styleVariant]);

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

      <DesktopConnectionDisplayRail />

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

function createStyles(theme: ReturnType<typeof useTheme>, styleVariant: TabStripStyle) {
  const codeLike = styleVariant === 'codeTabs' || styleVariant === 'underlineTabs';
  const radius = styleVariant === 'roundedPills' ? 12 : 10;
   const separatorWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      borderWidth: codeLike ? 0 : separatorWidth,
      borderColor: codeLike ? 'transparent' : theme.border,
      borderRadius: codeLike ? 0 : radius,
      backgroundColor: theme.surface,
      overflow: codeLike ? 'visible' : 'hidden',
    },
    header: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
      gap: 2,
      backgroundColor: codeLike ? theme.surface : theme.surface,
    },
    visible: {
      display: 'flex',
    },
    hidden: {
      display: 'none',
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
