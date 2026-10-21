import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import {
  buildActionDialogInitialValues,
  normalizeSelectOptions,
  type NormalizedSelectOption,
} from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from './theme';
import { useActionFormScroll } from './useActionFormScroll';

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
  presentationMode?: 'native' | 'overlay';
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
  onFocus?: () => void;
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
  onSubmit?: () => void;
  onFieldFocus?: () => void;
}

export interface ApplicationActionDialogLayoutProps
  extends Omit<ApplicationActionDialogProps, 'visible'> {
  style?: StyleProp<ViewStyle>;
  maxHeight?: number;
}

function parseBoolean(raw: string): boolean | null {
  const value = raw.trim().toLowerCase();
  if (!value) return null;
  if (value === 'true' || value === '1' || value === 'yes' || value === 'y') return true;
  if (value === 'false' || value === '0' || value === 'no' || value === 'n') return false;
  return null;
}

export const ApplicationActionForm = forwardRef<
  ApplicationActionFormHandle,
  ApplicationActionFormProps
>(function ApplicationActionForm(
  { form, prefillContext, fieldRenderers, renderField, style, onSubmit, onFieldFocus },
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

    const initial = buildActionDialogInitialValues(inputs, prefillContext);

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
    const isSecret = params.fieldType === 'secret' || params.fieldType === 'password';

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
          testID={`action-form-input-${params.name}`}
          style={isMultiline ? styles.modalInputMultiline : styles.modalInput}
          value={params.value}
          onChangeText={params.onChange}
          onFocus={params.onFocus}
          placeholder={params.placeholder}
          placeholderTextColor={theme.textSecondary}
          multiline={isMultiline}
          secureTextEntry={isSecret}
          autoCapitalize="none"
          autoCorrect={false}
          disableFullscreenUI
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
              onSubmit: onSubmit ?? submit,
              onFocus: onFieldFocus,
            };
            const params: ApplicationActionDialogFieldRenderParams = {
              ...baseParams,
              renderFallback: () =>
                renderDefaultField({
                  ...baseParams,
                  renderFallback: () => null,
                }),
            };

            const renderer = renderField || fieldRenderers?.[fieldType] || fieldRenderers?.fallback;

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
});

