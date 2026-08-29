import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

import { MacSelect, type MacSelectOption } from '../native/MacSelect';
import { closeDesktopPopover } from '../windows/desktopPopoverCoordinator';

export type AppendAsRole = 'system' | 'developer' | 'user' | 'assistant';

export interface AppendAsPopoverContentProps {
  popoverId: string;
  onSelectRole: (role: AppendAsRole) => void;
}

const ROLE_OPTIONS: MacSelectOption[] = [
  { value: 'system', label: 'System' },
  { value: 'developer', label: 'Developer' },
  { value: 'user', label: 'User' },
  { value: 'assistant', label: 'Assistant' },
];

const ROLE_HELPER_TEXT: Record<AppendAsRole, string> = {
  system: 'System message (instructions/constraints)',
  developer: 'Developer message (may be rejected by some servers)',
  user: 'User message',
  assistant: 'Assistant message',
};

export function AppendAsPopoverContent({
  popoverId,
  onSelectRole,
}: AppendAsPopoverContentProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [selectedRole, setSelectedRole] = useState<AppendAsRole>('user');
  const submitFocusRef = useRef<TextInput | null>(null);

  const focusSubmitCapture = useCallback(() => {
    submitFocusRef.current?.focus();
  }, []);

  const handleAppend = useCallback(() => {
    closeDesktopPopover(popoverId);
    onSelectRole(selectedRole);
  }, [onSelectRole, popoverId, selectedRole]);

  useEffect(() => {
    // Ensure keyboard events (Enter/Return) are handled inside the popover,
    // not by the underlying composer.
    const timer = setTimeout(() => focusSubmitCapture(), 0);
    return () => clearTimeout(timer);
  }, [focusSubmitCapture]);

  return (
    <View style={styles.body}>
      <Text style={styles.subtitle}>Append the composer text as a message with role:</Text>

      <MacSelect
        style={styles.select}
        options={ROLE_OPTIONS}
        selectedValue={selectedRole}
        onValueChange={(value) => {
          const next = String(value) as AppendAsRole;
          if (next === 'system' || next === 'developer' || next === 'user' || next === 'assistant') {
            setSelectedRole(next);
            focusSubmitCapture();
          }
        }}
      />

      <TextInput
        ref={(node) => {
          submitFocusRef.current = node;
        }}
        style={styles.submitCapture}
        value=""
        onChangeText={() => {}}
        blurOnSubmit={false}
        onSubmitEditing={() => handleAppend()}
      />

      <Text style={styles.helperText}>{ROLE_HELPER_TEXT[selectedRole]}</Text>

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
          onPress={() => closeDesktopPopover(popoverId)}
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
            handleAppend();
          }}
        >
          <Text style={styles.buttonPrimaryText}>Append</Text>
        </Pressable>
      </View>
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
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    select: {
      minHeight: 26,
      minWidth: 240,
      maxWidth: 420,
    },
    helperText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    submitCapture: {
      position: 'absolute',
      left: -1000,
      top: -1000,
      width: 1,
      height: 1,
      opacity: 0,
    },
    buttonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 10,
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
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
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
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
  });
}
