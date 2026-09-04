import React, { useMemo, useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import type {
  ConfigRichDropdownUi,
  ConfigRichUiControl,
} from "@crystal-lattice/frontend-sdk";

import { useTheme } from "../theme";
import type { MenuIconRenderer } from "./ActionsMenuContent";

export interface RichConfigDropdownControlProps {
  control: ConfigRichUiControl;
  value: unknown;
  disabled?: boolean;
  placement: string;
  onPress: () => void;
  renderIcon?: MenuIconRenderer;
  testID?: string;
  buttonRef?: React.Ref<any>;
}

export function RichConfigDropdownControl(
  props: RichConfigDropdownControlProps,
): React.JSX.Element | null {
  const theme = useTheme();
  if (props.control.richUi.kind !== "dropdown") {
    return null;
  }
  const richUi = props.control.richUi as ConfigRichDropdownUi;
  const value =
    props.value === undefined || props.value === null
      ? ""
      : String(props.value);
  const selectedLabel =
    richUi.options.find((option) => option.value === value)?.label ?? value;
  const testID =
    props.testID ??
    `rich-config-${props.control.element.key}-${props.placement}`;

  return (
    <TouchableOpacity
      ref={props.buttonRef}
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={`${richUi.label}: ${selectedLabel || "Not set"}`}
      accessibilityState={{ disabled: props.disabled }}
      disabled={props.disabled}
      style={[
        styles.control,
        { borderColor: theme.border, backgroundColor: theme.surfaceAlt },
      ]}
      onPress={props.onPress}
    >
      {richUi.icon && props.renderIcon
        ? props.renderIcon({
            name: richUi.icon,
            size: 14,
            color: props.disabled ? theme.textMuted : theme.primary,
          })
        : null}
      <Text
        numberOfLines={1}
        style={[
          styles.controlLabel,
          { color: props.disabled ? theme.textMuted : theme.textSecondary },
        ]}
      >
        {richUi.label}:
      </Text>
      <Text
        numberOfLines={1}
        style={[
          styles.controlValue,
          { color: props.disabled ? theme.textMuted : theme.text },
        ]}
      >
        {selectedLabel || "Not set"}
      </Text>
      <Text
        style={[
          styles.chevron,
          { color: props.disabled ? theme.textMuted : theme.textSecondary },
        ]}
      >
        ▾
      </Text>
    </TouchableOpacity>
  );
}

export interface RichConfigDropdownPanelProps {
  richUi: ConfigRichDropdownUi;
  selectedValue: string;
  hasOverride?: boolean;
  onSelect: (value: string) => void;
  onCustomValue: (value: string) => void;
  onReset?: () => void;
  onRequestClose: () => void;
  renderIcon?: MenuIconRenderer;
  testIDPrefix?: string;
}

export function RichConfigDropdownPanel(
  props: RichConfigDropdownPanelProps,
): React.JSX.Element {
  const theme = useTheme();
  const colors = useMemo(
    () => ({
      border: theme.border,
      text: theme.text,
      secondaryText: theme.textSecondary,
      selectedBackground: theme.surfaceAlt,
      primary: theme.primary,
      danger: theme.danger,
      surface: theme.surface,
    }),
    [theme],
  );
  const selectedIsDeclared = props.richUi.options.some(
    (option) => option.value === props.selectedValue,
  );
  const [customValue, setCustomValue] = useState(
    selectedIsDeclared ? "" : props.selectedValue,
  );
  const prefix = props.testIDPrefix ?? "rich-config-dropdown";

  return (
    <View
      testID={prefix}
      style={[styles.panel, { backgroundColor: colors.surface }]}
    >
      <View style={[styles.panelHeader, { borderBottomColor: colors.border }]}>
        <View style={styles.panelTitleColumn}>
          <Text style={[styles.panelTitle, { color: colors.text }]}>
            {props.richUi.label}
          </Text>
          {props.richUi.description ? (
            <Text
              style={[styles.panelDescription, { color: colors.secondaryText }]}
            >
              {props.richUi.description}
            </Text>
          ) : null}
        </View>
        <Pressable
          testID={`${prefix}-close`}
          accessibilityRole="button"
          accessibilityLabel={`Close ${props.richUi.label}`}
          onPress={props.onRequestClose}
        >
          <Text style={[styles.closeText, { color: colors.primary }]}>×</Text>
        </Pressable>
      </View>

      <ScrollView keyboardShouldPersistTaps="handled" style={styles.options}>
        {props.richUi.options.map((option) => {
          const selected = option.value === props.selectedValue;
          return (
            <TouchableOpacity
              key={option.value}
              testID={`${prefix}-option-${option.value}`}
              accessibilityRole="button"
              accessibilityLabel={`${option.label}${selected ? " selected" : ""}`}
              accessibilityState={{ selected }}
              style={[
                styles.option,
                selected && { backgroundColor: colors.selectedBackground },
              ]}
              onPress={() => props.onSelect(option.value)}
            >
              {option.icon && props.renderIcon
                ? props.renderIcon({
                    name: option.icon,
                    size: 16,
                    color: colors.primary,
                  })
                : null}
              <Text style={[styles.optionText, { color: colors.text }]}>
                {option.label}
              </Text>
              {selected ? (
                <Text style={[styles.selectedMark, { color: colors.primary }]}>
                  ✓
                </Text>
              ) : null}
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {props.richUi.allow_custom_value ? (
        <View style={[styles.customSection, { borderTopColor: colors.border }]}>
          <Text style={[styles.customLabel, { color: colors.text }]}>
            {props.richUi.custom_value_label ?? "Other value…"}
          </Text>
          <TextInput
            testID={`${prefix}-custom-input`}
            accessibilityLabel={
              props.richUi.custom_value_label ?? `Custom ${props.richUi.label}`
            }
            style={[
              styles.customInput,
              {
                borderColor: colors.border,
                color: colors.text,
                backgroundColor: colors.surface,
              },
            ]}
            value={customValue}
            placeholder={
              props.richUi.custom_value_placeholder ?? "Enter a value"
            }
            placeholderTextColor={colors.secondaryText}
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setCustomValue}
          />
          <Pressable
            testID={`${prefix}-custom-submit`}
            accessibilityRole="button"
            accessibilityLabel={`Use custom ${props.richUi.label}`}
            disabled={!customValue.trim()}
            style={[
              styles.primaryButton,
              { backgroundColor: colors.primary },
              !customValue.trim() && styles.disabledButton,
            ]}
            onPress={() => props.onCustomValue(customValue.trim())}
          >
            <Text style={styles.primaryButtonText}>Use value</Text>
          </Pressable>
        </View>
      ) : null}

      {props.hasOverride && props.onReset ? (
        <Pressable
          testID={`${prefix}-reset`}
          accessibilityRole="button"
          accessibilityLabel={`Reset ${props.richUi.label}`}
          style={styles.resetButton}
          onPress={props.onReset}
        >
          <Text style={[styles.resetText, { color: colors.danger }]}>
            Reset to configured value
          </Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  control: {
    minHeight: 30,
    maxWidth: 220,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  controlLabel: {
    fontSize: 11,
    fontWeight: "600",
  },
  controlValue: {
    flexShrink: 1,
    fontSize: 12,
    fontWeight: "700",
  },
  chevron: {
    fontSize: 11,
  },
  panel: {
    flex: 1,
    minWidth: 280,
  },
  panelHeader: {
    minHeight: 48,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  panelTitleColumn: {
    flex: 1,
    gap: 2,
  },
  panelTitle: {
    fontSize: 15,
    fontWeight: "800",
  },
  panelDescription: {
    fontSize: 12,
  },
  closeText: {
    fontSize: 22,
    fontWeight: "700",
    paddingHorizontal: 6,
  },
  options: {
    maxHeight: 280,
  },
  option: {
    minHeight: 44,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  optionText: {
    flex: 1,
    fontSize: 14,
    fontWeight: "600",
  },
  selectedMark: {
    fontSize: 16,
    fontWeight: "800",
  },
  customSection: {
    borderTopWidth: StyleSheet.hairlineWidth,
    padding: 14,
    gap: 8,
  },
  customLabel: {
    fontSize: 13,
    fontWeight: "700",
  },
  customInput: {
    minHeight: 38,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
  },
  primaryButton: {
    alignSelf: "flex-end",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  disabledButton: {
    opacity: 0.45,
  },
  primaryButtonText: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
  resetButton: {
    alignSelf: "flex-start",
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  resetText: {
    fontSize: 13,
    fontWeight: "700",
  },
});
