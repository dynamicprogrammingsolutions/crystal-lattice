import React, { useMemo, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  createConfigDropdownSuggestionEngine,
  resolveConfigRichToggleOption,
  type ConfigRichDropdownUi,
  type ConfigRichToggleUi,
  type ConfigRichUiControl,
} from '@crystal-lattice/frontend-sdk';

import { useTheme } from '../theme';
import type { MenuIconRenderer } from './ActionsMenuContent';
import { resolveSemanticToneColor } from './semanticTone';

export interface RichConfigDropdownControlProps {
  control: ConfigRichUiControl;
  value: unknown;
  disabled?: boolean;
  placement: string;
  onPress: () => void;
  renderIcon?: MenuIconRenderer;
  testID?: string;
  buttonRef?: React.Ref<any>;
  maxValueCharacters?: number;
}

export function truncatePinnedValue(
  value: string,
  maximum: number | undefined,
): string {
  const characters = Array.from(value);
  if (
    maximum === undefined ||
    !Number.isFinite(maximum) ||
    maximum <= 0 ||
    characters.length <= maximum
  ) {
    return value;
  }
  const limit = Math.max(1, Math.floor(maximum));
  if (limit === 1) {
    return '…';
  }
  return `${characters.slice(0, limit - 1).join('')}…`;
}

