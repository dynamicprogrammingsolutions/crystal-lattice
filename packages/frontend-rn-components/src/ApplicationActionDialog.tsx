import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
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

import {
  extractByPath,
  normalizeSelectOptions,
  type NormalizedSelectOption,
} from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from './theme';

export interface DialogInputField {
  name: string;
  type?: string;
  label?: string;
  placeholder?: string;
  default?: any;
  required?: boolean;
  description?: string;
  options?: any;
  prefill_from?: string;
  submit_empty?: boolean;
}

const EMPTY_INPUTS: DialogInputField[] = [];

export interface ApplicationActionDialogPrefillContext {
  session?: any;
  message?: any;
}

export interface ApplicationActionDialogProps {
  visible: boolean;
  dialog: any;
  titleFallback?: string;
  prefillContext?: ApplicationActionDialogPrefillContext;
  fieldRenderers?: ApplicationActionDialogFieldRenderers;
  renderField?: ApplicationActionDialogFieldRenderer;
  onSubmit: (values: Record<string, any>) => void;
  onCancel: () => void;
}

export interface ApplicationActionDialogFieldRenderParams {
  field: DialogInputField;
  name: string;
  label: string;
  description: string;
  placeholder: string;
  fieldType: string;
  value: string;
  options: NormalizedSelectOption[];
  isFirstField: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  renderFallback: () => React.ReactNode;
}

export type ApplicationActionDialogFieldRenderer = (
  params: ApplicationActionDialogFieldRenderParams,
) => React.ReactNode;

export type ApplicationActionDialogFieldRenderers = {
  fallback?: ApplicationActionDialogFieldRenderer;
} & Partial<Record<string, ApplicationActionDialogFieldRenderer>>;

export interface ApplicationActionFormHandle {
  submit: () => Record<string, any> | null;
}

export interface ApplicationActionFormProps {
  form: any;
  prefillContext?: ApplicationActionDialogPrefillContext;
  fieldRenderers?: ApplicationActionDialogFieldRenderers;
  renderField?: ApplicationActionDialogFieldRenderer;
  style?: StyleProp<ViewStyle>;
}

export interface ApplicationActionDialogLayoutProps
  extends Omit<ApplicationActionDialogProps, 'visible'> {
  style?: StyleProp<ViewStyle>;
}

function parseBoolean(raw: string): boolean | null {
  const value = raw.trim().toLowerCase();
  if (!value) return null;
  if (value === 'true' || value === '1' || value === 'yes' || value === 'y') return true;
  if (value === 'false' || value === '0' || value === 'no' || value === 'n') return false;
  return null;
}

export const ApplicationActionForm = forwardRef<ApplicationActionFormHandle, ApplicationActionFormProps>(
  function ApplicationActionForm(
    { form, prefillContext, fieldRenderers, renderField, style },
    ref,
  ): React.JSX.Element | null {
    const theme = useTheme();
    const styles = useMemo(() => createStyles(theme), [theme]);

    const kind: string = form && typeof form.kind === 'string' ? form.kind : 'none';
    const inputs: DialogInputField[] = useMemo(() => {
      if (kind !== 'form' || !form || !Array.isArray(form.inputs)) {
        return EMPTY_INPUTS;
      }
      return form.inputs as DialogInputField[];
    }, [form, kind]);

    const [valuesByName, setValuesByName] = useState<Record<string, string>>({});
    const [error, setError] = useState<string | null>(null);
    const initialValuesByNameRef = useRef<Record<string, string>>({});
    const firstInputRef = useRef<TextInput | null>(null);
    const lastFormRef = useRef<any>(null);

    useEffect(() => {
      if (!form || kind === 'none') {
        lastFormRef.current = form;
        setValuesByName((prev) => (Object.keys(prev).length === 0 ? prev : {}));
        setError((prev) => (prev === null ? prev : null));
        return;
      }

      const shouldReset = lastFormRef.current !== form;
      lastFormRef.current = form;
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
    }, [form, inputs, kind, prefillContext]);

    useEffect(() => {
      if (Platform.OS !== 'macos') {
        return;
      }
      if (!form || kind !== 'form' || inputs.length === 0) {
        return;
      }

      const timer = setTimeout(() => {
        firstInputRef.current?.focus();
      }, 0);

      return () => {
        clearTimeout(timer);
      };
    }, [form, inputs.length, kind]);

    const handleChange = (name: string, text: string) => {
      setValuesByName((prev) => ({ ...prev, [name]: text }));
    };

    const submit = (): Record<string, any> | null => {
      if (kind !== 'form') {
        setError(null);
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
        } else if (fieldType === 'boolean' || fieldType === 'checkbox') {
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

      setError(null);
      return result;
    };

    useImperativeHandle(ref, () => ({ submit }), [submit]);

    const renderDefaultField = (params: ApplicationActionDialogFieldRenderParams) => {
      const isMultiline = params.fieldType === 'multiline';

      return (
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>{params.label}</Text>
          {params.description ? (
            <Text style={styles.inputDescription}>{params.description}</Text>
          ) : null}
          <TextInput
            ref={(node) => {
              if (params.isFirstField) {
                firstInputRef.current = node;
              }
            }}
            style={isMultiline ? styles.modalInputMultiline : styles.modalInput}
            value={params.value}
            onChangeText={params.onChange}
            placeholder={params.placeholder}
            placeholderTextColor={theme.textSecondary}
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
              submit();
            }}
          />
        </View>
      );
    };

    if (!form || kind === 'none') {
      return null;
    }

    return (
      <View style={style}>
        {kind === 'form'
          ? inputs.map((field) => {
              const name = field.name;
              if (!name) return null;
              const label = field.label || name;
              const placeholder = field.placeholder || '';
              const description = field.description || '';
              const value = valuesByName[name] ?? '';
              const fieldType = typeof field.type === 'string' ? field.type : 'string';
              const isFirstField = inputs[0] === field;
              const baseParams: Omit<ApplicationActionDialogFieldRenderParams, 'renderFallback'> = {
                field,
                name,
                label,
                description,
                placeholder,
                fieldType,
                value,
                options: normalizeSelectOptions(field.options),
                isFirstField,
                onChange: (nextValue: string) => handleChange(name, nextValue),
                onSubmit: submit,
              };
              const params: ApplicationActionDialogFieldRenderParams = {
                ...baseParams,
                renderFallback: () =>
                  renderDefaultField({
                    ...baseParams,
                    renderFallback: () => null,
                  }),
              };

              const renderer =
                renderField ||
                fieldRenderers?.[fieldType] ||
                fieldRenderers?.fallback;

              return (
                <React.Fragment key={name}>
                  {renderer ? renderer(params) : renderDefaultField(params)}
                </React.Fragment>
              );
            })
          : null}

        {error ? <Text style={styles.errorText}>{error}</Text> : null}
      </View>
    );
  },
);