export function ApplicationActionDialogLayout({
  dialog,
  titleFallback,
  prefillContext,
  fieldRenderers,
  renderField,
  onSubmit,
  onCancel,
  style,
  maxHeight,
}: ApplicationActionDialogLayoutProps): React.JSX.Element | null {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const formRef = useRef<ApplicationActionFormHandle | null>(null);
  const submitCaptureRef = useRef<TextInput | null>(null);
  const formScroll = useActionFormScroll();
  const kind = typeof dialog?.kind === 'string' ? dialog.kind : 'none';
  const hasInputs = kind === 'form' && Array.isArray(dialog?.inputs) && dialog.inputs.length > 0;

  const handlePrimary = () => {
    const values = kind === 'form' ? formRef.current?.submit() : {};
    if (values !== null && values !== undefined) {
      onSubmit(values);
    }
  };

  useEffect(() => {
    if (Platform.OS !== 'macos' || kind === 'none' || hasInputs) return;
    const timer = setTimeout(() => submitCaptureRef.current?.focus(), 0);
    return () => clearTimeout(timer);
  }, [dialog, kind, hasInputs]);

  if (!dialog || kind === 'none') return null;
  const title = (typeof dialog.title === 'string' && dialog.title) || titleFallback || 'Action';
  const message = typeof dialog.message === 'string' && dialog.message ? dialog.message : null;
  const body = (
    <>
      {message ? <Text style={styles.modalSubtitle}>{message}</Text> : null}
      {kind === 'form' ? (
        <ApplicationActionForm
          ref={formRef}
          form={dialog}
          prefillContext={prefillContext}
          fieldRenderers={fieldRenderers}
          renderField={renderField}
          onSubmit={handlePrimary}
          onFieldFocus={formScroll.onFieldFocus}
        />
      ) : null}
    </>
  );

  return (
    <View
      testID="application-action-dialog-card"
      style={[styles.dialogCard, style, maxHeight !== undefined && { maxHeight }]}
    >
      {Platform.OS === 'macos' ? (
        <TextInput
          ref={submitCaptureRef}
          style={styles.submitCapture}
          value=""
          onChangeText={() => {}}
          blurOnSubmit={false}
          onSubmitEditing={handlePrimary}
        />
      ) : null}
      <Text testID="application-action-dialog-title" style={styles.modalTitle}>
        {title}
      </Text>
      {maxHeight !== undefined ? (
        <ScrollView
          ref={formScroll.scrollRef}
          testID="application-action-dialog-body"
          style={styles.formScroll}
          keyboardShouldPersistTaps="handled"
          nestedScrollEnabled
          removeClippedSubviews={false}
          contentInsetAdjustmentBehavior="never"
          onLayout={formScroll.onLayout}
          onScroll={formScroll.onScroll}
          scrollEventThrottle={16}
        >
          {body}
        </ScrollView>
      ) : (
        body
      )}
      <View testID="application-action-dialog-controls" style={styles.modalButtonsRow}>
        <TouchableOpacity
          accessibilityRole="button"
          style={[styles.button, styles.secondaryButton, styles.modalButton]}
          testID="application-action-dialog-cancel"
          onPress={onCancel}
        >
          <Text style={styles.buttonTextSecondary}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity
          accessibilityRole="button"
          style={[styles.button, styles.primaryButton, styles.modalButton]}
          testID="application-action-dialog-primary"
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
  presentationMode = 'native',
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
  const [viewportHeight, setViewportHeight] = useState<number | undefined>();
  useEffect(() => {
    if (visible && Platform.OS !== 'macos') Keyboard.dismiss();
  }, [visible, dialog]);

  const handleCancel = () => {
    if (Platform.OS !== 'macos') Keyboard.dismiss();
    onCancel();
  };
  const handleSubmit = (values: Record<string, any>) => {
    if (Platform.OS !== 'macos') Keyboard.dismiss();
    onSubmit(values);
  };

  if (!visible) {
    return null;
  }

  const content = (
    <KeyboardAvoidingView
      accessibilityViewIsModal
      style={[styles.modalOverlay, presentationMode === 'overlay' && styles.absoluteOverlay]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={0}
    >
      <SafeAreaView style={styles.safeViewport}>
        <View
          testID="application-action-dialog-viewport"
          style={styles.dialogViewport}
          onLayout={(event) => setViewportHeight(event.nativeEvent.layout.height)}
        >
          <ApplicationActionDialogLayout
            dialog={dialog}
            titleFallback={titleFallback}
            prefillContext={prefillContext}
            fieldRenderers={fieldRenderers}
            renderField={renderField}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            style={styles.modalCard}
            maxHeight={viewportHeight === undefined ? undefined : Math.max(0, viewportHeight - 24)}
          />
        </View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
  if (presentationMode === 'overlay') {
    return content;
  }
  return (
    <Modal
      visible
      transparent
      animationType="fade"
      supportedOrientations={['portrait', 'landscape']}
      onRequestClose={handleCancel}
    >
      {content}
    </Modal>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modalOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
    },
    safeViewport: {
      flex: 1,
    },
    dialogViewport: {
      flex: 1,
      padding: 12,
      alignItems: 'center',
      justifyContent: 'center',
    },
    absoluteOverlay: {
      ...StyleSheet.absoluteFillObject,
      zIndex: 1,
      elevation: 1,
    },
    modalCard: {
      width: '100%',
      maxWidth: 560,
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
    formScroll: {
      flexGrow: 0,
      flexShrink: 1,
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
      flexShrink: 0,
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
      flexShrink: 0,
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
