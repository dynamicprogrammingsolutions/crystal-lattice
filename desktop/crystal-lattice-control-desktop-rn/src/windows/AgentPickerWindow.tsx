import React, { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';

export interface AgentPickerWindowProps {
  connectionId: string;
  connectionName?: string;
  agents?: string[];
  mode?: 'createSession' | 'switchSessionAgent';
  sessionId?: string;
  title?: string;
  primaryButtonLabel?: string;
  initialAgentId?: string;
}

export function AgentPickerWindow(props: AgentPickerWindowProps): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <AgentPickerWindowInner {...props} />
    </ThemeProvider>
  );
}

function AgentPickerWindowInner({
  connectionId,
  connectionName,
  agents,
  mode = 'createSession',
  sessionId,
  title,
  primaryButtonLabel,
  initialAgentId,
}: AgentPickerWindowProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const agentList = Array.isArray(agents) ? agents : [];
  const initialSelected = useMemo(() => {
    if (typeof initialAgentId === 'string' && initialAgentId && agentList.includes(initialAgentId)) {
      return initialAgentId;
    }
    return agentList[0] ?? null;
  }, [agentList, initialAgentId]);

  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(initialSelected);

  const submit = () => {
    if (!connectionId || !selectedAgentId) {
      return;
    }
    DesktopWindowManager?.submitAgentPicker({
      connectionId,
      agentId: selectedAgentId,
      mode,
      sessionId: mode === 'switchSessionAgent' ? sessionId : undefined,
    });
  };

  const cancel = () => {
    DesktopWindowManager?.cancelAgentPicker();
  };

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.title}>
          {title ? title : mode === 'switchSessionAgent' ? 'Switch Agent' : 'New Session'}
        </Text>
        <Text style={styles.subtitle} numberOfLines={1}>
          {connectionName ? `Connection: ${connectionName}` : `Connection: ${connectionId}`}
        </Text>
        {mode === 'switchSessionAgent' && sessionId ? (
          <Text style={styles.subtitle} numberOfLines={1}>
            Session: {sessionId}
          </Text>
        ) : null}
      </View>

      {agentList.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No agents available.</Text>
          <Text style={styles.emptyMeta}>Open the connection and try again.</Text>
        </View>
      ) : (
        <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
          {agentList.map((agentId) => {
            const selected = selectedAgentId === agentId;
            return (
              <Pressable
                key={agentId}
                style={(state) => {
                  const hovered = (state as any).hovered as boolean | undefined;
                  return [
                    styles.row,
                    selected && styles.rowSelected,
                    (hovered || state.pressed) && styles.rowHovered,
                  ];
                }}
                onPress={() => setSelectedAgentId(agentId)}
              >
                <Text style={styles.rowText} numberOfLines={1}>
                  {agentId}
                </Text>
                {selected ? <Text style={styles.check}>✓</Text> : null}
              </Pressable>
            );
          })}
        </ScrollView>
      )}

      <View style={styles.footer}>
        <Pressable
          style={(state) => [styles.button, styles.cancelButton, state.pressed && styles.buttonPressed]}
          onPress={cancel}
        >
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </Pressable>

        <Pressable
          style={(state) => {
            const disabled = !selectedAgentId;
            return [
              styles.button,
              styles.createButton,
              disabled && styles.createButtonDisabled,
              state.pressed && !disabled && styles.buttonPressed,
            ];
          }}
          disabled={!selectedAgentId}
          onPress={submit}
        >
          <Text style={styles.createButtonText}>
            {primaryButtonLabel
              ? primaryButtonLabel
              : mode === 'switchSessionAgent'
                ? 'Switch'
                : 'Create'}
          </Text>
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
    header: {
      gap: 4,
    },
    title: {
      fontSize: 16,
      fontWeight: '800',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    list: {
      flex: 1,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
    },
    listContent: {
      paddingVertical: 6,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    rowHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    rowSelected: {
      backgroundColor: theme.primaryMuted,
    },
    rowText: {
      flex: 1,
      fontSize: 13,
      color: theme.text,
      fontWeight: '600',
    },
    check: {
      fontSize: 14,
      fontWeight: '800',
      color: theme.success,
    },
    empty: {
      padding: 12,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
      gap: 4,
    },
    emptyText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    emptyMeta: {
      fontSize: 11,
      color: theme.textMuted,
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
    createButton: {
      borderColor: theme.primary,
      backgroundColor: theme.primary,
    },
    createButtonDisabled: {
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
    },
    createButtonText: {
      color: theme.textOnPrimary,
      fontWeight: '800',
      fontSize: 12,
    },
  });
}
