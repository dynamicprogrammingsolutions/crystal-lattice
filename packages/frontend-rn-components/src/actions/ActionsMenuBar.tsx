import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  StyleSheet,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme } from '../theme';
import { ActionsMenuPanel } from './ActionsMenuPanel';
import {
  DropdownMenuSurface,
  ModalMenuSurface,
  type DropdownMenuSurfaceProps,
  type MenuSurfaceBaseProps,
} from './MenuSurfaces';
import type { ActionDefinition, ActionKey } from './types';
import { useActionsMenuModel } from './useActionsMenuModel';

export interface ActionsMenuBarProps<TDef extends ActionDefinition = ActionDefinition> {
  title: string;
  baseActions: readonly TDef[];
  extraActions?: readonly TDef[];
  availableActions?: readonly ActionKey[];
  pinned: readonly ActionKey[];
  onChangePinned: (nextPinned: ActionKey[]) => void;
  onAction: (key: ActionKey) => void;
  isActionDisabled?: (key: ActionKey) => boolean;
  isActive?: boolean;

  variant?: 'modal' | 'dropdown';
  dropdownOffset?: DropdownMenuSurfaceProps['offset'];
  backdropStyle?: MenuSurfaceBaseProps['backdropStyle'];
  modalContentStyle?: MenuSurfaceBaseProps['contentStyle'];
  dropdownMenuStyle?: DropdownMenuSurfaceProps['menuStyle'];
  style?: StyleProp<ViewStyle>;

  getIconName?: (action: TDef) => string | null;
}

export function ActionsMenuBar<TDef extends ActionDefinition>(
  props: ActionsMenuBarProps<TDef>,
): React.JSX.Element {
  const theme = useTheme();
  const variant = props.variant ?? 'modal';
  const [menuVisible, setMenuVisible] = useState(false);
  const menuAnchorRef = useRef<any>(null);

  useEffect(() => {
    if (props.isActive === false) {
      setMenuVisible(false);
    }
  }, [props.isActive]);

  const { model, togglePinned } = useActionsMenuModel<TDef>({
    baseActions: props.baseActions,
    extraActions: props.extraActions,
    availableActions: props.availableActions,
    pinned: props.pinned,
    onChangePinned: props.onChangePinned,
    isActionDisabled: props.isActionDisabled,
  });

  const getIconName =
    props.getIconName ??
    ((action: TDef) =>
      typeof (action as any).iconName === 'string' ? (action as any).iconName : null);

  const pinnedButtons = useMemo(() => {
    return model.visiblePinned
      .map((action) => {
        const iconName = getIconName(action);
        if (!iconName) {
          return null;
        }
        const disabled = props.isActionDisabled ? props.isActionDisabled(action.key) : false;
        return (
          <TouchableOpacity
            key={action.key}
            style={styles.iconButton}
            onPress={() => props.onAction(action.key)}
            disabled={disabled}
          >
            <Icon name={iconName} size={16} color={theme.primary} />
          </TouchableOpacity>
        );
      })
      .filter((el): el is React.JSX.Element => Boolean(el));
  }, [
    model.visiblePinned,
    getIconName,
    props.isActionDisabled,
    props.onAction,
    theme.primary,
  ]);

  const handleSelectAction = (key: ActionKey) => {
    setMenuVisible(false);
    props.onAction(key);
  };

  const panel = (
    <ActionsMenuPanel
      title={props.title}
      actions={model.orderedActions}
      pinnedKeys={props.pinned}
      onAction={handleSelectAction}
      onTogglePinned={(key) => togglePinned(key)}
      isActionDisabled={props.isActionDisabled}
      getIconName={getIconName}
      iconSize={16}
      pinIconSize={14}
      onRequestClose={() => setMenuVisible(false)}
    />
  );

  return (
    <>
      <View style={[styles.actionsRow, props.style]}>
        {pinnedButtons}
        <View ref={menuAnchorRef} collapsable={false}>
          <TouchableOpacity
            style={styles.iconButton}
            onPress={() => setMenuVisible(true)}
          >
            <Icon name="more-horizontal" size={18} color={theme.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {variant === 'modal' ? (
        <ModalMenuSurface
          visible={menuVisible}
          onRequestClose={() => setMenuVisible(false)}
          backdropStyle={props.backdropStyle}
          contentStyle={props.modalContentStyle}
        >
          {panel}
        </ModalMenuSurface>
      ) : (
        <DropdownMenuSurface
          visible={menuVisible}
          onRequestClose={() => setMenuVisible(false)}
          anchorRef={menuAnchorRef}
          offset={props.dropdownOffset}
          backdropStyle={props.backdropStyle}
          menuStyle={props.dropdownMenuStyle}
        >
          {panel}
        </DropdownMenuSurface>
      )}
    </>
  );
}

const styles = StyleSheet.create({
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 4,
  },
  iconButton: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginLeft: 4,
  },
});
