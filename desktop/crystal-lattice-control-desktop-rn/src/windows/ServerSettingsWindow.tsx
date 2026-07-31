import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';
import {
  useServerSettingsForm,
} from '@crystal-lattice/frontend-sdk-react';
import {
  FetchTransport,
  RestAgentBackend,
} from '@crystal-lattice/frontend-sdk';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';
import { useActiveServerSettingsWindow } from './serverSettingsCoordinator';

export interface ServerSettingsWindowProps {
  connectionId?: string;
  connectionName?: string;
  baseUrl?: string;
}

export function ServerSettingsWindow({
  connectionId,
  connectionName,
  baseUrl,
}: ServerSettingsWindowProps): React.JSX.Element {
  const theme = useDesktopTheme();
  return (
    <ThemeProvider theme={theme}>
      <ServerSettingsWindowInner
        connectionId={connectionId}
        connectionName={connectionName}
        baseUrl={baseUrl}
      />
    </ThemeProvider>
  );
}

function ServerSettingsWindowInner({
  connectionId,
  connectionName,
  baseUrl,
}: ServerSettingsWindowProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveServerSettingsWindow();
  const initialBackend = useMemo(
    () => (baseUrl ? new RestAgentBackend({ transport: new FetchTransport({ baseUrl }) }) : null),
    [baseUrl],
  );
  const [pending, setPending] = useState<Record<string, string>>({});
  const { controller, state, items, savingKeys: saving } = useServerSettingsForm({
    backend: active?.backend ?? initialBackend,
    cacheKey: active?.connectionId ?? connectionId ?? 'default',
    enabled: !!active || !!initialBackend,
  });
  const close = () => {
    DesktopWindowManager?.closeReactWindow({ windowKey: 'serverSettings' });
  };

  const displayConnectionName = active?.connectionName ?? connectionName;
  if (!active && !initialBackend) return <View style={styles.root} />;
  return (
    <View testID="server-settings-window-root" style={styles.root}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Server settings</Text>
          {displayConnectionName ? (
            <Text
              testID="server-settings-connection-name"
              style={styles.subtitle}
            >
              {displayConnectionName}
            </Text>
          ) : null}
        </View>
        <Pressable accessibilityLabel="Close server settings" onPress={close}>
          <Text style={styles.close}>Close</Text>
        </Pressable>
      </View>
      {state?.loading ? <ActivityIndicator color={theme.primary} /> : null}
      {state?.error ? <Text style={styles.error}>{state.error}</Text> : null}
      <ScrollView contentContainerStyle={styles.content}>
        {items.map((item) => {
          const isSaving = saving.has(item.key);
          const effective = item.effectiveValue;
          if (item.type === 'checkbox') {
            return (
              <View key={item.key} style={styles.item}>
                <Text style={styles.label}>{item.label}</Text>
                <Pressable
                  accessibilityLabel={item.label}
                  disabled={item.disabled || isSaving}
                  style={styles.valueButton}
                  onPress={() => void controller?.patchSetting(item.key, !Boolean(effective))}
                >
                  <Text style={styles.valueText}>{Boolean(effective) ? 'On' : 'Off'}</Text>
                </Pressable>
              </View>
            );
          }
          const options = Array.isArray((item.element as any).options)
            ? (item.element as any).options
            : [];
          if (item.type === 'select') {
            return (
              <View key={item.key} style={styles.block}>
                <Text style={styles.label}>{item.label}</Text>
                <View style={styles.options}>
                  {options.map((raw: any) => {
                    const value = typeof raw === 'object' ? raw.value : raw;
                    const label = typeof raw === 'object' ? raw.label ?? raw.value : raw;
                    return (
                      <Pressable
                        key={String(value)}
                        style={[styles.valueButton, value === effective && styles.selected]}
                        onPress={() => void controller?.patchSetting(item.key, value)}
                      >
                        <Text style={styles.valueText}>{String(label)}</Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>
            );
          }
          const text = pending[item.key] ?? String(effective ?? '');
          return (
            <View key={item.key} style={styles.block}>
              <Text style={styles.label}>{item.label}</Text>
              <View style={styles.textRow}>
                <TextInput
                  accessibilityLabel={item.label}
                  style={styles.input}
                  value={text}
                  editable={!item.disabled && !isSaving}
                  onChangeText={(value) => setPending((current) => ({ ...current, [item.key]: value }))}
                />
                <Pressable
                  style={styles.valueButton}
                  onPress={() => void controller?.patchSetting(item.key, text)}
                >
                  <Text style={styles.valueText}>Save</Text>
                </Pressable>
              </View>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: { flex: 1, padding: 20, backgroundColor: theme.background },
    header: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
    title: { color: theme.text, fontSize: 20, fontWeight: '700' },
    subtitle: { color: theme.textSecondary, fontSize: 12 },
    close: { color: theme.primary, fontWeight: '700' },
    content: { gap: 14 },
    item: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    block: { gap: 8 },
    label: { color: theme.text, fontWeight: '600' },
    options: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
    valueButton: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 7,
      backgroundColor: theme.surface,
    },
    selected: { borderColor: theme.primary, backgroundColor: theme.primaryMuted },
    valueText: { color: theme.text },
    textRow: { flexDirection: 'row', gap: 8 },
    input: {
      flex: 1,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      color: theme.text,
      backgroundColor: theme.surface,
    },
    error: { color: theme.danger, marginBottom: 8 },
  });
}