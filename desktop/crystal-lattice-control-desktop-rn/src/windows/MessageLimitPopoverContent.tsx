import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

import { closeDesktopPopover } from './desktopPopoverCoordinator';

export interface MessageLimitPopoverContentProps {
  popoverId: string;
  startText: string;
  endText: string;
  lastReloadAtMs: number | null;
  onApply: (params: { startText: string; endText: string }) => void;
  onCancel: () => void;
}

export function MessageLimitPopoverContent({
  popoverId,
  startText,
  endText,
  lastReloadAtMs,
  onApply,
  onCancel,
}: MessageLimitPopoverContentProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const startInputRef = useRef<TextInput | null>(null);

  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');

  useEffect(() => {
    setStart(startText ?? '');
    setEnd(endText ?? '');
  }, [endText, popoverId, startText]);

  useEffect(() => {
    const timer = setTimeout(() => {
      startInputRef.current?.focus();
    }, 0);
    return () => clearTimeout(timer);
  }, [popoverId]);

  const lastReload =
    typeof lastReloadAtMs === 'number' ? new Date(lastReloadAtMs).toLocaleTimeString() : null;

  const close = () => {
    closeDesktopPopover(popoverId);
  };

  const handleApply = () => {
    close();
    onApply({ startText: start, endText: end });
  };

  return (
    <View style={styles.body}>
      <Text style={styles.subtitle}>
        Python-style range (start:end). Example: -50: for last 50 messages. Leave blank for all
        messages.
      </Text>

      <View style={styles.rangeRow}>
        <View style={styles.rangeInputContainer}>
          <Text style={styles.rangeLabel}>Start</Text>
          <TextInput
            ref={(node) => {
              startInputRef.current = node;
            }}
            style={styles.input}
            value={start}
            onChangeText={setStart}
            placeholder="e.g. -50"
            blurOnSubmit={false}
            onSubmitEditing={handleApply}
          />
        </View>
        <View style={styles.rangeInputContainer}>
          <Text style={styles.rangeLabel}>End</Text>
          <TextInput
            style={styles.input}
            value={end}
            onChangeText={setEnd}
            placeholder="optional"
            blurOnSubmit={false}
            onSubmitEditing={handleApply}
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
            onCancel();
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
            handleApply();
          }}
        >
          <Text style={styles.buttonPrimaryText}>Apply</Text>
        </Pressable>
      </View>

      {lastReload ? <Text style={styles.helperText}>Last reload at {lastReload}</Text> : null}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;

  return StyleSheet.create({
    body: {
      flex: 1,
      padding: 12,
      gap: 10,
      backgroundColor: theme.surface,
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
