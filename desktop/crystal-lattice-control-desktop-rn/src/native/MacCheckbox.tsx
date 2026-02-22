import React from 'react';
import {
  Platform,
  Switch,
  Text,
  View,
  requireNativeComponent,
  type NativeSyntheticEvent,
  type ViewProps,
} from 'react-native';

type OnChangeEvent = NativeSyntheticEvent<{ value: boolean }>;

export interface MacCheckboxProps extends ViewProps {
  label: string;
  value: boolean;
  enabled?: boolean;
  onValueChange?: (next: boolean) => void;
}

type NativeMacCheckboxProps = Omit<MacCheckboxProps, 'onValueChange'> & {
  onChange?: (event: OnChangeEvent) => void;
};

const NativeMacCheckbox =
  Platform.OS === 'macos'
    ? requireNativeComponent<NativeMacCheckboxProps>('MacCheckbox')
    : null;

export function MacCheckbox({ onValueChange, ...props }: MacCheckboxProps): React.JSX.Element {
  if (!NativeMacCheckbox) {
    return (
      <View style={[{ flexDirection: 'row', alignItems: 'center', gap: 8 }, props.style]}>
        <Switch value={props.value} onValueChange={(next) => onValueChange?.(next)} />
        <Text>{props.label}</Text>
      </View>
    );
  }

  return (
    <NativeMacCheckbox
      {...props}
      onChange={(event) => {
        onValueChange?.(Boolean(event.nativeEvent?.value));
      }}
    />
  );
}
