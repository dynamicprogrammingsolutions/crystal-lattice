import React, { useEffect, useMemo, useState } from "react";
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from "react-native";

import { useTheme, type Theme } from "../theme";

export type OptionItem = { value: string; label: string };

export interface OptionsPickerModalProps {
  visible: boolean;
  options: OptionItem[];
  onSelect: (value: string) => void;
  onRequestClose: () => void;
  useModal?: boolean;
  selectedValue?: string;
  allowCustomValue?: boolean;
  customValueLabel?: string;
  customValuePlaceholder?: string;
  showReset?: boolean;
  resetLabel?: string;
  onReset?: () => void;
}

/**
 * Shared searchable options picker modal.
 */
const OptionsPickerModal: React.FC<OptionsPickerModalProps> = ({
  visible,
  options,
  onSelect,
  onRequestClose,
  useModal = true,
  selectedValue = "",
  allowCustomValue = false,
  customValueLabel = "Other value…",
  customValuePlaceholder = "Enter a value",
  showReset = false,
  resetLabel = "Reset to configured value",
  onReset,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [search, setSearch] = useState("");
  const [customValue, setCustomValue] = useState("");

  useEffect(() => {
    if (!visible) {
      return;
    }
    const selectedIsDeclared = options.some(
      (option) => option.value === selectedValue,
    );
    setCustomValue(selectedIsDeclared ? "" : selectedValue);
  }, [options, selectedValue, visible]);

  const filteredOptions = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return options;
    return options.filter((opt) => {
      const text = `${opt.label ?? ""} ${opt.value ?? ""}`.toLowerCase();
      return text.includes(q);
    });
  }, [options, search]);

  if (!visible) return null;

  const handleSelect = (value: string) => {
    onSelect(value);
    setSearch("");
  };
  const handleCustomSelect = () => {
    const nextValue = customValue.trim();
    if (nextValue) {
      handleSelect(nextValue);
    }
  };

  const handleClose = () => {
    setSearch("");
    onRequestClose();
  };

  const content = (
    <TouchableWithoutFeedback onPress={handleClose}>
      <View style={styles.overlay}>
        <TouchableWithoutFeedback onPress={() => {}}>
          <KeyboardAvoidingView
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            style={styles.content}
          >
            <TextInput
              style={styles.searchInput}
              placeholder="Search..."
              placeholderTextColor={theme.textSecondary}
              value={search}
              onChangeText={setSearch}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <ScrollView style={styles.list}>
              {filteredOptions.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  style={styles.item}
                  accessibilityRole="button"
                  accessibilityLabel={opt.label}
                  testID={`options-picker-option-${opt.value}`}
                  onPress={() => handleSelect(opt.value)}
                >
                  <Text style={styles.itemText} numberOfLines={2}>
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            {allowCustomValue ? (
              <View style={styles.customSection}>
                <Text style={styles.customLabel}>{customValueLabel}</Text>
                <TextInput
                  testID="options-picker-custom-input"
                  accessibilityLabel={customValueLabel}
                  style={styles.customInput}
                  placeholder={customValuePlaceholder}
                  placeholderTextColor={theme.textSecondary}
                  value={customValue}
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="done"
                  onSubmitEditing={handleCustomSelect}
                  onChangeText={setCustomValue}
                />
                <TouchableOpacity
                  testID="options-picker-custom-submit"
                  accessibilityRole="button"
                  accessibilityLabel="Use custom value"
                  style={[
                    styles.button,
                    styles.primaryButton,
                    !customValue.trim() && styles.disabledButton,
                  ]}
                  disabled={!customValue.trim()}
                  onPress={handleCustomSelect}
                >
                  <Text style={styles.primaryButtonText}>Use value</Text>
                </TouchableOpacity>
              </View>
            ) : null}
            {showReset && onReset ? (
              <TouchableOpacity
                testID="options-picker-reset"
                accessibilityRole="button"
                accessibilityLabel={resetLabel}
                style={styles.resetButton}
                onPress={() => {
                  onReset();
                  setSearch("");
                  setCustomValue("");
                }}
              >
                <Text style={styles.resetButtonText}>{resetLabel}</Text>
              </TouchableOpacity>
            ) : null}
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              accessibilityRole="button"
              accessibilityLabel="Cancel option selection"
              testID="options-picker-cancel"
              onPress={handleClose}
            >
              <Text style={styles.buttonTextSecondary}>Cancel</Text>
            </TouchableOpacity>
          </KeyboardAvoidingView>
        </TouchableWithoutFeedback>
      </View>
    </TouchableWithoutFeedback>
  );

  if (!useModal) {
    return content;
  }

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      onRequestClose={handleClose}
    >
      {content}
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      ...StyleSheet.absoluteFillObject,
      backgroundColor: theme.modalBackdrop,
      justifyContent: "center",
      alignItems: "center",
    },
    content: {
      width: "85%",
      maxHeight: "70%",
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
    },
    searchInput: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
      backgroundColor: theme.surface,
      marginBottom: 8,
    },
    list: {
      maxHeight: 320,
      marginVertical: 8,
    },
    customSection: {
      borderTopWidth: StyleSheet.hairlineWidth,
      borderTopColor: theme.border,
      paddingTop: 10,
      gap: 8,
    },
    customLabel: {
      color: theme.text,
      fontWeight: "700",
    },
    customInput: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      backgroundColor: theme.surface,
    },
    item: {
      paddingVertical: 12,
      paddingHorizontal: 8,
      borderBottomWidth: 1,
      borderBottomColor: theme.border,
    },
    itemText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
    },
    button: {
      marginTop: 8,
      alignSelf: "flex-end",
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 8,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    disabledButton: {
      opacity: 0.45,
    },
    primaryButtonText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: "600",
      color: theme.textOnPrimary,
    },
    resetButton: {
      alignSelf: "flex-start",
      paddingHorizontal: 8,
      paddingVertical: 8,
    },
    resetButtonText: {
      color: theme.danger,
      fontWeight: "700",
    },
    buttonTextSecondary: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: "600",
      color: theme.text,
    },
  });

export default OptionsPickerModal;