export function RichConfigDropdownControl(
  props: RichConfigDropdownControlProps,
): React.JSX.Element | null {
  const theme = useTheme();
  if (props.control.richUi.kind !== 'dropdown') {
    return null;
  }
  const richUi = props.control.richUi as ConfigRichDropdownUi;
  const value =
    props.value === undefined || props.value === null
      ? ''
      : String(props.value);
  const selectedOption = richUi.options.find(
    (option) => option.value === value,
  );
  const selectedLabel = selectedOption?.label ?? value;
  const compactLabel = truncatePinnedValue(
    selectedLabel || 'Not set',
    props.maxValueCharacters,
  );
  const color = props.disabled
    ? theme.textMuted
    : resolveSemanticToneColor(theme, selectedOption?.tone);
  const icon = selectedOption?.icon ?? richUi.icon;
  const testID =
    props.testID ??
    `rich-config-${props.control.element.key}-${props.placement}`;

  return (
    <TouchableOpacity
      ref={props.buttonRef}
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={`${richUi.label}: ${selectedLabel || 'Not set'}`}
      accessibilityState={{ disabled: props.disabled }}
      disabled={props.disabled}
      style={[
        styles.control,
        { borderColor: theme.border, backgroundColor: theme.surfaceAlt },
      ]}
      onPress={props.onPress}
    >
      {icon && props.renderIcon
        ? props.renderIcon({
            name: icon,
            size: 14,
            color,
          })
        : null}
      {richUi.show_label !== false ? (
        <Text
          numberOfLines={1}
          style={[
            styles.controlLabel,
            { color: props.disabled ? theme.textMuted : theme.textSecondary },
          ]}
        >
          {richUi.label}:
        </Text>
      ) : null}
      <Text numberOfLines={1} style={[styles.controlValue, { color }]}>
        {compactLabel}
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

export interface RichConfigToggleControlProps {
  control: ConfigRichUiControl;
  value: unknown;
  disabled?: boolean;
  placement: string;
  onPress: () => void;
  renderIcon?: MenuIconRenderer;
  testID?: string;
}

export function RichConfigToggleControl(
  props: RichConfigToggleControlProps,
): React.JSX.Element | null {
  const theme = useTheme();
  if (props.control.richUi.kind !== 'toggle') {
    return null;
  }
  const richUi = props.control.richUi as ConfigRichToggleUi;
  const option = resolveConfigRichToggleOption(richUi, props.value);
  const color = props.disabled
    ? theme.textMuted
    : resolveSemanticToneColor(
        theme,
        option.tone ?? (option.value ? 'success' : 'primary'),
      );
  const icon = option.icon ?? richUi.icon;
  const testID =
    props.testID ??
    `rich-config-${props.control.element.key}-${props.placement}`;

  return (
    <TouchableOpacity
      testID={testID}
      accessibilityRole="switch"
      accessibilityLabel={`${richUi.label}: ${option.label}`}
      accessibilityState={{
        disabled: props.disabled,
        checked: option.value,
      }}
      disabled={props.disabled}
      style={[
        styles.control,
        styles.toggleControl,
        { borderColor: theme.border, backgroundColor: theme.surfaceAlt },
      ]}
      onPress={props.onPress}
    >
      {icon && props.renderIcon
        ? props.renderIcon({ name: icon, size: 15, color })
        : null}
      {richUi.show_label !== false ? (
        <>
          <Text
            numberOfLines={1}
            style={[styles.controlLabel, { color: theme.textSecondary }]}
          >
            {richUi.label}:
          </Text>
          <Text numberOfLines={1} style={[styles.controlValue, { color }]}>
            {option.label}
          </Text>
        </>
      ) : null}
    </TouchableOpacity>
  );
}

export interface RichConfigDropdownPanelProps {
  richUi: ConfigRichDropdownUi;
  selectedValue: string;
  hasOverride?: boolean;
  onSelect: (value: string) => void;
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
  const [query, setQuery] = useState(
    selectedIsDeclared ? '' : props.selectedValue,
  );
  const suggestionEngine = useMemo(
    () => createConfigDropdownSuggestionEngine(props.richUi),
    [props.richUi],
  );
  const suggestions = useMemo(
    () => suggestionEngine.suggestions(query),
    [query, suggestionEngine],
  );
  const prefix = props.testIDPrefix ?? 'rich-config-dropdown';
  const submitQuery = () => {
    const candidate = query.trim();
    const exact = suggestions.find((option) => option.value === candidate);
    if (exact) {
      props.onSelect(exact.value);
    }
  };

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

      <View
        style={[styles.searchSection, { borderBottomColor: colors.border }]}
      >
        <TextInput
          testID={`${prefix}-input`}
          accessibilityLabel={
            props.richUi.placeholder ?? `Search or enter ${props.richUi.label}`
          }
          style={[
            styles.searchInput,
            {
              borderColor: colors.border,
              color: colors.text,
              backgroundColor: colors.surface,
            },
          ]}
          value={query}
          placeholder={
            props.richUi.placeholder ?? `Search or enter ${props.richUi.label}`
          }
          placeholderTextColor={colors.secondaryText}
          autoCapitalize="none"
          autoCorrect={false}
          returnKeyType="done"
          onChangeText={setQuery}
          onSubmitEditing={submitQuery}
        />
      </View>

      <ScrollView keyboardShouldPersistTaps="handled" style={styles.options}>
        {suggestions.map((option) => {
          const selected = option.value === props.selectedValue;
          const color = resolveSemanticToneColor(theme, option.tone);
          return (
            <TouchableOpacity
              key={`${option.kind}:${option.value}`}
              testID={`${prefix}-${option.kind}-${option.value}`}
              accessibilityRole="button"
              accessibilityLabel={`${option.label}${selected ? ' selected' : ''}`}
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
                    color,
                  })
                : null}
              <Text style={[styles.optionText, { color }]}>{option.label}</Text>
              {selected ? (
                <Text style={[styles.selectedMark, { color: colors.primary }]}>
                  ✓
                </Text>
              ) : null}
            </TouchableOpacity>
          );
        })}
        {suggestions.length === 0 ? (
          <Text style={[styles.emptyText, { color: colors.secondaryText }]}>
            No matching options
          </Text>
        ) : null}
      </ScrollView>

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
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  toggleControl: {
    minWidth: 34,
  },
  controlLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  controlValue: {
    flexShrink: 1,
    fontSize: 12,
    fontWeight: '700',
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  panelTitleColumn: {
    flex: 1,
    gap: 2,
  },
  panelTitle: {
    fontSize: 15,
    fontWeight: '800',
  },
  panelDescription: {
    fontSize: 12,
  },
  closeText: {
    fontSize: 22,
    fontWeight: '700',
    paddingHorizontal: 6,
  },
  options: {
    maxHeight: 280,
  },
  searchSection: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    padding: 12,
  },
  searchInput: {
    minHeight: 38,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
  },
  option: {
    minHeight: 44,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  optionText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
  },
  selectedMark: {
    fontSize: 16,
    fontWeight: '800',
  },
  emptyText: {
    paddingHorizontal: 14,
    paddingVertical: 18,
    fontSize: 13,
  },
  resetButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  resetText: {
    fontSize: 13,
    fontWeight: '700',
  },
});
