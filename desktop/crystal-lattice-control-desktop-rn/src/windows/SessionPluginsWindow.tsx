import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';
import type { SessionPluginEntry } from '@crystal-lattice/frontend-sdk';
import { useSessionPluginsController } from '@crystal-lattice/frontend-sdk-react';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { MacCheckbox } from '../native/MacCheckbox';
import { DesktopWindowManager } from './desktopWindowManager';
import {
  clearActiveSessionPluginsWindow,
  useActiveSessionPluginsWindow,
} from './sessionPluginsCoordinator';

const KIND_ORDER = ['providers', 'extensions', 'features', 'tools', 'other'] as const;
type OrderedKind = (typeof KIND_ORDER)[number];

function sortPlugins(a: SessionPluginEntry, b: SessionPluginEntry): number {
  const aLabel = (typeof a.name === 'string' && a.name) || a.id;
  const bLabel = (typeof b.name === 'string' && b.name) || b.id;
  return aLabel.localeCompare(bLabel);
}

function coerceKind(kind: SessionPluginEntry['kind']): OrderedKind {
  if (kind === 'providers' || kind === 'extensions' || kind === 'features' || kind === 'tools') {
    return kind as OrderedKind;
  }
  return 'other';
}

function hasSessionOverrides(plugins: SessionPluginEntry[]): boolean {
  return plugins.some((p) => p.source === 'session');
}

