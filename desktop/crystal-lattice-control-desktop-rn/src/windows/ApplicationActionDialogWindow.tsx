import React, { useCallback, useMemo } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';

import {
  ApplicationActionDialogLayout,
  ThemeProvider,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import {
  clearActiveApplicationActionDialog,
  useActiveApplicationActionDialog,
} from './applicationActionDialogCoordinator';
import { DesktopWindowManager } from './desktopWindowManager';

export function ApplicationActionDialogWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <ApplicationActionDialogWindowInner />
    </ThemeProvider>
  );
}

function ApplicationActionDialogWindowInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveApplicationActionDialog();

  const closeWindow = useCallback(() => {
    DesktopWindowManager?.closeApplicationActionDialogWindow();
  }, []);

  if (!active) {
    return <View style={styles.root} />;
  }

  const handleCancel = () => {
    clearActiveApplicationActionDialog(active.state.id);
    closeWindow();
    active.handlers.onCancel();
  };

  const handleSubmit = async (values: Record<string, any>) => {
    clearActiveApplicationActionDialog(active.state.id);
    closeWindow();
    await active.handlers.onSubmit(values);
  };

  return (
    <View style={styles.root}>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
        <ApplicationActionDialogLayout
          dialog={active.state.dialog}
          titleFallback={active.state.titleFallback}
          prefillContext={active.state.prefillContext}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          style={styles.card}
        />
      </ScrollView>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.backgroundAlt,
    },
    scroll: {
      flex: 1,
    },
    scrollContent: {
      padding: 16,
    },
    card: {
      borderWidth,
      borderColor: theme.border,
    },
  });
}
