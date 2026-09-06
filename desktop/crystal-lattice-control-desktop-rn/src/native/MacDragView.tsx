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

export interface MacDragViewProps extends ViewProps {
  mouseDownCanMoveWindow?: boolean;
  onDragStart?: (event: MacDragEvent) => void;
  onDragMove?: (event: MacDragEvent) => void;
  onDragEnd?: (event: MacDragEvent) => void;
  onDragCancel?: (event: MacDragEvent) => void;
}

type NativeMacDragViewProps = Omit<
  MacDragViewProps,
  'onDragStart' | 'onDragMove' | 'onDragEnd' | 'onDragCancel'
> & {
  onDragStart?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
  onDragMove?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
  onDragEnd?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
  onDragCancel?: (event: NativeSyntheticEvent<MacDragEvent>) => void;
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
    />
  );
}
