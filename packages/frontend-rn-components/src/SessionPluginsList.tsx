import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import type { SessionPluginEntry } from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from './theme';

const KIND_ORDER = ['providers', 'extensions', 'features', 'tools'] as const;

function formatKindLabel(kind: string): string {
  if (!kind) return 'Other';
  const normalized = kind.trim();
  if (!normalized) return 'Other';
  return normalized.slice(0, 1).toUpperCase() + normalized.slice(1);
}

function sortPlugins(a: SessionPluginEntry, b: SessionPluginEntry): number {
  const aLabel = (typeof a.name === 'string' && a.name) || a.id;
  const bLabel = (typeof b.name === 'string' && b.name) || b.id;
  return aLabel.localeCompare(bLabel);
}

export function SessionPluginsList(props: {
  plugins: SessionPluginEntry[];
  onToggle: (pluginId: string, nextEnabled: boolean) => void;
  onReset?: () => void;
  loading?: boolean;
  error?: string | null;
}): React.JSX.Element {
  const theme = useTheme();

  const duplicateKeySet = useMemo(() => {
    const counts = new Map<string, number>();
    const safePlugins = Array.isArray(props.plugins) ? props.plugins : [];
    for (const plugin of safePlugins) {
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
  }, [props.plugins]);

  console.log('Rendering SessionPluginsList with plugins:', props.plugins);

  const grouped = useMemo(() => {
    const byKind = new Map<string, SessionPluginEntry[]>();
    const safePlugins = Array.isArray(props.plugins) ? props.plugins : [];
    for (const plugin of safePlugins) {
      if (!plugin || typeof plugin.id !== 'string') {
        continue;
      }

      const kind = typeof plugin.kind === 'string' && plugin.kind ? plugin.kind : 'other';
      const list = byKind.get(kind) ?? [];
      list.push(plugin);
      byKind.set(kind, list);
    }

    for (const list of byKind.values()) {
      list.sort(sortPlugins);
    }

    const orderedKinds = [
      ...KIND_ORDER.filter((kind) => byKind.has(kind)),
      ...Array.from(byKind.keys())
        .filter((kind) => !KIND_ORDER.includes(kind as any))
        .sort(),
    ];

    return orderedKinds.map((kind) => ({ kind, plugins: byKind.get(kind) ?? [] }));
  }, [props.plugins]);

  const hasSessionOverride = useMemo(() => {
    return (Array.isArray(props.plugins) ? props.plugins : []).some(
      (plugin) => plugin?.source === 'session',
    );
  }, [props.plugins]);

  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View style={styles.container}>
      {props.error ? <Text style={styles.errorText}>{props.error}</Text> : null}

      {props.loading ? (
        <View style={styles.loadingRow}>
          <ActivityIndicator />
          <Text style={styles.loadingText}>Loading plugins…</Text>
        </View>
      ) : null}

      {grouped.map((group) => {
        if (group.plugins.length === 0) {
          return null;
        }

        return (
          <View key={group.kind} style={styles.group}>
            <Text style={styles.groupTitle}>{formatKindLabel(group.kind)}</Text>
            {group.plugins.map((plugin, index) => {
              const title = (typeof plugin.name === 'string' && plugin.name) || plugin.id;
              const duplicateKey = `${group.kind}:${plugin.id}`;

              const subtitle =
                typeof plugin.name === 'string' && plugin.name && plugin.id !== plugin.name
                  ? plugin.id
                  : duplicateKeySet.has(duplicateKey)
                    ? (typeof plugin.class_path === 'string' && plugin.class_path) ||
                      (typeof plugin.class_name === 'string' && plugin.class_name) ||
                      null
                  : null;
              const inactive = plugin.active === false;

              const keySuffix =
                (typeof plugin.class_path === 'string' && plugin.class_path) ||
                (typeof plugin.class_name === 'string' && plugin.class_name) ||
                `idx-${index}`;

              return (
                <View key={`${group.kind}:${plugin.id}:${keySuffix}`} style={styles.row}>
                  <View style={styles.rowText}>
                    <View style={styles.rowTitleLine}>
                      <Text style={styles.rowTitle} numberOfLines={1}>
                        {title}
                      </Text>
                      {inactive ? <Text style={styles.inactiveBadge}>Inactive</Text> : null}
                    </View>
                    {subtitle ? (
                      <Text style={styles.rowSubtitle} numberOfLines={1}>
                        {subtitle}
                      </Text>
                    ) : null}
                  </View>
                  <Switch
                    value={Boolean(plugin.enabled)}
                    onValueChange={(value) => props.onToggle(plugin.id, Boolean(value))}
                  />
                </View>
              );
            })}
          </View>
        );
      })}

      {props.onReset ? (
        <TouchableOpacity
          style={[styles.resetButton, !hasSessionOverride ? styles.resetButtonDisabled : null]}
          onPress={() => {
            if (!hasSessionOverride) {
              return;
            }
            props.onReset?.();
          }}
          disabled={!hasSessionOverride}
        >
          <Text style={[styles.resetText, !hasSessionOverride ? styles.resetTextDisabled : null]}>
            Reset to defaults
          </Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

function createStyles(theme: Theme) {
  return StyleSheet.create({
    container: {
      width: '100%',
    },
    errorText: {
      color: theme.danger,
      marginBottom: 10,
      fontSize: theme.typography.fontSize.secondary,
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 8,
    },
    loadingText: {
      marginLeft: 8,
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.secondary,
    },
    group: {
      marginBottom: 14,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 10,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    groupTitle: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      fontSize: theme.typography.fontSize.secondary,
      fontWeight: '700',
      color: theme.text,
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
      backgroundColor: theme.surfaceAlt,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
    },
    rowText: {
      flex: 1,
      paddingRight: 10,
    },
    rowTitleLine: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    rowTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
      flexShrink: 1,
    },
    rowSubtitle: {
      marginTop: 2,
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
    },
    inactiveBadge: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
    },
    resetButton: {
      alignSelf: 'flex-start',
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    resetButtonDisabled: {
      opacity: 0.6,
    },
    resetText: {
      color: theme.primary,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
    },
    resetTextDisabled: {
      color: theme.textSecondary,
    },
  });
}

