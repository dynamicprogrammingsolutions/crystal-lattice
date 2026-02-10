import React, {
  forwardRef,
  useCallback,
  useEffect,
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
  StyleSheet,
  View,
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
  textLength?: number;
}>;

export interface MacTextViewProps extends Omit<ViewProps, 'onLayout'> {
  initialText?: string;
  placeholder?: string;
  editable?: boolean;
  textColor?: string;
  placeholderTextColor?: string;
  fontSize?: number;
  addToHeight?: number;

  autoGrow?: boolean;
  minHeight?: number;
  maxHeight?: number;

  onChangeText?: (text: string) => void;
  onSubmit?: (text: string) => void;
  onHeightChange?: (height: number) => void;
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
  { autoGrow, minHeight, maxHeight, style, initialText, onHeightChange, addToHeight, ...props }: MacTextViewProps,
  ref,
): React.JSX.Element {
  const [contentHeight, setContentHeight] = useState<number | null>(null);
  const nativeRef = useRef<any>(null);
  const lastTextRef = useRef('');

  const resolvedHeight = useMemo(() => {
    if (!autoGrow) {
      return null;
    }

    const baseline = minHeight ?? 34;
    const measured = contentHeight ?? baseline;
    const capped = maxHeight ? Math.min(measured, maxHeight) : measured;
    const floored = minHeight ? Math.max(capped, minHeight) : capped;
    const resolved = floored + (addToHeight || 0);
    console.log('MacTextView resolvedHeight:', { baseline, measured, capped, floored, resolved, addToHeight, contentHeight });
    return resolved;
  }, [autoGrow, contentHeight, maxHeight, minHeight]);

  const shouldSelfSize = autoGrow && !onHeightChange;
  const autoHeightStyle: StyleProp<ViewStyle> = useMemo(() => {
    if (!shouldSelfSize || resolvedHeight == null) {
      return null;
    }
    return { height: resolvedHeight };
  }, [resolvedHeight, shouldSelfSize]);

  useEffect(() => {
    if (resolvedHeight == null) {
      return;
    }
    onHeightChange?.(resolvedHeight);
  }, [onHeightChange, resolvedHeight]);

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
    <View collapsable={false} style={[style, autoHeightStyle]}>
      <NativeMacTextView
        ref={nativeRef}
        {...props}
        initialText={initialText}
        style={styles.nativeFill}
        autoGrow={autoGrow}
        maxHeight={maxHeight}
        onChange={(event) => {
          const next = String(event.nativeEvent?.text ?? '');
          lastTextRef.current = next;
          props.onChangeText?.(next);
        }}
        onSubmit={(event) => {
          props.onSubmit?.(String(event.nativeEvent?.text ?? ''));
        }}
        onMacContentSizeChange={(event) => {
          const height = Number(event.nativeEvent?.contentSize?.height ?? NaN);
          console.log('MacTextView onMacContentSizeChange:', { height, event });
          if (Number.isFinite(height)) {
          const eventTextLength = Number(event.nativeEvent?.textLength ?? NaN);
          const hasText = Number.isFinite(eventTextLength)
            ? eventTextLength > 0
            : lastTextRef.current.length > 0;
            setContentHeight((prev) => {
              if (!hasText) {
                return height;
              }

              // Ignore transient "inset-only" measurements (~16px) while
              // there is text, as they cause auto-grow oscillations.
              const threshold = minHeight ?? 34;
              if (prev != null && height < prev && height < threshold) {
                return prev;
              }
              return height;
            });
          }
        }}
      />
    </View>
  );
});

const styles = StyleSheet.create({
  nativeFill: {
    flex: 1,
    alignSelf: 'stretch',
  },
});
