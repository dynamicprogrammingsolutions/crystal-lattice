import React, { useEffect, useMemo, useState } from 'react';
import {
  Clipboard,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

function isLikelyUrl(value: string): boolean {
  const v = value.trim();
  if (!v) return false;
  return v.startsWith('http://') || v.startsWith('https://') || v.startsWith('data:');
}

export const AttachmentUrlPopoverContent: React.FC<{
  title: string;
  initialUrl?: string;
  onCancel: () => void;
  onAttach: (url: string) => void;
}> = ({ title, initialUrl, onCancel, onAttach }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [url, setUrl] = useState(initialUrl ?? '');

  useEffect(() => {
    let cancelled = false;
    const readClipboard = async () => {
      try {
        const text = await Clipboard.getString();
        if (cancelled) return;
        if (isLikelyUrl(text) && !(initialUrl ?? '').trim()) {
          setUrl(text.trim());
        }
      } catch {
        // ignore
      }
    };
    readClipboard();
    return () => {
      cancelled = true;
    };
  }, [initialUrl]);

  const trimmed = url.trim();
  const canAttach = isLikelyUrl(trimmed);

  return (
    <View style={styles.root}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>Paste an http(s) or data: URL.</Text>

      <TextInput
        style={styles.input}
        value={url}
        onChangeText={setUrl}
        placeholder="https://…"
        placeholderTextColor={theme.textSecondary}
        autoCapitalize="none"
        autoCorrect={false}
      />

      <View style={styles.footerRow}>
        <TouchableOpacity style={styles.footerButton} onPress={onCancel}>
          <Text style={styles.footerButtonText}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.footerButton, styles.footerButtonPrimary, !canAttach && styles.footerButtonDisabled]}
          onPress={() => onAttach(trimmed)}
          disabled={!canAttach}
        >
          <View style={styles.attachRow}>
            <Icon name="paperclip" size={14} color={theme.textOnPrimary} />
            <Text style={[styles.footerButtonText, styles.footerButtonPrimaryText]}>Attach</Text>
          </View>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const createStyles = (theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    root: {
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    title: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
      textAlign: 'center',
      marginBottom: 4,
    },
    subtitle: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      marginBottom: 10,
      textAlign: 'center',
    },
    input: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 10,
      backgroundColor: theme.surface,
      paddingHorizontal: 10,
      paddingVertical: 8,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      color: theme.text,
      marginBottom: 10,
    },
    footerRow: {
      flexDirection: 'row',
      gap: 10,
    },
    footerButton: {
      flex: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
      alignItems: 'center',
      justifyContent: 'center',
    },
    footerButtonPrimary: {
      backgroundColor: theme.primary,
      borderColor: theme.primary,
    },
    footerButtonDisabled: {
      opacity: 0.5,
    },
    footerButtonText: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '700',
      color: theme.text,
    },
    footerButtonPrimaryText: {
      color: theme.textOnPrimary,
    },
    attachRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
  });
