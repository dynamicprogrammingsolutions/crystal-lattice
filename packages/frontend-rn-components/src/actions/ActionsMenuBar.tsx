import React, { useEffect, useMemo, useRef, useState } from "react";
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
} from "react-native";

import { useTheme } from "../theme";
import {
  ActionsMenuPanel,
  type ActionsMenuPanelProps,
} from "./ActionsMenuPanel";
import type { MenuIconRenderer } from "./ActionsMenuContent";
import {
  DropdownMenuSurface,
  ModalMenuSurface,
  type DropdownMenuSurfaceProps,
  type MenuSurfaceBaseProps,
} from "./MenuSurfaces";
import type { ActionDefinition, ActionKey } from "./types";
import type { ActionsMenuPinnedRenderParams } from "./types";
import { useActionsMenuModel } from "./useActionsMenuModel";
import {
  clearActiveActionsPopoverMenu,
  setLastActionsPopoverAnchorTag,
  setActiveActionsPopoverMenu,
  updateActiveActionsPopoverMenuData,
} from "./actionsPopoverCoordinator";
import { limitPinnedActionsForBar } from "./model";

const ICON_BUTTON_HIT_SLOP = { top: 10, bottom: 10, left: 10, right: 10 };
export const ACTIONS_MENU_BAR_ITEM_WIDTH = 44;

export interface ActionsMenuBarProps<
  TDef extends ActionDefinition = ActionDefinition,
> {
  title: string;
  baseActions: readonly TDef[];
  extraActions?: readonly TDef[];
  availableActions?: readonly ActionKey[];
  pinned: readonly ActionKey[];
  /** When set, only these pinned keys show as bar icons; modal still uses full pinned for star state. */
  pinnedKeysForBar?: readonly ActionKey[];
  /** Limits only compact pinned buttons; all actions and pin states remain available in the menu. */
  maxPinnedActionsForBar?: number;
  /** Enables one or two compact pinned rows. The default is one. */
  pinnedRows?: 1 | 2;
  /** Places the second pinned row above or below the primary/menu row. */
  secondPinnedRowPlacement?: "above" | "below";
  onChangePinned: (nextPinned: ActionKey[]) => void;
  onAction: (key: ActionKey) => void;
  onOpenMenu?: () => void;
  menuButtonTestID?: string;
  isActionDisabled?: (key: ActionKey) => boolean;
  isActive?: boolean;

  renderIcon?: MenuIconRenderer;
  renderPinIcon?: (params: {
    pinned: boolean;
    size: number;
    color: string;
  }) => React.ReactNode;
  renderCloseIcon?: (params: {
    size: number;
    color: string;
    renderIcon?: MenuIconRenderer;
  }) => React.ReactNode;

  variant?: "modal" | "dropdown";
  dropdownOffset?: DropdownMenuSurfaceProps["offset"];
  backdropStyle?: MenuSurfaceBaseProps["backdropStyle"];
  modalContentStyle?: MenuSurfaceBaseProps["contentStyle"];
  dropdownMenuStyle?: DropdownMenuSurfaceProps["menuStyle"];
  style?: StyleProp<ViewStyle>;

  getIconName?: (action: TDef) => string | null;
  renderPinnedAction?: (
    params: ActionsMenuPinnedRenderParams<TDef>,
  ) => React.ReactNode | undefined;
  renderItem?: ActionsMenuPanelProps<TDef>["renderItem"];
}

