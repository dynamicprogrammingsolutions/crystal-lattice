import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { extractByPath } from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from './theme';

interface DialogInputField {
  name: string;
  type?: string;
  label?: string;
  placeholder?: string;
  default?: any;
  required?: boolean;
  description?: string;
  prefill_from?: string;
  submit_empty?: boolean;
}

const EMPTY_INPUTS: DialogInputField[] = [];

export interface ActionDialogSubmitPayload {
  values: Record<string, any>;
  buttonId?: string;
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
  onSubmit: (payload: ActionDialogSubmitPayload) => void;
  onCancel: () => void;
}

export type ApplicationActionDialogDensity = 'default' | 'compact';

export interface ApplicationActionDialogLayoutProps
  extends Omit<ApplicationActionDialogProps, 'visible'> {
  style?: StyleProp<ViewStyle>;
  /** When false, the Cancel control is omitted (e.g. inline tool prompts). Default true. */
  showCancelButton?: boolean;
  /** When true, all actions are non-interactive (e.g. while submitting). */
  disabled?: boolean;
  /**
   * Visual density for inline / embedded dialogs. Does not change dialog structure or
   * button ids/labels (still driven by `dialog` from the backend).
   */
  density?: ApplicationActionDialogDensity;
}

export function ApplicationActionDialogLayout({
  dialog,
  titleFallback,
  prefillContext,
  onSubmit,
  onCancel,
  style,
  showCancelButton = true,
  disabled = false,
  density = 'default',
}: ApplicationActionDialogLayoutProps): React.JSX.Element | null {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, density), [theme, density]);

  const kind: string = dialog && typeof dialog.kind === 'string' ? dialog.kind : 'none';

  const customButtons = useMemo(() => {
    if (!dialog || !Array.isArray((dialog as any).buttons)) {
      return [] as Array<{ id: string; label: string; default?: boolean }>;
    }
    const out: Array<{ id: string; label: string; default?: boolean }> = [];
    for (const raw of (dialog as any).buttons) {
      if (!raw || typeof raw !== 'object') continue;
      const id = typeof (raw as any).id === 'string' ? (raw as any).id : '';
      const label = typeof (raw as any).label === 'string' ? (raw as any).label : '';
      if (!id || !label) continue;
      out.push({ id, label, default: (raw as any).default === true });
    }
    return out;
  }, [dialog]);

  const hasCustomButtons = customButtons.length > 0;

  const inputs: DialogInputField[] = useMemo(() => {
    if (kind !== 'form' || !dialog || !Array.isArray(dialog.inputs)) {
      return EMPTY_INPUTS;
    }
    return dialog.inputs as DialogInputField[];
  }, [dialog, kind]);

  const [valuesByName, setValuesByName] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const initialValuesByNameRef = useRef<Record<string, string>>({});

  const firstInputRef = useRef<TextInput | null>(null);
  const submitCaptureRef = useRef<TextInput | null>(null);

  const lastDialogRef = useRef<any>(null);

  useEffect(() => {
    if (!dialog || kind === 'none') {
      lastDialogRef.current = dialog;
      setValuesByName((prev) => (Object.keys(prev).length === 0 ? prev : {}));
      setError((prev) => (prev === null ? prev : null));
      return;
    }

    const shouldReset = lastDialogRef.current !== dialog;
    lastDialogRef.current = dialog;
    if (!shouldReset) {
      return;
    }

    if (kind !== 'form') {
      setValuesByName({});
      initialValuesByNameRef.current = {};
      setError(null);
      return;
    }

    const initial: Record<string, string> = {};
    inputs.forEach((field) => {
      const key = field.name;
      if (!key) return;
      const def = field.default;

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
      if (prefilled !== undefined && (def === undefined || def === null || String(def) === '')) {
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
    initialValuesByNameRef.current = initial;
    setError(null);
  }, [dialog, inputs, kind, prefillContext]);

  useEffect(() => {
    if (Platform.OS !== 'macos') {
      return;
    }
    if (!dialog || kind === 'none') {
      return;
    }

    const timer = setTimeout(() => {
      // Ensure keyboard focus lands inside the dialog so Return/Enter
      // does not trigger underlying UI (e.g. chat composer).
      if (kind !== 'form' || inputs.length === 0) {
        submitCaptureRef.current?.focus();
        return;
      }

      firstInputRef.current?.focus();
    }, 0);

    return () => {
      clearTimeout(timer);
    };
  }, [dialog, kind, inputs.length]);

  if (!dialog || kind === 'none') {
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

  const buildFormValues = (): Record<string, any> | null => {
    if (kind !== 'form') {
      return {};
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
          return null;
        }

        const fieldType = typeof field.type === 'string' ? field.type : 'string';
        const canSubmitEmpty = field.submit_empty === true;
        const initialTrimmed = (initialValuesByNameRef.current?.[name] ?? '').trim();
        const shouldSendEmptyToClear = !!initialTrimmed;
        if (
          (canSubmitEmpty || shouldSendEmptyToClear) &&
          (fieldType === 'string' || fieldType === 'multiline')
        ) {
          result[name] = '';
        }
        continue;
      }

      const fieldType = typeof field.type === 'string' ? field.type : 'string';
      let parsed: any = trimmed;

      if (fieldType === 'integer') {
        const numberValue = parseInt(trimmed, 10);
        if (Number.isNaN(numberValue)) {
          const label = field.label || name;
          setError(`Field "${label}" must be an integer.`);
          return null;
        }
        parsed = numberValue;
      } else if (fieldType === 'number') {
        const numberValue = parseFloat(trimmed);
        if (Number.isNaN(numberValue)) {
          const label = field.label || name;
          setError(`Field "${label}" must be a number.`);
          return null;
        }
        parsed = numberValue;
      } else if (fieldType === 'boolean') {
        const boolValue = parseBoolean(trimmed);
        if (boolValue === null) {
          const label = field.label || name;
          setError(`Field "${label}" must be true/false.`);
          return null;
        }
        parsed = boolValue;
      }

      result[name] = parsed;
    }

    return result;
  };

  const handlePrimary = () => {
    if (hasCustomButtons) {
      const def = customButtons.find((b) => b.default) ?? customButtons[0];
      if (def) {
        handleCustomButton(def.id);
      }
      return;
    }

    if (kind !== 'form') {
      setError(null);
      onSubmit({ values: {} });
      return;
    }

    const built = buildFormValues();
    if (built === null) {
      return;
    }
    setError(null);
    onSubmit({ values: built });
  };

  const handleCustomButton = (buttonId: string) => {
    if (kind === 'form') {
      const built = buildFormValues();
      if (built === null) {
        return;
      }
      setError(null);
      onSubmit({ values: built, buttonId });
      return;
    }
    setError(null);
    onSubmit({ values: {}, buttonId });
  };

  const handleSubmitCapture = () => {
    if (hasCustomButtons) {
      const def = customButtons.find((b) => b.default) ?? customButtons[0];
      if (def) {
        handleCustomButton(def.id);
      }
      return;
    }
    handlePrimary();
  };

  return (
    <View style={[styles.dialogCard, style]}>
      {Platform.OS === 'macos' ? (
        <TextInput
          ref={(node) => {
            submitCaptureRef.current = node;
          }}
          style={styles.submitCapture}
          value=""
          onChangeText={() => {}}
          blurOnSubmit={false}
          onSubmitEditing={() => handleSubmitCapture()}
        />
      ) : null}

      <Text style={styles.modalTitle}>{title}</Text>
      {message ? <Text style={styles.modalSubtitle}>{message}</Text> : null}

      {kind === 'form'
        ? inputs.map((field) => {
            const name = field.name;
            if (!name) return null;
            const label = field.label || name;
            const placeholder = field.placeholder || '';
            const description = field.description || '';
            const value = valuesByName[name] ?? '';
            const fieldType = typeof field.type === 'string' ? field.type : 'string';
            const isMultiline = fieldType === 'multiline';
            const isFirstField = inputs[0] === field;

            return (
              <View key={name} style={styles.inputGroup}>
                <Text style={styles.inputLabel}>{label}</Text>
                {description ? <Text style={styles.inputDescription}>{description}</Text> : null}
                <TextInput
                  ref={(node) => {
                    if (isFirstField) {
                      firstInputRef.current = node;
                    }
                  }}
                  style={isMultiline ? styles.modalInputMultiline : styles.modalInput}
                  value={value}
                  onChangeText={(text) => handleChange(name, text)}
                  placeholder={placeholder}
                  placeholderTextColor={theme.textSecondary}
                  editable={!disabled}
                  multiline={isMultiline}
                  textAlignVertical={isMultiline ? 'top' : 'center'}
                  blurOnSubmit={!isMultiline}
                  onSubmitEditing={() => {
                    if (Platform.OS !== 'macos') {
                      return;
                    }
                    if (isMultiline) {
                      return;
                    }
                    handleSubmitCapture();
                  }}
                />
              </View>
            );
          })
        : null}

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      {hasCustomButtons ? (
        <View style={styles.customButtonsColumn}>
          {customButtons.map((btn) => (
            <TouchableOpacity
              key={btn.id}
              style={[
                styles.button,
                btn.default ? styles.primaryButton : styles.secondaryButton,
                styles.customActionButton,
              ]}
              disabled={disabled}
              onPress={() => handleCustomButton(btn.id)}
            >
              <Text style={btn.default ? styles.buttonText : styles.buttonTextSecondary}>
                {btn.label}
              </Text>
            </TouchableOpacity>
          ))}
          {showCancelButton ? (
            <View style={styles.modalButtonsRow}>
              <TouchableOpacity
                style={[styles.button, styles.secondaryButton, styles.modalButton]}
                disabled={disabled}
                onPress={onCancel}
              >
                <Text style={styles.buttonTextSecondary}>Cancel</Text>
              </TouchableOpacity>
            </View>
          ) : null}
        </View>
      ) : (
        <View style={styles.modalButtonsRow}>
          {showCancelButton ? (
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton, styles.modalButton]}
              disabled={disabled}
              onPress={onCancel}
            >
              <Text style={styles.buttonTextSecondary}>Cancel</Text>
            </TouchableOpacity>
          ) : null}
          <TouchableOpacity
            style={[styles.button, styles.primaryButton, styles.modalButton]}
            disabled={disabled}
            onPress={handlePrimary}
          >
            <Text style={styles.buttonText}>OK</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

export function ApplicationActionDialog({
  visible,
  dialog,
  titleFallback,
  prefillContext,
  onSubmit,
  onCancel,
}: ApplicationActionDialogProps): React.JSX.Element | null {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, 'default'), [theme]);

  if (!visible) {
    return null;
  }

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onCancel}>
      <KeyboardAvoidingView
        style={styles.modalOverlay}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        <ApplicationActionDialogLayout
          dialog={dialog}
          titleFallback={titleFallback}
          prefillContext={prefillContext}
          onSubmit={onSubmit}
          onCancel={onCancel}
          style={styles.modalCard}
        />
      </KeyboardAvoidingView>
    </Modal>
  );
}

