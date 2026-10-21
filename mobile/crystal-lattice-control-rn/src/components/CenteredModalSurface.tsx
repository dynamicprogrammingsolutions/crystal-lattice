import React, { useMemo } from "react";
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";

import { useTheme, type Theme } from "../theme";

export interface CenteredModalSurfaceProps {
  visible: boolean;
  testID?: string;
  onRequestClose: () => void;
  children: React.ReactNode;
  overlayChildren?: React.ReactNode;
  contentStyle?: StyleProp<ViewStyle>;
  keyboardAvoiding?: boolean;
}

const CenteredModalSurface: React.FC<CenteredModalSurfaceProps> = ({
  visible,
  testID,
  onRequestClose,
  children,
  overlayChildren,
  contentStyle,
  keyboardAvoiding = false,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  if (!visible) {
    return null;
  }

  const content = (
    <>
      <Pressable style={StyleSheet.absoluteFill} onPress={onRequestClose} />
      <View testID={testID} style={[styles.content, contentStyle]}>
        {children}
      </View>
      {overlayChildren}
    </>
  );

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      supportedOrientations={["portrait", "landscape"]}
      onRequestClose={onRequestClose}
    >
      {keyboardAvoiding ? (
        <KeyboardAvoidingView
          style={styles.keyboardContainer}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
          keyboardVerticalOffset={0}
        >
          <View
            testID={testID ? `${testID}-viewport` : undefined}
            style={styles.overlay}
          >
            {content}
          </View>
        </KeyboardAvoidingView>
      ) : (
        <View style={styles.overlay}>{content}</View>
      )}
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    keyboardContainer: {
      flex: 1,
    },
    overlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: "center",
      alignItems: "center",
    },
    content: {
      width: "90%",
      maxHeight: "80%",
      backgroundColor: theme.surface,
      borderRadius: 12,
      overflow: "hidden",
    },
  });

export default CenteredModalSurface;
