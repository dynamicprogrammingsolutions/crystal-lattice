import React, { useEffect, useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Keyboard,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import {
  createConfigDropdownSuggestionEngine,
  type ConfigCustomValue,
  type RichDropdownOption,
} from '@crystal-lattice/frontend-sdk';
import { resolveSemanticToneColor } from '@crystal-lattice/frontend-rn-components';

import { useTheme, type Theme } from '../theme';

export type OptionItem = RichDropdownOption;

export interface OptionsPickerModalProps {
  visible: boolean;
  options: readonly OptionItem[];
  onSelect: (value: string) => void;
  onRequestClose: () => void;
  useModal?: boolean;
  selectedValue?: string;
  placeholder?: string;
  customValue?: ConfigCustomValue;
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
  selectedValue = '',
  placeholder = 'Search or enter a value',
  customValue,
  showReset = false,
  resetLabel = 'Reset to configured value',
  onReset,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!visible) {
      return;
    }
    const selectedIsDeclared = options.some(
      (option) => option.value === selectedValue
    );
    setSearch(selectedIsDeclared ? '' : selectedValue);
  }, [options, selectedValue, visible]);

  const suggestionEngine = useMemo(
    () =>
      createConfigDropdownSuggestionEngine({
        options,
        placeholder,
        ...(customValue ? { custom_value: customValue } : {}),
      }),
    [customValue, options, placeholder]
  );
  const suggestions = useMemo(
    () => suggestionEngine.suggestions(search),
    [search, suggestionEngine]
  );

  if (!visible) return null;

  const handleSelect = (value: string) => {
    Keyboard.dismiss();
    onSelect(value);
    setSearch('');
  };
  const handleSubmit = () => {
    const candidate = search.trim();
    const exact = suggestions.find((option) => option.value === candidate);
    if (exact) {
      handleSelect(exact.value);
    }
  };

  const handleClose = () => {
    Keyboard.dismiss();
    setSearch('');
    onRequestClose();
  };

  const content = (
    <TouchableWithoutFeedback onPress={handleClose}>
      <View style={styles.overlay}>
        <TouchableWithoutFeedback onPress={() => {}}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.content}
          >
            <TextInput
              style={styles.searchInput}
              accessibilityLabel={placeholder}
              testID="options-picker-input"
              placeholder={placeholder}
              placeholderTextColor={theme.textSecondary}
              value={search}
              onChangeText={setSearch}
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="done"
              onSubmitEditing={handleSubmit}
            />
            <ScrollView style={styles.list} keyboardShouldPersistTaps="handled">
              {suggestions.map((opt) => {
                const color = resolveSemanticToneColor(theme, opt.tone);
                return (
                  <TouchableOpacity
                    key={`${opt.kind}:${opt.value}`}
                    style={styles.item}
                    accessibilityRole="button"
                    accessibilityLabel={opt.label}
                    testID={`options-picker-${opt.kind}-${opt.value}`}
                    onPress={() => handleSelect(opt.value)}
                  >
                    {opt.icon ? (
                      <Icon name={opt.icon} size={16} color={color} />
                    ) : null}
                    <Text
                      style={[styles.itemText, { color }]}
                      numberOfLines={2}
                    >
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
            {showReset && onReset ? (
              <TouchableOpacity
                testID="options-picker-reset"
                accessibilityRole="button"
                accessibilityLabel={resetLabel}
                style={styles.resetButton}
                onPress={() => {
                  onReset();
                  setSearch('');
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
      zIndex: 1000,
      elevation: 24,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    content: {
      width: '85%',
      maxHeight: '70%',
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
      fontWeight: '700',
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
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    itemText: {
      flex: 1,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
    button: {
      marginTop: 8,
      alignSelf: 'flex-end',
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
      fontWeight: '600',
      color: theme.textOnPrimary,
    },
    resetButton: {
      alignSelf: 'flex-start',
      paddingHorizontal: 8,
      paddingVertical: 8,
    },
    resetButtonText: {
      color: theme.danger,
      fontWeight: '700',
    },
    buttonTextSecondary: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
      color: theme.text,
    },
  });

export default OptionsPickerModal;
