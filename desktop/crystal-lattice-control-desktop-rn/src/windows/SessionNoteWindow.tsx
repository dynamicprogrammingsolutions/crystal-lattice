import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import {
  MAX_SESSION_NOTE_LENGTH,
  ThemeProvider,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import {
  closeSessionNoteWindow,
  useActiveSessionNoteWindow,
} from './sessionNoteCoordinator';

export function SessionNoteWindow(): React.JSX.Element {
  const theme = useDesktopTheme();
  return (
    <ThemeProvider theme={theme}>
      <SessionNoteWindowInner />
    </ThemeProvider>
  );
}

function SessionNoteWindowInner(): React.JSX.Element {
  const active = useActiveSessionNoteWindow();
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [text, setText] = useState(active?.initialNote ?? '');

  useEffect(() => {
    setText(active?.initialNote ?? '');
  }, [active?.id, active?.initialNote]);

  if (!active) {
    return (
      <View style={styles.root}>
        <Text style={styles.helper}>No session note is selected.</Text>
      </View>
    );
  }

  return (
    <View style={styles.root} testID="session-note-window-root">
      <View style={styles.header}>
        <Text style={styles.title}>Local Note</Text>
        <Text style={styles.subtitle} numberOfLines={2}>
          {active.title}
        </Text>
        <Text style={styles.sessionId} numberOfLines={1}>
          {active.sessionId}
        </Text>
      </View>
      <TextInput
        testID="session-note-input"
        style={styles.input}
        multiline
        value={text}
        maxLength={MAX_SESSION_NOTE_LENGTH}
        onChangeText={setText}
        placeholder="Add a note stored only on this Mac"
        placeholderTextColor={theme.textMuted}
      />
      <View style={styles.actions}>
        <Pressable
          style={[styles.button, styles.secondaryButton]}
          onPress={() => {
            active.onRemove();
            closeSessionNoteWindow(active.id);
          }}
        >
          <Text style={styles.secondaryButtonText}>Remove Note</Text>
        </Pressable>
        <View style={styles.actionsSpacer} />
        <Pressable
          style={[styles.button, styles.secondaryButton]}
          onPress={() => closeSessionNoteWindow(active.id)}
        >
          <Text style={styles.secondaryButtonText}>Cancel</Text>
        </Pressable>
        <Pressable
          style={[styles.button, styles.primaryButton]}
          onPress={() => {
            active.onSave(text);
            closeSessionNoteWindow(active.id);
          }}
        >
          <Text style={styles.primaryButtonText}>Save</Text>
        </Pressable>
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      padding: 18,
      gap: 12,
      backgroundColor: theme.background,
    },
    header: {
      gap: 3,
    },
    title: {
      fontSize: theme.typography.fontSize.title,
      lineHeight: theme.typography.lineHeight.title,
      color: theme.text,
      fontWeight: '700',
    },
    subtitle: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
    },
    sessionId: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    helper: {
      color: theme.textSecondary,
    },
    input: {
      flex: 1,
      minHeight: 150,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 10,
      backgroundColor: theme.surface,
      color: theme.text,
      padding: 10,
      textAlignVertical: 'top',
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
    actions: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    actionsSpacer: {
      flex: 1,
    },
    button: {
      borderRadius: 8,
      paddingHorizontal: 13,
      paddingVertical: 8,
      borderWidth: 1,
    },
    secondaryButton: {
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    primaryButton: {
      borderColor: theme.primary,
      backgroundColor: theme.primary,
    },
    secondaryButtonText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '600',
    },
    primaryButtonText: {
      color: theme.textOnPrimary,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '700',
    },
  });
}
