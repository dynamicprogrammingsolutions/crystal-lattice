import React, { useMemo } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export type ComposerAttachmentPlusRow = {
  id: string;
  label: string;
  iconName: string;
};

export const ComposerAttachmentPlusPopoverContent: React.FC<{
  title?: string;
  rows: ComposerAttachmentPlusRow[];
  onSelectRow: (rowId: string) => void;
  onCancel?: () => void;
}> = ({ title = 'Add attachment', rows, onSelectRow, onCancel }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <View style={styles.root}>
      {/*<Text style={styles.title}>{title}</Text>*/}
      {rows.map((row) => (
        <TouchableOpacity
          key={row.id}
          style={styles.rowButton}
          onPress={() => onSelectRow(row.id)}
        >
          <Icon name={row.iconName} size={16} color={theme.textSecondary} />
          <Text style={styles.rowButtonText}>{row.label}</Text>
        </TouchableOpacity>
      ))}
      {/*{onCancel && (
        <TouchableOpacity style={[styles.rowButton, styles.cancelButton]} onPress={onCancel}>
          <Icon name="x" size={16} color={theme.textSecondary} />
          <Text style={styles.rowButtonText}>Cancel</Text>
        </TouchableOpacity>
      )}*/}
    </View>
  );
};

const createStyles = (theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    root: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      gap: 8,
    },
    title: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
      textAlign: 'center',
      marginBottom: 6,
    },
    rowButton: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    cancelButton: {
      backgroundColor: theme.surfaceAlt,
    },
    rowButtonText: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '600',
      color: theme.text,
    },
  });
