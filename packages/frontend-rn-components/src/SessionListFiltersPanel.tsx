import React, { useMemo } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import type {
  SessionListFilterElement,
  SessionListFilterSchema,
  SessionListFilterValues,
  SessionListOption,
} from '@crystal-lattice/frontend-sdk';
import { validateSessionListFilterValue } from '@crystal-lattice/frontend-sdk';

import { useTheme } from './theme';

export interface SessionListFiltersPanelProps {
  schema: SessionListFilterSchema;
  values: SessionListFilterValues;
  onChange: (filterId: string, value: unknown) => void;
  onReset: () => void;
  onShowAll: () => void;
  onRequestClose?: () => void;
  renderIcon?: (props: {
    name: string;
    size: number;
    color: string;
  }) => React.ReactNode;
}

function booleanLabel(
  filter: SessionListFilterElement,
  value: boolean,
): string {
  const option = filter.options.find((candidate) => candidate.value === value);
  return option?.label ?? (value ? 'True' : 'False');
}

function isSelected(value: unknown, option: SessionListOption): boolean {
  return typeof value === typeof option.value && value === option.value;
}

function DatetimeFilterInput({
  filter,
  value,
  onChange,
  style,
  placeholderTextColor,
}: {
  filter: SessionListFilterElement;
  value: unknown;
  onChange: (filterId: string, value: unknown) => void;
  style: any;
  placeholderTextColor: string;
}): React.JSX.Element {
  const externalValue = typeof value === 'string' ? value : '';
  const [draft, setDraft] = React.useState(externalValue);
  const [error, setError] = React.useState<string | null>(null);
  React.useEffect(() => {
    setDraft(externalValue);
    setError(null);
  }, [externalValue]);
  const commit = React.useCallback(() => {
    const normalized = draft.trim();
    const nextValue = normalized || null;
    const nextError = validateSessionListFilterValue(filter, nextValue);
    setError(nextError);
    if (nextError === null) {
      onChange(filter.id, nextValue);
    }
  }, [draft, filter, onChange]);

  return (
    <View>
      <TextInput
        testID={`session-filter-${filter.id}-datetime`}
        accessibilityLabel={filter.label}
        style={style}
        value={draft}
        placeholder="2026-09-01T00:00:00Z"
        placeholderTextColor={placeholderTextColor}
        onChangeText={setDraft}
        onBlur={commit}
        onSubmitEditing={commit}
        autoCapitalize="none"
        autoCorrect={false}
      />
      {error ? (
        <Text
          testID={`session-filter-${filter.id}-datetime-error`}
          style={{ color: placeholderTextColor }}
        >
          {error}
        </Text>
      ) : null}
    </View>
  );
}

