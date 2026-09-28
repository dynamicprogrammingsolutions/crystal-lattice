import React, { useMemo } from "react";
import {
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";

import { useTheme } from "../theme";
import type { ActionDefinition, ActionKey } from "./types";

const PIN_BUTTON_HIT_SLOP = { top: 4, bottom: 4, left: 4, right: 4 };

export interface MenuIconRenderParams {
  name: string;
  size: number;
  color: string;
}

export type MenuIconRenderer = (
  params: MenuIconRenderParams
) => React.ReactNode;

export interface ActionsMenuRenderItemParams<
  TDef extends ActionDefinition = ActionDefinition
> {
  action: TDef;
  pinned: boolean;
  disabled: boolean;
  onPressAction: () => void;
  onTogglePinned: () => void;
}

export interface ActionsMenuContentProps<
  TDef extends ActionDefinition = ActionDefinition
> {
  actions: readonly TDef[];
  pinnedKeys: readonly ActionKey[];
  onAction: (key: ActionKey) => void;
  onTogglePinned: (key: ActionKey) => void;
  isActionDisabled?: (key: ActionKey) => boolean;
  getIconName?: (action: TDef) => string | null;
  renderIcon?: MenuIconRenderer;
  renderPinIcon?: (params: {
    pinned: boolean;
    size: number;
    color: string;
  }) => React.ReactNode;
  iconSize?: number;
  pinIconSize?: number;
  renderItem?: (params: ActionsMenuRenderItemParams<TDef>) => React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function ActionsMenuContent<TDef extends ActionDefinition>(
  props: ActionsMenuContentProps<TDef>
): React.JSX.Element {
  const theme = useTheme();
  const pinnedSet = useMemo(
    () => new Set(props.pinnedKeys),
    [props.pinnedKeys]
  );
  const isActionDisabled = props.isActionDisabled ?? (() => false);
  const iconSize = props.iconSize ?? 16;
  const pinIconSize = props.pinIconSize ?? 14;
  const getIconName =
    props.getIconName ??
    ((action: TDef) =>
      typeof (action as any).iconName === "string"
        ? (action as any).iconName
        : null);

  return (
    <View style={[styles.container, props.style]}>
      {props.actions.map((action) => {
        const pinned = pinnedSet.has(action.key);
        const disabled = isActionDisabled(action.key);

        const onPressAction = () => {
          if (disabled) {
            return;
          }
          props.onAction(action.key);
        };

        const onTogglePinned = () => {
          props.onTogglePinned(action.key);
        };

        if (props.renderItem) {
          return (
            <React.Fragment key={action.key}>
              {props.renderItem({
                action,
                pinned,
                disabled,
                onPressAction,
                onTogglePinned,
              })}
            </React.Fragment>
          );
        }

        const iconName = getIconName(action);
        const iconColor = disabled ? theme.textSecondary : theme.primary;
        const pinColor = pinned ? theme.highlight : "#C7C7CC";
        const menuStateLabel =
          typeof action.menuStateLabel === "string" &&
          action.menuStateLabel.trim()
            ? action.menuStateLabel.trim()
            : null;

        return (
          <View key={action.key} style={styles.menuItem}>
            <TouchableOpacity
              style={styles.menuItemLeft}
              testID={`actions-menu-action-${String(action.key)}`}
              accessibilityLabel={
                menuStateLabel
                  ? `${action.label}: ${menuStateLabel}`
                  : action.label
              }
              accessibilityRole="button"
              accessibilityActions={
                Platform.OS === "macos"
                  ? undefined
                  : [{ name: "activate", label: action.label }]
              }
              onAccessibilityAction={
                Platform.OS === "macos"
                  ? undefined
                  : (event) => {
                      if (event.nativeEvent.actionName === "activate") {
                        onPressAction();
                      }
                    }
              }
              onPress={onPressAction}
              disabled={disabled}
            >
              {iconName && props.renderIcon ? (
                <View style={styles.iconButton}>
                  {props.renderIcon({
                    name: iconName,
                    size: iconSize,
                    color: iconColor,
                  })}
                </View>
              ) : null}
              <Text
                numberOfLines={1}
                ellipsizeMode="tail"
                style={[
                  styles.menuItemText,
                  iconName && styles.menuItemTextWithIcon,
                  {
                    color: disabled ? theme.textSecondary : theme.text,
                    fontSize: theme.typography.fontSize.message,
                    lineHeight: theme.typography.lineHeight.message,
                  },
                ]}
              >
                {action.label}
              </Text>
              {menuStateLabel ? (
                <Text
                  testID={`actions-menu-state-${String(action.key)}`}
                  numberOfLines={1}
                  ellipsizeMode="tail"
                  style={[
                    styles.menuStateText,
                    {
                      color: theme.textSecondary,
                      fontSize: theme.typography.fontSize.secondary,
                      lineHeight: theme.typography.lineHeight.secondary,
                    },
                  ]}
                >
                  {menuStateLabel}
                </Text>
              ) : null}
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.pinButton}
              hitSlop={PIN_BUTTON_HIT_SLOP}
              accessibilityRole="button"
              accessibilityLabel={`${pinned ? "Unpin" : "Pin"} ${action.label}`}
              testID={`actions-menu-pin-${String(action.key)}`}
              onPress={onTogglePinned}
            >
              {props.renderPinIcon ? (
                props.renderPinIcon({
                  pinned,
                  size: pinIconSize,
                  color: pinColor,
                })
              ) : (
                <Text
                  style={[
                    styles.pinText,
                    { fontSize: pinIconSize, color: pinColor },
                  ]}
                >
                  {pinned ? "★" : "☆"}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    paddingVertical: 0,
    minHeight: 44,
  },
  menuItemLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    minWidth: 0,
  },
  iconButton: {
    width: 34,
    flexShrink: 0,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 0,
    paddingVertical: 2,
  },
  menuItemText: {
    flexShrink: 1,
    minWidth: 0,
  },
  menuItemTextWithIcon: {
    marginLeft: 8,
  },
  menuStateText: {
    flexShrink: 1,
    minWidth: 0,
    marginLeft: "auto",
    paddingLeft: 12,
    textAlign: "right",
  },
  pinButton: {
    minWidth: 44,
    minHeight: 44,
    flexShrink: 0,
    alignItems: "center",
    justifyContent: "center",
  },
  pinText: {
    fontWeight: "800",
  },
});
