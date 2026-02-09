import React, { useMemo, useState } from 'react';
import {
  Platform,
  TextInput,
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
  value: string;
  placeholder?: string;
  editable?: boolean;
  textColor?: string;
  placeholderTextColor?: string;
  fontSize?: number;

  autoGrow?: boolean;
  maxHeight?: number;

  onChangeText?: (text: string) => void;
  onSubmit?: (text: string) => void;
}

type NativeMacTextViewProps = Omit<MacTextViewProps, 'onChangeText' | 'onSubmit' | 'autoGrow'> & {
  onChange?: (event: OnChangeEvent) => void;
  onSubmit?: (event: OnSubmitEvent) => void;
  onMacContentSizeChange?: (event: OnMacContentSizeChangeEvent) => void;
  autoGrow?: boolean;
};

const NativeMacTextView =
  Platform.OS === 'macos'
    ? requireNativeComponent<NativeMacTextViewProps>('MacTextView')
    : null;

export function MacTextView({ autoGrow, maxHeight, style, ...props }: MacTextViewProps): React.JSX.Element {
  const [contentHeight, setContentHeight] = useState<number | null>(null);

  const autoHeightStyle: StyleProp<ViewStyle> = useMemo(() => {
    if (!autoGrow || contentHeight == null) {
      return null;
    }
    const nextHeight = maxHeight ? Math.min(contentHeight, maxHeight) : contentHeight;
    return { height: nextHeight };
  }, [autoGrow, contentHeight, maxHeight]);

  if (!NativeMacTextView) {
    const fallbackProps: TextInputProps = {
      value: props.value,
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
      {...props}
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
}