const createStyles = (theme: Theme, density: ApplicationActionDialogDensity) => {
  const compact = density === 'compact';
  const cardPad = compact ? 10 : 16;
  const titleSize = compact ? 15 : 18;
  const titleMb = compact ? 2 : 4;
  const subtitleSize = compact ? 11 : 12;
  const subtitleMb = compact ? 8 : 12;
  const btnPadH = compact ? 8 : 10;
  const btnPadV = compact ? 5 : 6;
  const btnTextSize = compact ? 12 : 14;
  const customBtnMb = compact ? 5 : 8;
  const customColMt = compact ? 4 : 8;

  return StyleSheet.create({
    modalOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    modalCard: {
      width: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: cardPad,
    },
    dialogCard: {
      width: '100%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: cardPad,
    },
    submitCapture: {
      position: 'absolute',
      left: -1000,
      top: -1000,
      width: 1,
      height: 1,
      opacity: 0,
    },
    modalTitle: {
      fontSize: theme.typography.fontSize.title,
      fontWeight: '600',
      marginBottom: titleMb,
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: theme.typography.fontSize.small,
      color: theme.textSecondary,
      marginBottom: subtitleMb,
    },
    inputGroup: {
      marginBottom: 12,
    },
    inputLabel: {
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    inputDescription: {
      fontSize: theme.typography.fontSize.tiny,
      color: theme.textSecondary,
      marginBottom: 6,
    },
    modalInput: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      backgroundColor: theme.backgroundAlt,
    },
    modalInputMultiline: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      backgroundColor: theme.backgroundAlt,
      minHeight: 90,
    },
    errorText: {
      fontSize: theme.typography.fontSize.small,
      color: theme.danger,
      marginBottom: 8,
    },
    customButtonsColumn: {
      marginTop: customColMt,
      width: '100%',
    },
    customActionButton: {
      width: '100%',
      alignItems: 'center',
      marginBottom: customBtnMb,
      marginLeft: 0,
    },
    modalButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      marginTop: 8,
    },
    modalButton: {
      minWidth: 90,
      alignItems: 'center',
      marginLeft: 8,
    },
    button: {
      paddingHorizontal: btnPadH,
      paddingVertical: btnPadV,
      borderRadius: 8,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    buttonTextSecondary: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '700',
    },
  });
};
