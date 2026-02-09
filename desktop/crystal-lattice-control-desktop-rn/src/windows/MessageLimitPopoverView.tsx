import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';
import {
  clearActiveMessageLimitPopover,
  useActiveMessageLimitPopover,
} from './messageLimitPopoverCoordinator';

export function MessageLimitPopoverView(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <MessageLimitPopoverViewInner />
    </ThemeProvider>
  );
}

function MessageLimitPopoverViewInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveMessageLimitPopover();

  const [startText, setStartText] = useState('');
  const [endText, setEndText] = useState('');

  useEffect(() => {
    if (!active) {
      setStartText('');
      setEndText('');
      return;
    }
    setStartText(active.state.startText ?? '');
    setEndText(active.state.endText ?? '');
  }, [active?.state.endText, active?.state.id, active?.state.startText]);

  if (!active) {
    return <View style={styles.root} />;
  }

  const close = () => {
    clearActiveMessageLimitPopover(active.state.id);
    DesktopWindowManager?.closeMessageLimitPopover();
  };

  const lastReload =
    typeof active.state.lastReloadAtMs === 'number'
      ? new Date(active.state.lastReloadAtMs).toLocaleTimeString()
      : null;

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.headerTitle} numberOfLines={1}>
          Message range
        </Text>
        <Pressable
          style={(pressState) => {
            const hovered = (pressState as any).hovered as boolean | undefined;
            return [styles.closeButton, (hovered || pressState.pressed) && styles.closeButtonHovered];
          }}
          onPress={() => {
            close();
            active.handlers.onCancel();
          }}
        >
          <Text style={styles.closeButtonText}>×</Text>
        </Pressable>
      </View>

      <View style={styles.body}>
        <Text style={styles.subtitle}>
          Python-style range (start:end). Example: -50: for last 50 messages. Leave blank for all messages.
        </Text>

        <View style={styles.rangeRow}>
          <View style={styles.rangeInputContainer}>
            <Text style={styles.rangeLabel}>Start</Text>
            <TextInput
              style={styles.input}
              value={startText}
              onChangeText={setStartText}
              placeholder="e.g. -50"
            />
          </View>
          <View style={styles.rangeInputContainer}>
            <Text style={styles.rangeLabel}>End</Text>
            <TextInput
              style={styles.input}
              value={endText}
              onChangeText={setEndText}
              placeholder="optional"
            />
          </View>
        </View>

        <View style={styles.buttonsRow}>
          <Pressable
            style={(pressState) => {
              const hovered = (pressState as any).hovered as boolean | undefined;
              return [
                styles.button,
                styles.buttonSecondary,
                (hovered || pressState.pressed) && styles.buttonHovered,
              ];
            }}
            onPress={() => {
              close();
              active.handlers.onCancel();
            }}
          >
            <Text style={styles.buttonSecondaryText}>Cancel</Text>
          </Pressable>
          <Pressable
            style={(pressState) => {
              const hovered = (pressState as any).hovered as boolean | undefined;
              return [
                styles.button,
                styles.buttonPrimary,
                (hovered || pressState.pressed) && styles.buttonPrimaryHovered,
              ];
            }}
            onPress={() => {
              close();
              active.handlers.onApply({ startText, endText });
            }}
          >
            <Text style={styles.buttonPrimaryText}>Apply</Text>
          </Pressable>
        </View>

        {lastReload ? (
          <Text style={styles.helperText}>Last reload at {lastReload}</Text>
        ) : null}
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.surface,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderBottomWidth: borderWidth,
      borderBottomColor: theme.border,
    },
    headerTitle: {
      flex: 1,
      fontSize: 13,
      fontWeight: '800',
      color: theme.text,
    },
    closeButton: {
      borderWidth,
      borderColor: theme.border,
      borderRadius: 10,
      backgroundColor: theme.surface,
      width: 28,
      height: 28,
      alignItems: 'center',
      justifyContent: 'center',
    },
    closeButtonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    closeButtonText: {
      fontSize: 16,
      fontWeight: '900',
      color: theme.textSecondary,
      marginTop: -2,
    },
    body: {
      padding: 12,
      gap: 10,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    rangeRow: {
      flexDirection: 'row',
      gap: 12,
    },
    rangeInputContainer: {
      flex: 1,
      gap: 6,
    },
    rangeLabel: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.textSecondary,
    },
    input: {
      borderWidth,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      fontSize: 13,
    },
    buttonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 10,
      marginTop: 2,
    },
    button: {
      borderRadius: 10,
      paddingVertical: 10,
      paddingHorizontal: 14,
      borderWidth,
    },
    buttonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    buttonSecondary: {
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    buttonSecondaryText: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    buttonPrimary: {
      borderColor: theme.primary,
      backgroundColor: theme.primary,
    },
    buttonPrimaryHovered: {
      opacity: 0.9,
    },
    buttonPrimaryText: {
      fontSize: 13,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    helperText: {
      fontSize: 11,
      color: theme.textMuted,
    },
  });
}
