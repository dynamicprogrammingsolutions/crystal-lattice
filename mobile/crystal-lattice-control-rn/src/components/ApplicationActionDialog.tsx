import React, { useEffect, useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useTheme, type Theme } from '../theme';
import { extractByPath } from '../uiSchemaUtils';

interface DialogInputField {
  name: string;
  type?: string;
  label?: string;
  placeholder?: string;
  default?: any;
  required?: boolean;
  description?: string;
  prefill_from?: string;
}

export interface ApplicationActionDialogPrefillContext {
  session?: any;
  message?: any;
}

export interface ApplicationActionDialogProps {
  visible: boolean;
  dialog: any;
  titleFallback?: string;
  prefillContext?: ApplicationActionDialogPrefillContext;
  onSubmit: (values: Record<string, any>) => void;
  onCancel: () => void;
}

const ApplicationActionDialog: React.FC<ApplicationActionDialogProps> = ({
  visible,
  dialog,
  titleFallback,
  prefillContext,
  onSubmit,
  onCancel,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const kind: string = dialog && typeof dialog.kind === 'string' ? dialog.kind : 'none';

  const inputs: DialogInputField[] =
    kind === 'form' && dialog && Array.isArray(dialog.inputs)
      ? (dialog.inputs as DialogInputField[])
      : []

  const [valuesByName, setValuesByName] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible || kind !== 'form') {
      setValuesByName({});
      setError(null);
      return;
    }
    const initial: Record<string, string> = {};
    inputs.forEach((field) => {
      const key = field.name;
      if (!key) return;
      const def = field.default;

      // Optional prefill resolution based on ``prefill_from`` hints. This
      // allows dialogs to derive defaults from the current session or
      // message context without each caller having to rewrite the schema.
      let prefilled: string | undefined;
      const src = field.prefill_from;
      if (typeof src === 'string' && src) {
        let root: any = null;
        let path: string | null = null;
        if (src.startsWith('$session.')) {
          root = prefillContext?.session;
          path = src.slice('$session.'.length);
        } else if (src.startsWith('$message.')) {
          root = prefillContext?.message;
          path = src.slice('$message.'.length);
        }
        if (root && path) {
          const value = extractByPath(root, path);
          if (value !== undefined && value !== null && value !== '') {
            prefilled = String(value);
          }
        }
      }

      let value: string;
      if (
        prefilled !== undefined &&
        (def === undefined || def === null || String(def) === '')
      ) {
        value = prefilled;
      } else if (def === undefined || def === null) {
        value = '';
      } else if (typeof def === 'string') {
        value = def;
      } else {
        value = String(def);
      }

      initial[key] = value;
    });
    setValuesByName(initial);
    setError(null);
  }, [visible, dialog, prefillContext]);

  if (!visible || !dialog || kind === 'none') {
    return null;
  }

  const title: string =
    (typeof dialog.title === 'string' && dialog.title) || titleFallback || 'Action';
  const message: string | null =
    typeof dialog.message === 'string' && dialog.message ? dialog.message : null;

  const handleChange = (name: string, text: string) => {
    setValuesByName((prev) => ({ ...prev, [name]: text }));
  };

  const parseBoolean = (raw: string): boolean | null => {
    const value = raw.trim().toLowerCase();
    if (!value) return null;
    if (value === 'true' || value === '1' || value === 'yes' || value === 'y') return true;
    if (value === 'false' || value === '0' || value === 'no' || value === 'n') return false;
    return null;
  };

  const handlePrimary = () => {
    if (kind !== 'form') {
      setError(null);
      onSubmit({});
      return;
    }

    const result: Record<string, any> = {};

    for (const field of inputs) {
      const name = field.name;
      if (!name) continue;
      const raw = valuesByName[name] ?? '';
      const trimmed = raw.trim();

      if (!trimmed) {
        if (field.required) {
          const label = field.label || name;
          setError(`Field "${label}" is required.`);
          return;
        }
        continue;
      }

      const fType = typeof field.type === 'string' ? field.type : 'string';
      let parsed: any = trimmed;

      if (fType === 'integer') {
        const n = parseInt(trimmed, 10);
        if (Number.isNaN(n)) {
          const label = field.label || name;
          setError(`Field "${label}" must be an integer.`);
          return;
        }
        parsed = n;
      } else if (fType === 'number') {
        const n = parseFloat(trimmed);
        if (Number.isNaN(n)) {
          const label = field.label || name;
          setError(`Field "${label}" must be a number.`);
          return;
        }
        parsed = n;
      } else if (fType === 'boolean') {
        const b = parseBoolean(trimmed);
        if (b === null) {
          const label = field.label || name;
          setError(`Field "${label}" must be true/false.`);
          return;
        }
        parsed = b;
      }

      result[name] = parsed;
    }

    setError(null);
    onSubmit(result);
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <KeyboardAvoidingView
        style={styles.modalOverlay}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={16}
      >
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>{title}</Text>
          {message ? <Text style={styles.modalSubtitle}>{message}</Text> : null}
          {kind === 'form' &&
            inputs.map((field) => {
              const name = field.name;
              if (!name) return null;
              const label = field.label || name;
              const placeholder = field.placeholder || '';
              const description = field.description || '';
              const value = valuesByName[name] ?? '';
              const fType = typeof field.type === 'string' ? field.type : 'string';
              const isMultiline = fType === 'multiline';

              return (
                <View key={name} style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>{label}</Text>
                  {description ? (
                    <Text style={styles.inputDescription}>{description}</Text>
                  ) : null}
                  <TextInput
                    style={isMultiline ? styles.modalInputMultiline : styles.modalInput}
                    value={value}
                    onChangeText={(text) => handleChange(name, text)}
                    placeholder={placeholder}
                    placeholderTextColor={theme.textSecondary}
                    multiline={isMultiline}
                    textAlignVertical={isMultiline ? 'top' : 'center'}
                  />
                </View>
              );
            })}
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          <View style={styles.modalButtonsRow}>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton, styles.modalButton]}
              onPress={onCancel}
            >
              <Text style={styles.buttonTextSecondary}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.primaryButton, styles.modalButton]}
              onPress={handlePrimary}
            >
              <Text style={styles.buttonText}>OK</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modalOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    modalContent: {
      width: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: 12,
      color: theme.textSecondary,
      marginBottom: 12,
    },
    modalInput: {
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      fontSize: 14,
      marginTop: 4,
      color: theme.text,
    },
    modalInputMultiline: {
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      fontSize: 14,
      marginTop: 4,
      color: theme.text,
      minHeight: 80,
    },
    modalButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      marginTop: 12,
    },
    modalButton: {
      minWidth: 90,
      alignItems: 'center',
      marginLeft: 8,
    },
    button: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: 14,
      fontWeight: '600',
    },
    buttonTextSecondary: {
      color: theme.text,
      fontSize: 14,
      fontWeight: '600',
    },
    inputGroup: {
      marginBottom: 8,
    },
    inputLabel: {
      fontSize: 12,
      color: theme.text,
    },
    inputDescription: {
      fontSize: 11,
      color: theme.textSecondary,
      marginTop: 2,
    },
    errorText: {
      marginTop: 4,
      fontSize: 12,
      color: theme.danger,
    },
  });

export default ApplicationActionDialog;
