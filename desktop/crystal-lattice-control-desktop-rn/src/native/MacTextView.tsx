import React, {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  NativeModules,
  Platform,
  TextInput,
  findNodeHandle,
  requireNativeComponent,
  type NativeSyntheticEvent,
  type StyleProp,
  type TextInputProps,
  type ViewProps,
  type ViewStyle,
} from 'react-native';

type OnChangeEvent = NativeSyntheticEvent<{ text: string }>;
type OnSubmitEvent = NativeSyntheticEvent<{ text: string }>;
type OnMacContentSizeChangeEvent = NativeSyntheticEvent<{
  contentSize: { width: number; height: number };
}>;

export interface MacTextViewProps extends Omit<ViewProps, 'onLayout'> {
  initialText?: string;
  placeholder?: string;
  editable?: boolean;
  textColor?: string;
  placeholderTextColor?: string;
  fontSize?: number;

  autoGrow?: boolean;
  minHeight?: number;
  maxHeight?: number;

  onChangeText?: (text: string) => void;
  onSubmit?: (text: string) => void;
}

type NativeMacTextViewProps = Omit<MacTextViewProps, 'onChangeText' | 'onSubmit' | 'autoGrow'> & {
  initialText?: string;
  onChange?: (event: OnChangeEvent) => void;
  onSubmit?: (event: OnSubmitEvent) => void;
  onMacContentSizeChange?: (event: OnMacContentSizeChangeEvent) => void;
  autoGrow?: boolean;
};

const NativeMacTextView =
  Platform.OS === 'macos'
    ? requireNativeComponent<NativeMacTextViewProps>('MacTextView')
    : null;

export interface MacTextViewHandle {
  setText: (text: string) => void;
  focus: () => void;
}

export const MacTextView = forwardRef<MacTextViewHandle, MacTextViewProps>(function MacTextView(
  { autoGrow, minHeight, maxHeight, style, initialText, ...props }: MacTextViewProps,
  ref,
): React.JSX.Element {
  const [contentHeight, setContentHeight] = useState<number | null>(null);
  const nativeRef = useRef<any>(null);

  const autoHeightStyle: StyleProp<ViewStyle> = useMemo(() => {
    if (!autoGrow) {
      return null;
    }

    const baseline = minHeight ?? 34;
    const measured = contentHeight ?? baseline;
    const capped = maxHeight ? Math.min(measured, maxHeight) : measured;
    const floored = minHeight ? Math.max(capped, minHeight) : capped;
    return { height: floored };
  }, [autoGrow, contentHeight, maxHeight, minHeight]);

  const setText = useCallback((text: string) => {
    const tag = findNodeHandle(nativeRef.current);
    if (!tag || Platform.OS !== 'macos') {
      return;
    }
    NativeModules.MacTextView?.setText?.(tag, String(text ?? ''));
  }, []);

  const focus = useCallback(() => {
    const tag = findNodeHandle(nativeRef.current);
    if (!tag || Platform.OS !== 'macos') {
      return;
    }
    NativeModules.MacTextView?.focus?.(tag);
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      setText,
      focus,
    }),
    [focus, setText],
  );

  if (!NativeMacTextView) {
    const fallbackProps: TextInputProps = {
      defaultValue: initialText,
      editable: props.editable,
      placeholder: props.placeholder,
      placeholderTextColor: props.placeholderTextColor,
      onChangeText: props.onChangeText,
      multiline: true,
      autoCorrect: false,
      spellCheck: false,
      style: [style as any, autoHeightStyle as any],
    };

    return <TextInput {...fallbackProps} />;
  }

  return (
    <NativeMacTextView
      ref={nativeRef}
      {...props}
      initialText={initialText}
      style={[style, autoHeightStyle]}
      autoGrow={autoGrow}
      maxHeight={maxHeight}
      onChange={(event) => {
        props.onChangeText?.(String(event.nativeEvent?.text ?? ''));
      }}
      onSubmit={(event) => {
        props.onSubmit?.(String(event.nativeEvent?.text ?? ''));
      }}
      onMacContentSizeChange={(event) => {
        const height = Number(event.nativeEvent?.contentSize?.height ?? NaN);
        if (Number.isFinite(height)) {
          setContentHeight(height);
        }
      }}
    />
  );
});
