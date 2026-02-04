import React, { useMemo } from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';

import { ActionsMenuContent, type ActionsMenuContentProps } from './ActionsMenuContent';
import {
  DropdownMenuSurface,
  ModalMenuSurface,
  type MenuSurfaceBaseProps,
  type DropdownMenuSurfaceProps,
} from './MenuSurfaces';
import type { ActionDefinition } from './types';

export interface ActionsMenuProps<TDef extends ActionDefinition = ActionDefinition>
  extends Pick<
    ActionsMenuContentProps<TDef>,
    'actions' | 'pinnedKeys' | 'onAction' | 'onTogglePinned' | 'isActionDisabled' | 'renderItem'
  > {
  variant: 'modal' | 'dropdown';
  visible: boolean;
  onRequestClose: () => void;

  /** Required when `variant === 'dropdown'`. */
  anchorRef?: React.RefObject<any>;
  offset?: { x?: number; y?: number };

  backdropStyle?: MenuSurfaceBaseProps['backdropStyle'];
  contentStyle?: MenuSurfaceBaseProps['contentStyle'];
  menuStyle?: DropdownMenuSurfaceProps['menuStyle'];
  contentContainerStyle?: StyleProp<ViewStyle>;
}

export function ActionsMenu<TDef extends ActionDefinition>(
  props: ActionsMenuProps<TDef>,
): React.JSX.Element | null {
  const content = useMemo(
    () => (
      <View style={props.contentContainerStyle}>
        <ActionsMenuContent
          actions={props.actions}
          pinnedKeys={props.pinnedKeys}
          onAction={props.onAction}
          onTogglePinned={props.onTogglePinned}
          isActionDisabled={props.isActionDisabled}
          renderItem={props.renderItem}
        />
      </View>
    ),
    [
      props.actions,
      props.pinnedKeys,
      props.onAction,
      props.onTogglePinned,
      props.isActionDisabled,
      props.renderItem,
      props.contentContainerStyle,
    ],
  );

  if (props.variant === 'modal') {
    return (
      <ModalMenuSurface
        visible={props.visible}
        onRequestClose={props.onRequestClose}
        backdropStyle={props.backdropStyle}
        contentStyle={props.contentStyle}
      >
        {content}
      </ModalMenuSurface>
    );
  }

  if (!props.anchorRef) {
    return null;
  }

  return (
    <DropdownMenuSurface
      visible={props.visible}
      onRequestClose={props.onRequestClose}
      anchorRef={props.anchorRef}
      offset={props.offset}
      backdropStyle={props.backdropStyle}
      menuStyle={props.menuStyle}
    >
      {content}
    </DropdownMenuSurface>
  );
}
