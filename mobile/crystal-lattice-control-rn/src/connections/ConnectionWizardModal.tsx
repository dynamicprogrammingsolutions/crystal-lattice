import React, { useMemo } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import CenteredModalSurface from "../components/CenteredModalSurface";
import { useTheme } from "../theme";

interface ConnectionWizardModalProps {
  content: React.ReactNode;
  onCancel: () => void;
}

export default function ConnectionWizardModal({
  content,
  onCancel,
}: ConnectionWizardModalProps) {
  const theme = useTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        header: {
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
          padding: 16,
        },
        title: { color: theme.text, fontSize: 20, fontWeight: "600" },
        close: { padding: 8 },
        closeText: { color: theme.primary, fontSize: 16 },
      }),
    [theme]
  );
  return (
    <CenteredModalSurface
      visible={content != null}
      testID="connection-wizard-modal"
      onRequestClose={onCancel}
      keyboardAvoiding
    >
      <View style={styles.header}>
        <Text style={styles.title}>New connection</Text>
        <TouchableOpacity
          testID="connection-wizard-modal-close"
          accessibilityRole="button"
          accessibilityLabel="Close connection setup"
          style={styles.close}
          onPress={onCancel}
        >
          <Text style={styles.closeText}>Close</Text>
        </TouchableOpacity>
      </View>
      {content}
    </CenteredModalSurface>
  );
}
