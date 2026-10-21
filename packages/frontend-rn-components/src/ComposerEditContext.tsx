import React, { useMemo } from "react";
import {
  Pressable,
  Platform,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import { useTheme } from "./theme";

export function ComposerEditContext({
  index,
  onCancel,
  submitting,
  prefix = "composer",
  style,
}: {
  index: number;
  onCancel: () => void;
  submitting: boolean;
  prefix?: string;
  style?: StyleProp<ViewStyle>;
}) {
  const theme = useTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        row: {
          flexDirection: "row",
          alignItems: "center",
          gap: 8,
          paddingHorizontal: 10,
          paddingVertical: 3,
          backgroundColor: theme.warningMuted,
        },
        text: {
          color: theme.warning,
          flex: 1,
          minWidth: 0,
          fontSize: theme.typography.fontSize.secondary,
          lineHeight: theme.typography.lineHeight.secondary,
          fontWeight: "600",
        },
        button: { paddingVertical: 5 },
        disabled: { opacity: 0.45 },
        cancelText: {
          color: theme.warning,
          fontSize: theme.typography.fontSize.secondary,
          lineHeight: theme.typography.lineHeight.secondary,
        },
      }),
    [theme]
  );
  return (
    <View
      testID={`${prefix}-edit-context`}
      accessible={Platform.OS === "macos"}
      accessibilityRole="summary"
      accessibilityLabel={`Editing message [${index}]`}
      style={[styles.row, style]}
    >
      <Text
        testID={`${prefix}-edit-label`}
        accessible
        accessibilityRole="text"
        style={styles.text}
        numberOfLines={1}
        ellipsizeMode="middle"
      >
        {`Editing message [${index}]`}
      </Text>
      <Pressable
        testID={`${prefix}-cancel-edit`}
        accessibilityRole="button"
        accessibilityLabel="Cancel edit"
        disabled={submitting}
        style={[styles.button, submitting && styles.disabled]}
        onPress={onCancel}
      >
        <Text style={styles.cancelText}>Cancel edit</Text>
      </Pressable>
    </View>
  );
}
