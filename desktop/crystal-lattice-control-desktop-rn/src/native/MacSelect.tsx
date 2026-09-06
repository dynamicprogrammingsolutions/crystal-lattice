import React from 'react';
import {
  Platform,
  Pressable,
  Text,
  requireNativeComponent,
  type NativeSyntheticEvent,
  type ViewProps,
} from 'react-native';

export interface MacSelectOption {
  value: string;
  label: string;
}

type OnChangeEvent = NativeSyntheticEvent<{ value: string }>;

export interface MacSelectProps extends ViewProps {
  options: MacSelectOption[];
  selectedValue: string;
  /**
   * Optional placeholder shown when `selectedValue` is empty.
   *
   * On macOS, this is rendered as a disabled first menu item.
   */
  placeholder?: string;
  enabled?: boolean;
  onValueChange?: (value: string) => void;
}

type NativeMacSelectProps = Omit<MacSelectProps, 'onValueChange'> & {
  onChange?: (event: OnChangeEvent) => void;
};

const NativeMacSelect =
  Platform.OS === 'macos' ? requireNativeComponent<NativeMacSelectProps>('MacSelect') : null;

export function MacSelect({ onValueChange, ...props }: MacSelectProps): React.JSX.Element {
  if (!NativeMacSelect) {
    const selected = props.options.find((opt) => opt.value === props.selectedValue);
    const label =
      selected?.label ??
      (props.selectedValue ? props.selectedValue : props.placeholder ? props.placeholder : '');
    return (
      <Pressable
        testID={props.testID}
        accessibilityLabel={props.accessibilityLabel}
        style={props.style}
        disabled={props.enabled === false}
        onPress={() => {
          if (props.options.length === 0) return;
          const index = props.options.findIndex(
            (option) => option.value === props.selectedValue,
          );
          const next = props.options[(index + 1) % props.options.length];
          onValueChange?.(next.value);
        }}
      >
        <Text>{label}</Text>
      </Pressable>
    );
  }

  return (
    <NativeMacSelect
      {...props}
      onChange={(event) => {
        const value = String(event.nativeEvent?.value ?? '');
        onValueChange?.(value);
      }}
    />
  );
}
