import React from 'react';
import {
  Platform,
  TextInput,
  requireNativeComponent,
  type NativeSyntheticEvent,
  type ViewProps,
} from 'react-native';

export interface MacComboBoxOption {
  value: string;
  label: string;
}

type ValueEvent = NativeSyntheticEvent<{ value: string }>;

export interface MacComboBoxProps extends ViewProps {
  options: MacComboBoxOption[];
  inputValue: string;
  placeholder?: string;
  enabled?: boolean;
  onInputValueChange?: (value: string) => void;
  onValueChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
}

type NativeMacComboBoxProps = Omit<
  MacComboBoxProps,
  'onInputValueChange' | 'onValueChange' | 'onSubmit'
> & {
  onInputChange?: (event: ValueEvent) => void;
  onChange?: (event: ValueEvent) => void;
  onSubmitValue?: (event: ValueEvent) => void;
};

const NativeMacComboBox =
  Platform.OS === 'macos'
    ? requireNativeComponent<NativeMacComboBoxProps>('MacComboBox')
    : null;

export function MacComboBox({
  options,
  inputValue,
  placeholder,
  enabled,
  onInputValueChange,
  onValueChange,
  onSubmit,
  ...props
}: MacComboBoxProps): React.JSX.Element {
  if (!NativeMacComboBox) {
    return (
      <TextInput
        testID={props.testID}
        accessibilityLabel={props.accessibilityLabel}
        style={props.style}
        value={inputValue}
        placeholder={placeholder}
        editable={enabled !== false}
        onChangeText={onInputValueChange}
        onSubmitEditing={() => onSubmit?.(inputValue)}
      />
    );
  }

  return (
    <NativeMacComboBox
      {...props}
      options={options}
      inputValue={inputValue}
      placeholder={placeholder}
      enabled={enabled}
      onInputChange={event => {
        const value = String(event.nativeEvent?.value ?? '');
        onInputValueChange?.(value);
      }}
      onChange={event =>
        onValueChange?.(String(event.nativeEvent?.value ?? ''))
      }
      onSubmitValue={event =>
        onSubmit?.(String(event.nativeEvent?.value ?? ''))
      }
    />
  );
}
