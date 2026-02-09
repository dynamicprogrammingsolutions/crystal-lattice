import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Platform,
  Text,
  StyleSheet,
  TouchableOpacity,
  View,
  findNodeHandle,
  NativeModules,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { useTheme } from '../theme';
import { ActionsMenuPanel } from './ActionsMenuPanel';
import type { MenuIconRenderer } from './ActionsMenuContent';
import {
  DropdownMenuSurface,
  ModalMenuSurface,
  type DropdownMenuSurfaceProps,
  type MenuSurfaceBaseProps,
} from './MenuSurfaces';
import type { ActionDefinition, ActionKey } from './types';
import { useActionsMenuModel } from './useActionsMenuModel';
import {
  clearActiveActionsPopoverMenu,
  setLastActionsPopoverAnchorTag,
  setActiveActionsPopoverMenu,
  updateActiveActionsPopoverMenuData,
} from './actionsPopoverCoordinator';

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

  renderIcon?: MenuIconRenderer;
  renderPinIcon?: (params: { pinned: boolean; size: number; color: string }) => React.ReactNode;
  renderCloseIcon?: (params: { size: number; color: string; renderIcon?: MenuIconRenderer }) => React.ReactNode;

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
  const menuIdRef = useRef<string>(`actions-menu-${Math.random().toString(36).slice(2)}`);

  const desktopWindowManager = (NativeModules as any)?.DesktopWindowManager as
    | {
        toggleActionsPopover?: (params: { anchorTag: number; width?: number; height?: number }) => void;
        closeActionsPopover?: () => void;
      }
    | undefined;

  const isMacOSPopoverMenu =
    Platform.OS === 'macos' &&
    variant === 'dropdown' &&
    typeof desktopWindowManager?.toggleActionsPopover === 'function';

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
        const disabled = props.isActionDisabled ? props.isActionDisabled(action.key) : false;
        const iconColor = disabled ? theme.textMuted : theme.primary;
        const fallbackLabel = action.label.trim().slice(0, 1) || '•';
        return (
          <TouchableOpacity
            key={action.key}
            style={styles.iconButton}
            onPress={() => {
              if (Platform.OS === 'macos' && menuAnchorRef.current) {
                try {
                  const anchorTag = findNodeHandle(menuAnchorRef.current) as any;
                  setLastActionsPopoverAnchorTag(typeof anchorTag === 'number' ? anchorTag : null);
                } catch {
                  setLastActionsPopoverAnchorTag(null);
                }
              }
              props.onAction(action.key);
            }}
            disabled={disabled}
          >
            {iconName && props.renderIcon ? (
              props.renderIcon({ name: iconName, size: 16, color: iconColor })
            ) : (
              <Text style={[styles.fallbackIcon, { color: iconColor }]}>{fallbackLabel}</Text>
            )}
          </TouchableOpacity>
        );
      })
      .filter((el): el is React.JSX.Element => Boolean(el));
  }, [
    model.visiblePinned,
    getIconName,
    props.isActionDisabled,
    props.renderIcon,
    props.onAction,
    theme.primary,
    theme.textMuted,
  ]);

  const handleSelectAction = (key: ActionKey) => {
    setMenuVisible(false);
    props.onAction(key);
  };

  useEffect(() => {
    if (!isMacOSPopoverMenu) {
      return;
    }

    const menuId = menuIdRef.current;
    updateActiveActionsPopoverMenuData({
      id: menuId,
      title: props.title,
      actions: model.orderedActions.map((action) => ({
        ...action,
        iconName: getIconName(action),
      })),
      pinnedKeys: props.pinned,
      disabledKeys: model.orderedActions
        .filter((action) => (props.isActionDisabled ? props.isActionDisabled(action.key) : false))
        .map((action) => action.key),
    });
  }, [getIconName, isMacOSPopoverMenu, model.orderedActions, props.isActionDisabled, props.pinned, props.title]);

  const panel = (
    <ActionsMenuPanel
      title={props.title}
      actions={model.orderedActions}
      pinnedKeys={props.pinned}
      onAction={handleSelectAction}
      onTogglePinned={(key) => togglePinned(key)}
      isActionDisabled={props.isActionDisabled}
      getIconName={getIconName}
      renderIcon={props.renderIcon}
      renderPinIcon={props.renderPinIcon}
      renderCloseIcon={props.renderCloseIcon}
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
            onPress={() => {
              if (isMacOSPopoverMenu) {
                const anchorTag = menuAnchorRef.current
                  ? (findNodeHandle(menuAnchorRef.current) as any)
                  : null;
                if (typeof anchorTag !== 'number') {
                  return;
                }

                setLastActionsPopoverAnchorTag(anchorTag);

                const menuId = menuIdRef.current;
                const actions = model.orderedActions.map((action) => ({
                  ...action,
                  iconName: getIconName(action),
                }));
                const disabledKeys = model.orderedActions
                  .filter((action) =>
                    props.isActionDisabled ? props.isActionDisabled(action.key) : false,
                  )
                  .map((action) => action.key);

                const close = () => {
                  desktopWindowManager?.closeActionsPopover?.();
                  clearActiveActionsPopoverMenu(menuId);
                };

                setActiveActionsPopoverMenu({
                  data: {
                    id: menuId,
                    title: props.title,
                    actions,
                    pinnedKeys: props.pinned,
                    disabledKeys,
                  },
                  handlers: {
                    onAction: (key) => {
                      close();
                      props.onAction(key);
                    },
                    onTogglePinned: (key) => {
                      togglePinned(key);
                    },
                    onRequestClose: () => {
                      close();
                    },
                  },
                });

                const rowHeight = 42;
                const headerHeight = 44;
                const paddingHeight = 12;
                const maxVisibleRows = 8;
                const height =
                  headerHeight +
                  paddingHeight +
                  Math.min(actions.length, maxVisibleRows) * rowHeight;

                desktopWindowManager?.toggleActionsPopover?.({
                  anchorTag,
                  width: 320,
                  height: Math.max(140, Math.min(420, height)),
                });
                return;
              }

              setMenuVisible(true);
            }}
          >
            {props.renderIcon ? (
              props.renderIcon({ name: 'more-horizontal', size: 18, color: theme.primary })
            ) : (
              <Text style={[styles.moreText, { color: theme.primary }]}>⋯</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {isMacOSPopoverMenu ? null : variant === 'modal' ? (
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
  moreText: {
    fontSize: 18,
    fontWeight: '800',
    marginTop: -3,
  },
  fallbackIcon: {
    fontSize: 14,
    fontWeight: '800',
  },
});
