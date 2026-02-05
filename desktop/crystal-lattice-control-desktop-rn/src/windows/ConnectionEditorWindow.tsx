import React, { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';
import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';

export interface ConnectionEditorWindowProps {
  mode: 'new' | 'edit';
  initialRecord?: ConnectionRecord;
}

function parsePort(value: string): number | null {
  const parsed = parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0 || parsed > 65535) {
    return null;
  }
  return parsed;
}

function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    const v = c === 'x' ? r : (r % 4) + 8;
    return v.toString(16);
  });
}

export function ConnectionEditorWindow({
  mode,
  initialRecord,
}: ConnectionEditorWindowProps): React.JSX.Element {
  const systemTheme = useDesktopTheme();

  return (
    <ThemeProvider theme={systemTheme}>
      <ConnectionEditorWindowInner mode={mode} initialRecord={initialRecord} />
    </ThemeProvider>
  );
}

function ConnectionEditorWindowInner({
  mode,
  initialRecord,
}: ConnectionEditorWindowProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [name, setName] = useState(initialRecord?.name ?? '');
  const [host, setHost] = useState(initialRecord?.kind === 'manual' ? initialRecord.host : '127.0.0.1');
  const [portText, setPortText] = useState(
    initialRecord?.kind === 'manual' ? String(initialRecord.port) : '8080',
  );
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    const trimmedHost = host.trim();
    const parsedPort = parsePort(portText.trim());
    if (!trimmedHost) {
      setError('Host is required');
      return;
    }
    if (!parsedPort) {
      setError('Port must be 1–65535');
      return;
    }

    const now = Date.now();
    const record: ConnectionRecord = {
      id: initialRecord?.id ?? generateId(),
      kind: 'manual',
      name: name.trim() || `${trimmedHost}:${parsedPort}`,
      host: trimmedHost,
      port: parsedPort,
      lastUsedAt: now,
    };

    DesktopWindowManager?.submitConnectionEditor({ record });
  };

  const cancel = () => {
    DesktopWindowManager?.cancelConnectionEditor();
  };

  return (
    <View style={styles.root}>
      <Text style={styles.title}>{mode === 'new' ? 'New Connection' : 'Edit Connection'}</Text>

      <View style={styles.form}>
        <View style={styles.field}>
          <Text style={styles.label}>Name</Text>
          <TextInput
            style={styles.input}
            value={name}
            placeholder="Optional"
            placeholderTextColor={theme.textMuted}
            onChangeText={(value) => {
              setError(null);
              setName(value);
            }}
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Host</Text>
          <TextInput
            style={styles.input}
            value={host}
            placeholder="127.0.0.1"
            placeholderTextColor={theme.textMuted}
            onChangeText={(value) => {
              setError(null);
              setHost(value);
            }}
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Port</Text>
          <TextInput
            style={styles.input}
            value={portText}
            keyboardType="number-pad"
            placeholder="8080"
            placeholderTextColor={theme.textMuted}
            onChangeText={(value) => {
              setError(null);
              setPortText(value);
            }}
          />
        </View>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.footer}>
        <Pressable
          style={({ pressed }) => [styles.button, styles.cancelButton, pressed && styles.buttonPressed]}
          onPress={cancel}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </Pressable>

        <Pressable
          style={({ pressed }) => [styles.button, styles.saveButton, pressed && styles.buttonPressed]}
          onPress={submit}
        >
          <Text style={styles.saveButtonText}>Save</Text>
        </Pressable>
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      padding: 16,
      gap: 12,
      backgroundColor: theme.background,
    },
    title: {
      fontSize: 16,
      fontWeight: '800',
      color: theme.text,
    },
    form: {
      gap: 10,
    },
    field: {
      gap: 6,
    },
    label: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.textSecondary,
    },
    input: {
      borderWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      backgroundColor: theme.surface,
    },
    error: {
      fontSize: 12,
      color: theme.danger,
    },
    footer: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 10,
      marginTop: 'auto',
    },
    button: {
      paddingHorizontal: 14,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth,
    },
    buttonPressed: {
      opacity: 0.85,
    },
    cancelButton: {
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    cancelButtonText: {
      color: theme.text,
      fontWeight: '700',
      fontSize: 12,
    },
    saveButton: {
      borderColor: theme.primary,
      backgroundColor: theme.primary,
    },
    saveButtonText: {
      color: theme.textOnPrimary,
      fontWeight: '800',
      fontSize: 12,
    },
  });
}
