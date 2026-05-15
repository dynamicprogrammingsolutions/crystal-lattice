import type * as React from 'react';
import type { ColorValue, HostComponent, ViewProps } from 'react-native';
import codegenNativeCommands from 'react-native/Libraries/Utilities/codegenNativeCommands';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';
import type {
  BubblingEventHandler,
  DirectEventHandler,
  Double,
  Int32,
  WithDefault,
} from 'react-native/Libraries/Types/CodegenTypes';

export type MacTextViewChangeEvent = Readonly<{
  text: string;
}>;

export type MacTextViewSubmitEvent = Readonly<{
  text: string;
}>;

export type MacTextViewContentSizeChangeEvent = Readonly<{
  width: Double;
  height: Double;
  textLength: Int32;
}>;

export interface NativeProps extends ViewProps {
  initialText?: string;
  placeholder?: string;
  editable?: WithDefault<boolean, true>;
  autoGrow?: WithDefault<boolean, false>;
  maxHeight?: WithDefault<Double, 0>;
  textColor?: ColorValue;
  placeholderTextColor?: ColorValue;
  fontSize?: WithDefault<Double, 13>;
  onChange?: BubblingEventHandler<MacTextViewChangeEvent>;
  onSubmit?: BubblingEventHandler<MacTextViewSubmitEvent>;
  onMacContentSizeChange?: DirectEventHandler<MacTextViewContentSizeChangeEvent>;
}

export interface NativeCommands {
  setText: (
    viewRef: React.ElementRef<HostComponent<NativeProps>>,
    text: string,
  ) => void;
  focus: (viewRef: React.ElementRef<HostComponent<NativeProps>>) => void;
}

export const Commands = codegenNativeCommands<NativeCommands>({
  supportedCommands: ['setText', 'focus'],
});

export default codegenNativeComponent<NativeProps>(
  'CLCMacTextView',
) as HostComponent<NativeProps>;