import React, { useMemo } from 'react';
import { StyleSheet, Switch, Text, TouchableOpacity, View } from 'react-native';
import type {
  ApplicationActionDialogFieldRenderParams,
  ApplicationActionDialogFieldRenderers,
} from '@crystal-lattice/frontend-rn-components';

import { useTheme, type Theme } from '../theme';

function isTruthyBooleanText(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  return normalized === 'true' || normalized === '1' || normalized === 'yes' || normalized === 'y';
}

function FieldShell({
  params,
  children,
}: {
  params: ApplicationActionDialogFieldRenderParams;
  children: React.ReactNode;
}) {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View style={styles.inputGroup}>
      <Text style={styles.inputLabel}>{params.label}</Text>
      {params.description ? <Text style={styles.inputDescription}>{params.description}</Text> : null}
      {children}
    </View>
  );
}

export function useMobileApplicationActionDialogFieldRenderers(): ApplicationActionDialogFieldRenderers {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return useMemo(
    () => ({
      select: (params: ApplicationActionDialogFieldRenderParams) => {
        if (params.options.length === 0) {
          return params.renderFallback();
        }

        return (
          <FieldShell params={params}>
            <View style={styles.chipsRow}>
              {params.options.map((option) => {
                const selected = option.value === params.value;
                return (
                  <TouchableOpacity
                    key={option.value}
                    accessibilityRole="button"
                    accessibilityState={{ selected }}
                    testID={`action-dialog-select-${params.name}-${option.value}`}
                    style={selected ? styles.chipSelected : styles.chip}
                    onPress={() => params.onChange(option.value)}
                  >
                    <Text style={selected ? styles.chipTextSelected : styles.chipText}>
                      {option.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </FieldShell>
        );
      },
      boolean: (params: ApplicationActionDialogFieldRenderParams) => (
        <FieldShell params={params}>
          <View style={styles.switchRow}>
            <Switch
              value={isTruthyBooleanText(params.value)}
              onValueChange={(next) => params.onChange(next ? 'true' : 'false')}
            />
          </View>
        </FieldShell>
      ),
      checkbox: (params: ApplicationActionDialogFieldRenderParams) => (
        <FieldShell params={params}>
          <View style={styles.switchRow}>
            <Switch
              value={isTruthyBooleanText(params.value)}
              onValueChange={(next) => params.onChange(next ? 'true' : 'false')}
            />
          </View>
        </FieldShell>
      ),
    }),
    [styles],
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    inputGroup: {
      marginBottom: 12,
    },
    inputLabel: {
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    inputDescription: {
      fontSize: theme.typography.fontSize.tiny,
      color: theme.textSecondary,
      marginBottom: 6,
    },
    chipsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginTop: 2,
    },
    chip: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: theme.border,
      marginRight: 6,
      marginBottom: 6,
      backgroundColor: theme.surfaceAlt,
    },
    chipSelected: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 12,
      borderWidth: 1,
      backgroundColor: theme.primary,
      borderColor: theme.primary,
      marginRight: 6,
      marginBottom: 6,
    },
    chipText: {
      fontSize: theme.typography.fontSize.small,
      color: theme.text,
    },
    chipTextSelected: {
      fontSize: theme.typography.fontSize.small,
      color: theme.textOnPrimary,
      fontWeight: '600',
    },
    switchRow: {
      alignItems: 'flex-start',
      marginTop: 2,
    },
  });