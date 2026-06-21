import React, { useMemo, useState } from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';

import { useTheme, type Theme } from '../theme';

export type OptionItem = { value: string; label: string };

export interface OptionsPickerModalProps {
  visible: boolean;
  options: OptionItem[];
  onSelect: (value: string) => void;
  onRequestClose: () => void;
  useModal?: boolean;
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
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [search, setSearch] = useState('');

  const filteredOptions = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return options;
    return options.filter((opt) => {
      const text = `${opt.label ?? ''} ${opt.value ?? ''}`.toLowerCase();
      return text.includes(q);
    });
  }, [options, search]);

  if (!visible) return null;

  const handleSelect = (value: string) => {
    onSelect(value);
    setSearch('');
  };

  const handleClose = () => {
    setSearch('');
    onRequestClose();
  };

  const content = (
    <TouchableWithoutFeedback onPress={handleClose}>
      <View style={styles.overlay}>
        <TouchableWithoutFeedback onPress={() => {}}>
          <View style={styles.content}>
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
                  onPress={() => handleSelect(opt.value)}
                >
                  <Text style={styles.itemText} numberOfLines={2}>
                    {opt.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={handleClose}
            >
              <Text style={styles.buttonTextSecondary}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </TouchableWithoutFeedback>
      </View>
    </TouchableWithoutFeedback>
  );

  if (!useModal) {
    return content;
  }

  return (
    <Modal visible transparent animationType="fade" onRequestClose={handleClose}>
      {content}
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      ...StyleSheet.absoluteFillObject,
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
      fontSize: 14,
      color: theme.text,
      backgroundColor: theme.surface,
      marginBottom: 8,
    },
    list: {
      maxHeight: 320,
      marginVertical: 8,
    },
    item: {
      paddingVertical: 12,
      paddingHorizontal: 8,
      borderBottomWidth: 1,
      borderBottomColor: theme.border,
    },
    itemText: {
      fontSize: 14,
      color: theme.text,
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
    buttonTextSecondary: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.text,
    },
  });

export default OptionsPickerModal;
