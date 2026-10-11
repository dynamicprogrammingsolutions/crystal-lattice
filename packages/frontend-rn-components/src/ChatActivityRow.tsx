import React, { useMemo } from "react";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useTheme } from "./theme";

export interface ChatActivityRowProps {
  activities: readonly string[];
  recovery?: {
    onResend: () => void;
    onCancel: () => void;
    disabled: boolean;
  } | null;
}

export function ChatActivityRow({
  activities,
  recovery,
}: ChatActivityRowProps) {
  const theme = useTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        row: {
          flexDirection: "row",
          alignItems: "center",
          gap: 8,
          paddingHorizontal: 10,
          paddingVertical: 4,
          minHeight: 32,
          backgroundColor: recovery ? theme.warningMuted : theme.surfaceAlt,
        },
        text: {
          flex: 1,
          minWidth: 0,
          color: recovery ? theme.warning : theme.textSecondary,
          fontSize: theme.typography.fontSize.secondary,
          lineHeight: theme.typography.lineHeight.secondary,
        },
        button: { paddingHorizontal: 6, paddingVertical: 6 },
        buttonText: {
          color: theme.primary,
          fontSize: theme.typography.fontSize.secondary,
          lineHeight: theme.typography.lineHeight.secondary,
        },
        disabled: { opacity: 0.45 },
      }),
    [theme, !!recovery]
  );
  if (!recovery && activities.length === 0) return null;
  const activity = activities.join(" · ");
  return (
    <View
      testID="chat-activity-row"
      accessible={Platform.OS === "macos"}
      accessibilityRole="summary"
      accessibilityLabel={recovery ? "Send recovery" : "Chat activity"}
      style={styles.row}
    >
      {(!recovery || activities.length > 0) && (
        <View
          testID="chat-activity-progress"
          accessible
          accessibilityRole="progressbar"
          accessibilityLabel="Chat activity in progress"
        >
          <ActivityIndicator size="small" color={theme.primary} />
        </View>
      )}
      <Text
        testID={recovery ? "chat-send-recovery" : "chat-activity-label"}
        accessible
        accessibilityRole="text"
        style={styles.text}
        numberOfLines={2}
        accessibilityLiveRegion="polite"
      >
        {recovery
          ? `Send not confirmed${activity ? ` · ${activity}` : ""}`
          : activity}
      </Text>
      {recovery && (
        <>
          <Pressable
            testID="chat-send-recovery-resend"
            accessibilityRole="button"
            accessibilityLabel="Resend unconfirmed message"
            disabled={recovery.disabled}
            style={[styles.button, recovery.disabled && styles.disabled]}
            onPress={recovery.onResend}
          >
            <Text style={styles.buttonText}>Resend</Text>
          </Pressable>
          <Pressable
            testID="chat-send-recovery-cancel"
            accessibilityRole="button"
            accessibilityLabel="Cancel send recovery"
            style={styles.button}
            onPress={recovery.onCancel}
          >
            <Text style={styles.buttonText}>Cancel</Text>
          </Pressable>
        </>
      )}
    </View>
  );
}