function computeDuplicateKeySet(plugins: SessionPluginEntry[]): Set<string> {
  const counts = new Map<string, number>();
  for (const plugin of plugins) {
    if (!plugin || typeof plugin.id !== 'string' || !plugin.id) {
      continue;
    }
    const kind = typeof plugin.kind === 'string' && plugin.kind ? plugin.kind : 'other';
    const key = `${kind}:${plugin.id}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const duplicates = new Set<string>();
  for (const [key, count] of counts.entries()) {
    if (count > 1) {
      duplicates.add(key);
    }
  }
  return duplicates;
}

export function SessionPluginsWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <SessionPluginsWindowInner />
    </ThemeProvider>
  );
}

function SessionPluginsWindowInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveSessionPluginsWindow();

  const [optimisticEnabledById, setOptimisticEnabledById] = useState<Record<string, boolean>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [mutationCount, setMutationCount] = useState(0);
  const clearSuccessTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const backend = active?.state.backend ?? null;
  const sessionId = active?.state.sessionId ?? null;

  const { state, setEnabled, resetToDefaults } = useSessionPluginsController({
    backend,
    sessionId,
    enabled: Boolean(active),
  });

  useEffect(() => {
    return () => {
      if (clearSuccessTimerRef.current) {
        clearTimeout(clearSuccessTimerRef.current);
        clearSuccessTimerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!successMessage) {
      return;
    }
    if (clearSuccessTimerRef.current) {
      clearTimeout(clearSuccessTimerRef.current);
    }
    clearSuccessTimerRef.current = setTimeout(() => {
      setSuccessMessage(null);
    }, 1400);

    return () => {
      if (clearSuccessTimerRef.current) {
        clearTimeout(clearSuccessTimerRef.current);
        clearSuccessTimerRef.current = null;
      }
    };
  }, [successMessage]);

  useEffect(() => {
    setOptimisticEnabledById({});
  }, [state.lastLoadedAt]);

  const plugins = useMemo((): SessionPluginEntry[] => {
    const base = Array.isArray(state.plugins) ? state.plugins : [];
    if (!optimisticEnabledById || Object.keys(optimisticEnabledById).length === 0) {
      return base;
    }

    return base.map((plugin) => {
      const next = optimisticEnabledById[plugin.id];
      if (typeof next !== 'boolean') {
        return plugin;
      }
      return { ...plugin, enabled: next };
    });
  }, [optimisticEnabledById, state.plugins]);

  const closeWindow = useCallback(() => {
    if (active?.state.id) {
      clearActiveSessionPluginsWindow(active.state.id);
    }
    DesktopWindowManager?.closeReactWindow({ windowKey: 'sessionPlugins' });
  }, [active]);

  const grouped = useMemo(() => {
    const groups: Record<OrderedKind, SessionPluginEntry[]> = {
      providers: [],
      extensions: [],
      features: [],
      tools: [],
      other: [],
    };

    plugins.forEach((plugin) => {
      groups[coerceKind(plugin.kind)].push(plugin);
    });

    for (const list of Object.values(groups)) {
      list.sort(sortPlugins);
    }

    return groups;
  }, [plugins]);

  const duplicateKeySet = useMemo(() => {
    return computeDuplicateKeySet(plugins);
  }, [plugins]);

  if (!active) {
    return <View style={styles.root} />;
  }

  const canReset = hasSessionOverrides(plugins);

  const hasOptimistic = Object.keys(optimisticEnabledById).length > 0;
  const showSpinner = (state.loading || mutationCount > 0 || hasOptimistic) && !state.error;
  const statusText = state.error || successMessage;
  const statusTone = state.error ? 'error' : successMessage ? 'success' : showSpinner ? 'busy' : 'idle';

  return (
    <View style={styles.root}>
      <View style={styles.headerRow}>
        <View style={styles.header}>
          <Text style={styles.title}>Session plugins</Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            Session: {active.state.sessionId}
          </Text>
        </View>

        <View style={styles.headerButtons}>
          <Pressable
            style={(pressState) => {
              const hovered = (pressState as any).hovered as boolean | undefined;
              return [
                styles.button,
                styles.buttonSecondary,
                (!canReset || state.loading) && styles.buttonDisabled,
                (hovered || pressState.pressed) &&
                  canReset &&
                  !state.loading &&
                  styles.buttonHovered,
              ];
            }}
            disabled={!canReset || state.loading}
            onPress={() => {
              setSuccessMessage(null);
              setMutationCount((prev) => prev + 1);
              resetToDefaults()
                .then(() => {
                  setSuccessMessage('Reset to defaults.');
                })
                .catch(() => {
                  // state captures errors
                })
                .finally(() => {
                  setMutationCount((prev) => Math.max(0, prev - 1));
                });
            }}
          >
            <Text style={styles.buttonSecondaryText}>Reset</Text>
          </Pressable>

          <Pressable
            style={(pressState) => {
              const hovered = (pressState as any).hovered as boolean | undefined;
              return [styles.button, styles.buttonPrimary, (hovered || pressState.pressed) && styles.buttonHovered];
            }}
            onPress={closeWindow}
          >
            <Text style={styles.buttonPrimaryText}>Close</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.statusLine}>
        {showSpinner ? <ActivityIndicator size="small" color={theme.primary} /> : null}
        {statusText ? (
          <Text
            style={[
              styles.statusText,
              statusTone === 'error'
                ? styles.statusTextError
                : statusTone === 'success'
                  ? styles.statusTextSuccess
                  : null,
            ]}
            numberOfLines={1}
          >
            {statusText}
          </Text>
        ) : null}
      </View>

      {!state.loading && !state.error && plugins.length === 0 ? (
        <Text style={styles.helperText}>No plugins are available.</Text>
      ) : null}

      {plugins.length > 0 ? (
        <View style={styles.listContainer}>
          <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
            {KIND_ORDER.map((kind) => {
              const entries = grouped[kind];
              if (!entries || entries.length === 0) {
                return null;
              }
              return (
                <View key={kind} style={styles.kindSection}>
                  <Text style={styles.kindTitle}>{kind}</Text>
                  {entries.map((plugin, index) => {
                    const title = (typeof plugin.name === 'string' && plugin.name) || plugin.id;
                    const duplicateKey = `${kind}:${plugin.id}`;

                    const subtitle =
                      typeof plugin.name === 'string' && plugin.name && plugin.id !== plugin.name
                        ? plugin.id
                        : duplicateKeySet.has(duplicateKey)
                          ? (typeof plugin.class_path === 'string' && plugin.class_path) ||
                            (typeof plugin.class_name === 'string' && plugin.class_name) ||
                            null
                          : null;

                    const keySuffix =
                      (typeof plugin.class_path === 'string' && plugin.class_path) ||
                      (typeof plugin.class_name === 'string' && plugin.class_name) ||
                      `idx-${index}`;

                    const inactive = plugin.active === false;
                    return (
                      <View
                        key={`${kind}:${plugin.id}:${keySuffix}`}
                        style={styles.pluginRow}
                      >
                        <View style={styles.pluginLeft}>
                          <MacCheckbox
                            style={styles.macCheckbox}
                            label={title}
                            value={Boolean(plugin.enabled)}
                            enabled={!state.loading}
                            onValueChange={(next) => {
                              setSuccessMessage(null);
                              setMutationCount((prev) => prev + 1);
                              setOptimisticEnabledById((prev) => ({ ...prev, [plugin.id]: next }));
                              setEnabled(plugin.id, next)
                                .then(() => {
                                  setSuccessMessage('Saved.');
                                  setOptimisticEnabledById((prev) => {
                                    const updated = { ...prev };
                                    delete updated[plugin.id];
                                    return updated;
                                  });
                                })
                                .catch(() => {
                                  setOptimisticEnabledById((prev) => {
                                    const updated = { ...prev };
                                    delete updated[plugin.id];
                                    return updated;
                                  });
                                })
                                .finally(() => {
                                  setMutationCount((prev) => Math.max(0, prev - 1));
                                });
                            }}
                          />
                          {subtitle ? (
                            <Text style={styles.pluginSubtitle} numberOfLines={1}>
                              {subtitle}
                            </Text>
                          ) : null}
                        </View>

                        <View style={styles.pluginMeta}>
                          {inactive ? <Text style={styles.inactiveBadge}>Inactive</Text> : null}
                          {plugin.source ? (
                            <Text style={styles.sourceBadge}>{plugin.source}</Text>
                          ) : null}
                        </View>
                      </View>
                    );
                  })}
                </View>
              );
            })}
          </ScrollView>
        </View>
      ) : null}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;
  return StyleSheet.create({
    root: {
      flex: 1,
      padding: 16,
      backgroundColor: theme.surface,
    },
    headerRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    },
    header: {
      flex: 1,
      paddingRight: 12,
    },
    title: {
      fontSize: 18,
      fontWeight: '700',
      color: theme.text,
      marginBottom: 2,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textMuted,
    },
    headerButtons: {
      flexDirection: 'row',
      gap: 8,
      alignItems: 'center',
    },
    button: {
      borderRadius: 10,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderWidth,
    },
    buttonPrimary: {
      backgroundColor: theme.primary,
      borderColor: theme.primary,
    },
    buttonSecondary: {
      backgroundColor: theme.surface,
      borderColor: theme.border,
    },
    buttonDisabled: {
      opacity: 0.5,
    },
    buttonHovered: {
      opacity: 0.92,
    },
    buttonPrimaryText: {
      color: theme.textOnPrimary,
      fontWeight: '700',
      fontSize: 13,
    },
    buttonSecondaryText: {
      color: theme.text,
      fontWeight: '600',
      fontSize: 13,
    },
    statusLine: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      minHeight: 22,
      marginBottom: 10,
    },
    statusText: {
      color: theme.textSecondary,
      fontSize: 13,
      flexShrink: 1,
    },
    statusTextError: {
      color: theme.danger,
      fontWeight: '600',
    },
    statusTextSuccess: {
      color: theme.success,
      fontWeight: '600',
    },
    helperText: {
      color: theme.textSecondary,
    },
    listContainer: {
      flex: 1,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      overflow: 'hidden',
    },
    list: {
      flex: 1,
      backgroundColor: theme.surface,
    },
    listContent: {
      padding: 12,
      gap: 16,
    },
    kindSection: {
      gap: 10,
    },
    kindTitle: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.textSecondary,
      textTransform: 'capitalize',
    },
    pluginRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      paddingVertical: 2,
      gap: 12,
    },
    pluginLeft: {
      flex: 1,
      flexDirection: 'column',
      gap: 4,
      paddingRight: 10,
    },
    macCheckbox: {
      flexGrow: 1,
      flexShrink: 1,
      minHeight: 20,
    },
    pluginSubtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    pluginMeta: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    inactiveBadge: {
      fontSize: 12,
      color: theme.danger,
      fontWeight: '600',
    },
    sourceBadge: {
      fontSize: 12,
      color: theme.textMuted,
    },
  });
}
