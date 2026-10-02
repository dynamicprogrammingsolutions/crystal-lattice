import React from 'react';
import {
  Platform,
  View,
  requireNativeComponent,
  type NativeSyntheticEvent,
  type ViewProps,
} from 'react-native';

export interface MacDragEvent {
  translationX: number;
  translationY: number;
  locationX: number;
  locationY: number;
  pageX: number;
  pageY: number;
}

export interface MacAuxiliaryClickEvent extends MacDragEvent {
  button: number;
}

export interface MacDragViewProps extends ViewProps {
  dragEnabled?: boolean;
  keyboardAdjustable?: boolean;
  mouseDownCanMoveWindow?: boolean;
  onDragStart?: (event: MacDragEvent) => void;
  onDragMove?: (event: MacDragEvent) => void;
  onDragEnd?: (event: MacDragEvent) => void;
  onDragCancel?: (event: MacDragEvent) => void;
  onAuxiliaryClick?: (event: MacAuxiliaryClickEvent) => void;
  onKeyIncrement?: () => void;
  onKeyDecrement?: () => void;
}

type NativeMacDragViewProps = Omit<
  MacDragViewProps,
  | 'onDragStart'
  | 'onDragMove'
  | 'onDragEnd'
  | 'onDragCancel'
  | 'onAuxiliaryClick'
  | 'onKeyIncrement'
  | 'onKeyDecrement'
> & {
  onDragStart?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
  onDragMove?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
  onDragEnd?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
  onDragCancel?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
  onAuxiliaryClick?: (
    event: NativeSyntheticEvent<MacAuxiliaryClickEvent>,
  ) => void;
  onKeyIncrement?: (event: NativeSyntheticEvent<Record<string, never>>) => void;
  onKeyDecrement?: (event: NativeSyntheticEvent<Record<string, never>>) => void;
};

const NativeMacDragView =
  Platform.OS === 'macos'
    ? requireNativeComponent<NativeMacDragViewProps>('MacDragView')
    : null;

export function MacDragView({
  onDragStart,
  onDragMove,
  onDragEnd,
  onDragCancel,
  onAuxiliaryClick,
  onKeyIncrement,
  onKeyDecrement,
  ...props
}: MacDragViewProps): React.JSX.Element {
  if (!NativeMacDragView) {
    return <View {...props} />;
  }
  return (
    <NativeMacDragView
      {...props}
      onDragStart={event => onDragStart?.(event.nativeEvent)}
      onDragMove={event => onDragMove?.(event.nativeEvent)}
      onDragEnd={event => onDragEnd?.(event.nativeEvent)}
      onDragCancel={event => onDragCancel?.(event.nativeEvent)}
      onAuxiliaryClick={event => onAuxiliaryClick?.(event.nativeEvent)}
      onKeyIncrement={() => onKeyIncrement?.()}
      onKeyDecrement={() => onKeyDecrement?.()}
    />
  );
}