export function ApplicationActionDialogLayout({
  dialog,
  titleFallback,
  prefillContext,
  fieldRenderers,
  renderField,
  onSubmit,
  onCancel,
  style,
}: ApplicationActionDialogLayoutProps): React.JSX.Element | null {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const kind: string = dialog && typeof dialog.kind === 'string' ? dialog.kind : 'none';

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
  }, [dialog, kind]);

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
          return;
        }
        parsed = numberValue;
      } else if (fieldType === 'number') {
        const numberValue = parseFloat(trimmed);
        if (Number.isNaN(numberValue)) {
          const label = field.label || name;
          setError(`Field "${label}" must be a number.`);
          return;
        }
        parsed = numberValue;
      } else if (fieldType === 'boolean' || fieldType === 'checkbox') {
        const boolValue = parseBoolean(trimmed);
        if (boolValue === null) {
          const label = field.label || name;
          setError(`Field "${label}" must be true/false.`);
          return;
        }
        parsed = boolValue;
      }

      result[name] = parsed;
    }

    setError(null);
    onSubmit(result);
  };

  const renderDefaultField = (params: ApplicationActionDialogFieldRenderParams) => {
    const isMultiline = params.fieldType === 'multiline';

    return (
      <View style={styles.inputGroup}>
        <Text style={styles.inputLabel}>{params.label}</Text>
        {params.description ? (
          <Text style={styles.inputDescription}>{params.description}</Text>
        ) : null}
        <TextInput
          ref={(node) => {
            if (params.isFirstField) {
              firstInputRef.current = node;
            }
          }}
          style={isMultiline ? styles.modalInputMultiline : styles.modalInput}
          value={params.value}
          onChangeText={params.onChange}
          placeholder={params.placeholder}
          placeholderTextColor={theme.textSecondary}
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
            params.onSubmit();
          }}
        />
      </View>
    );
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
          onSubmitEditing={() => handlePrimary()}
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
            const isFirstField = inputs[0] === field;
            const baseParams: Omit<ApplicationActionDialogFieldRenderParams, 'renderFallback'> = {
              field,
              name,
              label,
              description,
              placeholder,
              fieldType,
              value,
              options: normalizeSelectOptions(field.options),
              isFirstField,
              onChange: (nextValue: string) => handleChange(name, nextValue),
              onSubmit: handlePrimary,
            };
            const params: ApplicationActionDialogFieldRenderParams = {
              ...baseParams,
              renderFallback: () =>
                renderDefaultField({
                  ...baseParams,
                  renderFallback: () => null,
                }),
            };

            const renderer =
              renderField ||
              fieldRenderers?.[fieldType] ||
              fieldRenderers?.fallback;

            return (
              <React.Fragment key={name}>
                {renderer ? renderer(params) : renderDefaultField(params)}
              </React.Fragment>
            );
          })
        : null}

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
  );
}

export function ApplicationActionDialog({
  visible,
  dialog,
  titleFallback,
  prefillContext,
  fieldRenderers,
  renderField,
  onSubmit,
  onCancel,
}: ApplicationActionDialogProps): React.JSX.Element | null {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

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
          fieldRenderers={fieldRenderers}
          renderField={renderField}
          onSubmit={onSubmit}
          onCancel={onCancel}
          style={styles.modalCard}
        />
      </KeyboardAvoidingView>
    </Modal>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
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
      padding: 16,
    },
    dialogCard: {
      width: '100%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
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
      marginBottom: 4,
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: theme.typography.fontSize.small,
      color: theme.textSecondary,
      marginBottom: 12,
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
      paddingHorizontal: 10,
      paddingVertical: 6,
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