export function ActionsMenuBar<TDef extends ActionDefinition>(
  props: ActionsMenuBarProps<TDef>,
): React.JSX.Element {
  const theme = useTheme();
  const variant = props.variant ?? "modal";
  const pinnedRows = props.pinnedRows ?? 1;
  const secondPinnedRowPlacement = props.secondPinnedRowPlacement ?? "below";
  const [menuVisible, setMenuVisible] = useState(false);
  const menuAnchorRef = useRef<any>(null);
  const menuIdRef = useRef<string>(
    `actions-menu-${Math.random().toString(36).slice(2)}`,
  );

  const desktopWindowManager = (NativeModules as any)?.DesktopWindowManager as
    | {
        toggleActionsPopover?: (params: {
          anchorTag: number;
          menuId: string;
          rows: Array<{ label: string; stateLabel?: string; hasIcon: boolean }>;
          fontSize: number;
          stateFontSize: number;
          width?: number;
          height?: number;
        }) => void;
        closeActionsPopover?: () => void;
      }
    | undefined;

  const isMacOSPopoverMenu =
    Platform.OS === "macos" &&
    variant === "dropdown" &&
    typeof desktopWindowManager?.toggleActionsPopover === "function";

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
      typeof (action as any).iconName === "string"
        ? (action as any).iconName
        : null);

  const pinnedButtons = useMemo(() => {
    const barPinned =
      props.pinnedKeysForBar != null
        ? model.visiblePinned.filter((action) =>
            props.pinnedKeysForBar!.includes(action.key),
          )
        : model.visiblePinned;
    return limitPinnedActionsForBar(barPinned, props.maxPinnedActionsForBar)
      .map((action) => {
        const iconName = getIconName(action);
        const disabled = props.isActionDisabled
          ? props.isActionDisabled(action.key)
          : false;
        const iconColor = disabled ? theme.textMuted : theme.primary;
        const fallbackLabel = action.label.trim().slice(0, 1) || "•";
        const onPress = () => {
          if (Platform.OS === "macos" && menuAnchorRef.current) {
            try {
              const anchorTag = findNodeHandle(menuAnchorRef.current) as any;
              setLastActionsPopoverAnchorTag(
                typeof anchorTag === "number" ? anchorTag : null,
              );
            } catch {
              setLastActionsPopoverAnchorTag(null);
            }
          }
          props.onAction(action.key);
        };
        const custom = props.renderPinnedAction?.({
          action,
          disabled,
          iconName,
          iconColor,
          onPress,
        });
        if (custom !== undefined) {
          return (
            <View key={action.key} style={styles.customPinnedActionSlot}>
              {custom}
            </View>
          );
        }
        return (
          <TouchableOpacity
            key={action.key}
            style={styles.iconButton}
            hitSlop={ICON_BUTTON_HIT_SLOP}
            accessibilityRole="button"
            accessibilityLabel={action.label}
            testID={
              typeof action.testID === "string" ? action.testID : undefined
            }
            onPress={onPress}
            disabled={disabled}
          >
            {iconName && props.renderIcon ? (
              props.renderIcon({ name: iconName, size: 16, color: iconColor })
            ) : (
              <Text
                style={[
                  styles.fallbackIcon,
                  {
                    color: iconColor,
                    fontSize: theme.typography.fontSize.normal,
                  },
                ]}
              >
                {fallbackLabel}
              </Text>
            )}
          </TouchableOpacity>
        );
      })
      .filter((el): el is React.JSX.Element => Boolean(el));
  }, [
    model.visiblePinned,
    props.pinnedKeysForBar,
    props.maxPinnedActionsForBar,
    getIconName,
    props.isActionDisabled,
    props.renderIcon,
    props.renderPinnedAction,
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
        .filter((action) =>
          props.isActionDisabled ? props.isActionDisabled(action.key) : false,
        )
        .map((action) => action.key),
      renderItem: props.renderItem as any,
    });
  }, [
    getIconName,
    isMacOSPopoverMenu,
    model.orderedActions,
    props.isActionDisabled,
    props.pinned,
    props.renderItem,
    props.title,
  ]);

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
      iconSize={18}
      pinIconSize={16}
      renderItem={props.renderItem}
      onRequestClose={() => setMenuVisible(false)}
    />
  );

  return (
    <>
      <View style={[styles.actionsRow, props.style]} testID="actions-menu-bar">
        <View
          style={[
            styles.pinnedActionsViewport,
            pinnedRows === 2 && styles.pinnedActionsViewportTwoRows,
            pinnedRows === 2 &&
              (secondPinnedRowPlacement === "above"
                ? styles.pinnedActionsWrapAbove
                : styles.pinnedActionsWrapBelow),
          ]}
          testID="actions-menu-pinned-viewport"
        >
          {pinnedButtons}
        </View>
        <View
          ref={menuAnchorRef}
          collapsable={false}
          style={[
            styles.menuButtonSlot,
            pinnedRows === 2 &&
              (secondPinnedRowPlacement === "above"
                ? styles.menuButtonSlotBottom
                : styles.menuButtonSlotTop),
          ]}
          testID="actions-menu-overflow-slot"
        >
          <TouchableOpacity
            style={styles.iconButton}
            hitSlop={ICON_BUTTON_HIT_SLOP}
            accessibilityLabel={`Open ${props.title}`}
            accessibilityRole="button"
            testID={props.menuButtonTestID}
            onPress={() => {
              if (isMacOSPopoverMenu) {
                const anchorTag = menuAnchorRef.current
                  ? (findNodeHandle(menuAnchorRef.current) as any)
                  : null;
                if (typeof anchorTag !== "number") {
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
                    props.isActionDisabled
                      ? props.isActionDisabled(action.key)
                      : false,
                  )
                  .map((action) => action.key);

                const close = () => {
                  desktopWindowManager?.closeActionsPopover?.();
                  clearActiveActionsPopoverMenu(menuId);
                };

                props.onOpenMenu?.();
                setActiveActionsPopoverMenu({
                  data: {
                    id: menuId,
                    title: props.title,
                    actions,
                    pinnedKeys: props.pinned,
                    disabledKeys,
                    renderItem: props.renderItem as any,
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

                desktopWindowManager?.toggleActionsPopover?.({
                  anchorTag,
                  menuId,
                  rows: actions.map((action) => ({
                    label: action.label,
                    stateLabel: action.menuStateLabel,
                    hasIcon: Boolean(action.iconName),
                  })),
                  fontSize: theme.typography.fontSize.message,
                  stateFontSize: theme.typography.fontSize.secondary,
                  height: 44 + 12 + actions.length * 44,
                });
                return;
              }

              props.onOpenMenu?.();
              setMenuVisible(true);
            }}
          >
            {props.renderIcon ? (
              props.renderIcon({
                name: "more-horizontal",
                size: 18,
                color: theme.primary,
              })
            ) : (
              <Text
                style={[
                  styles.moreText,
                  {
                    color: theme.primary,
                    fontSize: theme.typography.fontSize.title,
                  },
                ]}
              >
                ⋯
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {isMacOSPopoverMenu ? null : variant === "modal" ? (
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
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-end",
    alignSelf: "stretch",
    flexShrink: 1,
    minWidth: 0,
    maxWidth: "100%",
    marginTop: 4,
  },
  pinnedActionsViewport: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-end",
    flexShrink: 1,
    minWidth: 0,
    overflow: "hidden",
  },
  pinnedActionsViewportTwoRows: {
    minHeight: 40,
    maxHeight: 82,
    flexWrap: "wrap",
    alignItems: "center",
    alignContent: "flex-start",
    rowGap: 2,
  },
  pinnedActionsWrapAbove: {
    flexWrap: "wrap-reverse",
    alignContent: "flex-end",
  },
  pinnedActionsWrapBelow: {
    flexWrap: "wrap",
    alignContent: "flex-start",
  },
  menuButtonSlot: {
    width: ACTIONS_MENU_BAR_ITEM_WIDTH,
    flexShrink: 0,
  },
  menuButtonSlotTop: {
    alignSelf: "flex-start",
  },
  menuButtonSlotBottom: {
    alignSelf: "flex-end",
  },
  iconButton: {
    width: ACTIONS_MENU_BAR_ITEM_WIDTH,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  customPinnedActionSlot: {
    height: 40,
    flexShrink: 0,
    alignItems: "center",
    justifyContent: "center",
  },
  moreText: {
    fontWeight: "800",
    marginTop: -3,
  },
  fallbackIcon: {
    fontWeight: "800",
  },
});
