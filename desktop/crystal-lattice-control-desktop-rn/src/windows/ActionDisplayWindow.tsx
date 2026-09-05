import React, { useCallback, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { type ActionDisplayFollowupAction } from '@crystal-lattice/frontend-sdk';
import {
  ThemeProvider,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import { MacSelect } from '../native/MacSelect';
import { useDesktopTheme } from '../theme/useDesktopTheme';
import { ActionDisplayCard } from '../ui/ActionDisplayCard';
import {
  clearActiveActionDisplayWindow,
  useActiveActionDisplayWindow,
} from './actionDisplayWindowCoordinator';
import { DesktopWindowManager } from './desktopWindowManager';

const WINDOW_KEY = 'actionDisplay';

export function ActionDisplayWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <ActionDisplayWindowInner />
    </ThemeProvider>
  );
}

function ActionDisplayWindowInner(): React.JSX.Element {
  const active = useActiveActionDisplayWindow();
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const fieldRenderers = useMemo(
    () => ({
      select: (params: any) => (
        <View style={styles.selectGroup}>
          <Text style={styles.selectLabel}>{params.label}</Text>
          {params.description ? (
            <Text style={styles.selectDescription}>{params.description}</Text>
          ) : null}
          <MacSelect
            style={styles.select}
            options={params.options}
            selectedValue={params.value}
            placeholder={params.placeholder || 'Select…'}
            onValueChange={params.onChange}
          />
        </View>
      ),
    }),
    [styles],
  );

  const closeWindow = useCallback(() => {
    DesktopWindowManager?.closeReactWindow({ windowKey: WINDOW_KEY });
  }, []);

  const dismiss = useCallback(() => {
    if (!active) {
      closeWindow();
      return;
    }
    clearActiveActionDisplayWindow(active.state.id);
    closeWindow();
    void active.handlers.onDismiss();
  }, [active, closeWindow]);

  const followup = useCallback(
    async (
      action: ActionDisplayFollowupAction,
      formValues?: Record<string, any>,
    ) => {
      if (!active) {
        return;
      }
      setActiveActionId(action.id);
      try {
        await active.handlers.onFollowupAction(action, formValues);
      } finally {
        setActiveActionId(null);
      }
    },
    [active],
  );

  if (!active) {
    return <View style={styles.root} />;
  }

  return (
    <View style={styles.root} testID="desktop-action-display-window">
      <ActionDisplayCard
        display={active.state.display}
        contextLabel={active.state.contextLabel}
        activeActionId={activeActionId}
        onDismiss={dismiss}
        onFollowupAction={followup}
        fieldRenderers={fieldRenderers}
        bounded
        bodyTestID="desktop-action-display-body"
      />
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      padding: 16,
      backgroundColor: theme.backgroundAlt,
    },
    selectGroup: {
      marginBottom: 14,
    },
    selectLabel: {
      color: theme.text,
      fontSize: 12,
      fontWeight: '600',
      marginBottom: 5,
    },
    selectDescription: {
      color: theme.textSecondary,
      fontSize: 11,
      marginBottom: 5,
    },
    select: {
      minHeight: 28,
    },
  });
}
