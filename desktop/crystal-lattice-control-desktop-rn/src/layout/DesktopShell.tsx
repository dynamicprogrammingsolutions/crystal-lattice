import React, { useMemo } from 'react';
import { StyleSheet, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export interface DesktopShellProps {
  activityRail: React.ReactNode;
  panel: React.ReactNode;
  main: React.ReactNode;
}

export function DesktopShell({
  activityRail,
  panel,
  main,
}: DesktopShellProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View style={styles.root}>
      <View style={styles.left}>
        <View style={styles.activityRail}>{activityRail}</View>
        <View style={styles.panel}>{panel}</View>
      </View>
      <View style={styles.main}>{main}</View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const separatorWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      flexDirection: 'row',
    },
    left: {
      flexDirection: 'row',
      borderRightWidth: separatorWidth,
      borderRightColor: theme.border,
      backgroundColor: theme.backgroundAlt,
    },
    activityRail: {
      width: 46,
      borderRightWidth: separatorWidth,
      borderRightColor: theme.border,
      backgroundColor: theme.surfaceAlt,
    },
    panel: {
      width: 340,
      backgroundColor: theme.backgroundAlt,
    },
    main: {
      flex: 1,
      backgroundColor: theme.background,
    },
  });
}