export function SessionListFiltersPanel({
  schema,
  values,
  onChange,
  onReset,
  onShowAll,
  onRequestClose,
  renderIcon,
}: SessionListFiltersPanelProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const filters = schema.filters.filter(
    (filter) => filter.id !== schema.mainSearch?.id,
  );

  const renderChoice = (
    filter: SessionListFilterElement,
    key: string,
    label: string,
    selected: boolean,
    nextValue: unknown,
    option?: SessionListOption,
  ) => (
    <TouchableOpacity
      key={key}
      testID={`session-filter-${filter.id}-option-${key}`}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      accessibilityLabel={`${filter.label}: ${label}${selected ? ', selected' : ''}`}
      style={[
        styles.choice,
        selected ? styles.choiceSelected : null,
        option?.tone
          ? {
              borderColor:
                option.tone === 'primary'
                  ? theme.primary
                  : option.tone === 'highlight'
                    ? theme.highlight
                  : option.tone === 'warning'
                    ? theme.warning
                    : option.tone === 'success'
                      ? theme.success
                      : option.tone === 'danger'
                        ? theme.danger
                        : theme.textMuted,
            }
          : null,
      ]}
      onPress={() => onChange(filter.id, nextValue)}
    >
      <View style={styles.choiceContent}>
        {option?.icon && renderIcon ? (
          <View testID={`session-filter-${filter.id}-option-${key}-icon`}>
            {renderIcon({
              name: option.icon,
              size: 14,
              color: selected ? theme.primary : theme.textSecondary,
            })}
          </View>
        ) : null}
        <Text
          style={[
            styles.choiceText,
            selected ? styles.choiceTextSelected : null,
          ]}
        >
          {selected ? '✓ ' : ''}
          {label}
        </Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.root} testID="session-filters-panel">
      <View style={styles.header}>
        <Text style={styles.title}>Session filters</Text>
        {onRequestClose ? (
          <TouchableOpacity
            testID="session-filters-close"
            accessibilityLabel="Close session filters"
            onPress={onRequestClose}
          >
            <Text style={styles.closeText}>Close</Text>
          </TouchableOpacity>
        ) : null}
      </View>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        {filters.map((filter) => {
          const value = values[filter.id];
          return (
            <View
              key={filter.id}
              style={styles.filter}
              testID={`session-filter-${filter.id}`}
            >
              <Text style={styles.label}>{filter.label}</Text>
              {filter.type === 'text' ? (
                <TextInput
                  testID={`session-filter-${filter.id}-text`}
                  accessibilityLabel={filter.label}
                  style={styles.textInput}
                  value={typeof value === 'string' ? value : ''}
                  onChangeText={(next) => onChange(filter.id, next)}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              ) : null}
              {filter.type === 'datetime' ? (
                <DatetimeFilterInput
                  filter={filter}
                  value={value}
                  onChange={onChange}
                  style={styles.textInput}
                  placeholderTextColor={theme.textMuted}
                />
              ) : null}
              {filter.type === 'boolean' ? (
                <View style={styles.choices}>
                  {renderChoice(filter, 'any', 'Any', value === null, null)}
                  {renderChoice(
                    filter,
                    'true',
                    booleanLabel(filter, true),
                    value === true,
                    true,
                    filter.options.find((option) => option.value === true),
                  )}
                  {renderChoice(
                    filter,
                    'false',
                    booleanLabel(filter, false),
                    value === false,
                    false,
                    filter.options.find((option) => option.value === false),
                  )}
                </View>
              ) : null}
              {filter.type === 'select' && !filter.multiple ? (
                <View style={styles.choices}>
                  {renderChoice(filter, 'any', 'Any', value === null, null)}
                  {filter.options.map((option, index) =>
                    renderChoice(
                      filter,
                      String(index),
                      option.label,
                      isSelected(value, option),
                      option.value,
                      option,
                    ),
                  )}
                </View>
              ) : null}
              {filter.type === 'select' && filter.multiple ? (
                <View style={styles.choices}>
                  {renderChoice(
                    filter,
                    'any',
                    'Any',
                    Array.isArray(value) && value.length === 0,
                    [],
                  )}
                  {filter.options.map((option, index) => {
                    const selected =
                      Array.isArray(value) &&
                      value.some((item) => isSelected(item, option));
                    const next = selected
                      ? (value as unknown[]).filter(
                          (item) => !isSelected(item, option),
                        )
                      : [...(Array.isArray(value) ? value : []), option.value];
                    return renderChoice(
                      filter,
                      String(index),
                      option.label,
                      selected,
                      next,
                      option,
                    );
                  })}
                </View>
              ) : null}
            </View>
          );
        })}
      </ScrollView>
      <View style={styles.actions}>
        <TouchableOpacity
          testID="session-filters-show-all"
          accessibilityLabel="Show all sessions"
          style={styles.secondaryButton}
          onPress={onShowAll}
        >
          <Text style={styles.secondaryButtonText}>Show all</Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="session-filters-reset"
          accessibilityLabel="Reset session filters"
          style={styles.primaryButton}
          onPress={onReset}
        >
          <Text style={styles.primaryButtonText}>Reset</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      maxHeight: 560,
      minHeight: 180,
      backgroundColor: theme.surface,
      borderRadius: 12,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 16,
      paddingVertical: 12,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
    },
    title: {
      color: theme.text,
      fontSize: theme.typography.fontSize.title,
      fontWeight: '700',
    },
    closeText: {
      color: theme.primary,
      fontWeight: '600',
    },
    scroll: {
      flexGrow: 0,
      flexShrink: 1,
    },
    content: {
      padding: 14,
      gap: 16,
    },
    filter: {
      gap: 8,
    },
    label: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '700',
    },
    textInput: {
      minHeight: 38,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      color: theme.text,
      backgroundColor: theme.backgroundAlt,
    },
    choices: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
    },
    choice: {
      minHeight: 34,
      justifyContent: 'center',
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      backgroundColor: theme.surface,
    },
    choiceSelected: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    choiceText: {
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.secondary,
    },
    choiceContent: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 5,
    },
    choiceTextSelected: {
      color: theme.primary,
      fontWeight: '700',
    },
    actions: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 10,
      paddingHorizontal: 14,
      paddingVertical: 12,
      borderTopWidth: StyleSheet.hairlineWidth,
      borderTopColor: theme.border,
    },
    secondaryButton: {
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 14,
      paddingVertical: 9,
    },
    secondaryButtonText: {
      color: theme.text,
      fontWeight: '600',
    },
    primaryButton: {
      borderRadius: 8,
      paddingHorizontal: 14,
      paddingVertical: 9,
      backgroundColor: theme.primary,
    },
    primaryButtonText: {
      color: theme.textOnPrimary,
      fontWeight: '700',
    },
  });
}