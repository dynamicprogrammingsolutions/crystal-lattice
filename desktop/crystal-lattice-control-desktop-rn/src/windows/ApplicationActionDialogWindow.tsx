import React, { useCallback, useMemo } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';

import {
  ApplicationActionDialogLayout,
  ThemeProvider,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { useDesktopApplicationActionFieldRenderers } from '../ui/useDesktopApplicationActionFieldRenderers';
import {
  clearActiveApplicationActionDialog,
  useActiveApplicationActionDialog,
} from './applicationActionDialogCoordinator';
import { DesktopWindowManager } from './desktopWindowManager';

type Presentation = 'window' | 'popover';

export interface ApplicationActionDialogWindowProps {
  presentation?: Presentation;
}

export function ApplicationActionDialogWindow(
  props: ApplicationActionDialogWindowProps,
): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <ApplicationActionDialogWindowInner {...props} />
    </ThemeProvider>
  );
}

function ApplicationActionDialogWindowInner(
  props: ApplicationActionDialogWindowProps,
): React.JSX.Element {
  const theme = useTheme();
  const presentation: Presentation = props.presentation === 'window' ? 'window' : 'popover';
  const styles = useMemo(() => createStyles(theme, presentation), [presentation, theme]);
  const active = useActiveApplicationActionDialog();
  const fieldRenderers = useDesktopApplicationActionFieldRenderers();

  const closeWindow = useCallback(() => {
    DesktopWindowManager?.closeApplicationActionDialogPopover();
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
          fieldRenderers={fieldRenderers}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          style={presentation === 'popover' ? styles.popoverLayout : styles.windowLayout}
        />
      </ScrollView>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>, presentation: Presentation) {
  const borderWidth = 1;
  const isPopover = presentation === 'popover';

  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: isPopover ? theme.surface : theme.backgroundAlt,
    },
    scroll: {
      flex: 1,
    },
    scrollContent: {
      padding: isPopover ? 0 : 16,
    },
    windowLayout: {
      borderWidth,
      borderColor: theme.border,
    },
    popoverLayout: {
      backgroundColor: 'transparent',
      borderWidth: 0,
      borderColor: 'transparent',
      borderRadius: 0,
    },
  });
}
