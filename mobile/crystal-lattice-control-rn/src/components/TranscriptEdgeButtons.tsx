import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import Icon from "react-native-vector-icons/Feather";

import { useTheme, type Theme } from "../theme";

const HIT_SLOP = 8;

export function TranscriptEdgeButtons({
  canScrollToTop,
  canScrollToBottom,
  onScrollToTop,
  onScrollToBottom,
}: {
  canScrollToTop: boolean;
  canScrollToBottom: boolean;
  onScrollToTop: () => void;
  onScrollToBottom: () => void;
}): React.JSX.Element | null {
  const theme = useTheme();
  const styles = React.useMemo(() => createStyles(theme), [theme]);

  if (!canScrollToTop && !canScrollToBottom) {
    return null;
  }

  return (
    <View pointerEvents="box-none" style={styles.overlay}>
      {canScrollToTop ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Scroll to top"
          hitSlop={HIT_SLOP}
          testID="transcript-scroll-to-top"
          style={({ pressed }) => [
            styles.button,
            styles.topButton,
            pressed && styles.pressed,
          ]}
          onPress={onScrollToTop}
        >
          <Icon name="chevron-up" size={20} color={theme.text} />
        </Pressable>
      ) : null}

      {canScrollToBottom ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Scroll to bottom"
          hitSlop={HIT_SLOP}
          testID="transcript-scroll-to-bottom"
          style={({ pressed }) => [
            styles.button,
            styles.bottomButton,
            pressed && styles.pressed,
          ]}
          onPress={onScrollToBottom}
        >
          <Icon name="chevron-down" size={20} color={theme.text} />
        </Pressable>
      ) : null}
    </View>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      ...StyleSheet.absoluteFillObject,
    },
    button: {
      position: "absolute",
      right: 7,
      width: 34,
      height: 34,
      borderRadius: 17,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      alignItems: "center",
      justifyContent: "center",
      opacity: 0.94,
      zIndex: 2,
    },
    topButton: {
      top: 8,
    },
    bottomButton: {
      bottom: 8,
    },
    pressed: {
      opacity: 0.7,
    },
  });
