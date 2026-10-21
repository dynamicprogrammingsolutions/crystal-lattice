import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Platform,
  StyleSheet,
  TextInput,
  View,
  type NativeSyntheticEvent,
  type StyleProp,
  type TextInputProps,
  type ViewProps,
  type ViewStyle,
} from 'react-native';

import NativeMacTextView, {
  Commands,
  type MacTextViewChangeEvent,
  type MacTextViewContentSizeChangeEvent,
  type MacTextViewSubmitEvent,
} from './specs/CLCMacTextViewNativeComponent';

type OnChangeEvent = NativeSyntheticEvent<MacTextViewChangeEvent>;
type OnSubmitEvent = NativeSyntheticEvent<MacTextViewSubmitEvent>;
type OnMacContentSizeChangeEvent = NativeSyntheticEvent<MacTextViewContentSizeChangeEvent>;

export interface MacTextViewProps extends Omit<ViewProps, 'onLayout'> {
  initialText?: string;
  placeholder?: string;
  editable?: boolean;
  submitOnEnter?: boolean;
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

export interface MacTextViewHandle {
  setText: (text: string) => void;
  focus: () => void;
}

export const MacTextView = forwardRef<MacTextViewHandle, MacTextViewProps>(function MacTextView(
  { autoGrow, minHeight, maxHeight, style, initialText, onHeightChange, addToHeight, ...props }: MacTextViewProps,
  ref,
): React.JSX.Element {
  const [contentHeight, setContentHeight] = useState<number | null>(null);
  const nativeRef = useRef<React.ElementRef<typeof NativeMacTextView> | null>(null);
  const lastTextRef = useRef('');

  const resolvedHeight = useMemo(() => {
    if (!autoGrow) {
      return null;
    }

    const baseline = minHeight ?? 34;
    const measured = contentHeight ?? baseline;
    const capped = maxHeight ? Math.min(measured, maxHeight) : measured;
    const floored = minHeight ? Math.max(capped, minHeight) : capped;
    return floored + (addToHeight || 0);
  }, [addToHeight, autoGrow, contentHeight, maxHeight, minHeight]);

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

  useImperativeHandle(
    ref,
    () => ({
      setText: (text: string) => {
        if (Platform.OS !== 'macos' || !nativeRef.current) {
          return;
        }
        const next = String(text ?? '');
        lastTextRef.current = next;
        if (next.length === 0) {
          setContentHeight(null);
        }
        Commands.setText(nativeRef.current, next);
      },
      focus: () => {
        if (Platform.OS !== 'macos' || !nativeRef.current) {
          return;
        }
        Commands.focus(nativeRef.current);
      },
    }),
    [],
  );

  if (Platform.OS !== 'macos') {
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
      blurOnSubmit: props.submitOnEnter !== false,
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
        onChange={(event: OnChangeEvent) => {
          const next = String(event.nativeEvent?.text ?? '');
          lastTextRef.current = next;
          if (next.length === 0) {
            setContentHeight(null);
          }
          props.onChangeText?.(next);
        }}
        onSubmit={(event: OnSubmitEvent) => {
          props.onSubmit?.(String(event.nativeEvent?.text ?? ''));
        }}
        onMacContentSizeChange={(event: OnMacContentSizeChangeEvent) => {
          const height = Number(event.nativeEvent?.height ?? NaN);
          if (!Number.isFinite(height)) {
            return;
          }

          const eventTextLength = Number(event.nativeEvent?.textLength ?? NaN);
          const hasText = Number.isFinite(eventTextLength)
            ? eventTextLength > 0
            : lastTextRef.current.length > 0;

          if (!hasText) {
            setContentHeight(null);
            return;
          }

          setContentHeight((prev) => {
            const threshold = minHeight ?? 34;
            if (prev != null && height < prev && height < threshold) {
              return prev;
            }
            return height;
          });
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