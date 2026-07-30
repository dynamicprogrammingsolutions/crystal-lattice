import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import type {
  TranscriptRangeControlAction,
  TranscriptRangeControlButton,
} from "@crystal-lattice/frontend-sdk";

import { useTheme, type Theme } from "../theme";

export function TranscriptRangeControls({
  buttons,
  disabled,
  onAction,
  testID,
}: {
  buttons: TranscriptRangeControlButton[];
  disabled: boolean;
  onAction: (action: TranscriptRangeControlAction) => void;
  testID: string;
}): React.JSX.Element | null {
  const theme = useTheme();
  const styles = React.useMemo(() => createStyles(theme), [theme]);

  if (buttons.length === 0) {
    return null;
  }

  return (
    <View style={styles.row} testID={testID}>
      {buttons.map((button) => {
        const secondary = button.id === "showAll" || button.id === "showLast";
        return (
          <TouchableOpacity
            key={button.id}
            accessibilityRole="button"
            accessibilityLabel={button.title}
            disabled={disabled}
            testID={`${testID}-${button.id}`}
            style={[
              styles.button,
              secondary && styles.secondaryButton,
              disabled && styles.disabledButton,
            ]}
            onPress={() => onAction(button.id)}
          >
            <Text style={styles.label}>{button.title}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    row: {
      flexDirection: "row",
      justifyContent: "center",
      alignItems: "center",
      flexWrap: "wrap",
      gap: 8,
      paddingHorizontal: 44,
      paddingVertical: 8,
    },
    button: {
      minHeight: 36,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      paddingHorizontal: 10,
      paddingVertical: 6,
      alignItems: "center",
      justifyContent: "center",
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    disabledButton: {
      opacity: 0.45,
    },
    label: {
      color: theme.primary,
      fontSize: theme.typography.fontSize.small,
      fontWeight: "700",
    },
  });
