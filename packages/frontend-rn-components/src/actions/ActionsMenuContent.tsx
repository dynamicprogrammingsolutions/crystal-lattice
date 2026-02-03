import React, { useMemo } from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme } from '../theme';
import type { ActionDefinition, ActionKey } from './types';

export interface ActionsMenuRenderItemParams<TDef extends ActionDefinition = ActionDefinition> {
  action: TDef;
  pinned: boolean;
  disabled: boolean;
  onPressAction: () => void;
  onTogglePinned: () => void;
}

export interface ActionsMenuContentProps<TDef extends ActionDefinition = ActionDefinition> {
  actions: readonly TDef[];
  pinnedKeys: readonly ActionKey[];
  onAction: (key: ActionKey) => void;
  onTogglePinned: (key: ActionKey) => void;
  isActionDisabled?: (key: ActionKey) => boolean;
  getIconName?: (action: TDef) => string | null;
  iconSize?: number;
  pinIconSize?: number;
  renderItem?: (params: ActionsMenuRenderItemParams<TDef>) => React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function ActionsMenuContent<TDef extends ActionDefinition>(
  props: ActionsMenuContentProps<TDef>,
): React.JSX.Element {
  const theme = useTheme();
  const pinnedSet = useMemo(() => new Set(props.pinnedKeys), [props.pinnedKeys]);
  const isActionDisabled = props.isActionDisabled ?? (() => false);
  const iconSize = props.iconSize ?? 16;
  const pinIconSize = props.pinIconSize ?? 14;
  const getIconName =
    props.getIconName ??
    ((action: TDef) =>
      typeof (action as any).iconName === 'string' ? (action as any).iconName : null);

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

        return (
          <View key={action.key} style={styles.menuItem}>
            <TouchableOpacity
              style={styles.menuItemLeft}
              onPress={onPressAction}
              disabled={disabled}
            >
              {iconName ? (
                <View style={styles.iconButton}>
                  <Icon
                    name={iconName}
                    size={iconSize}
                    color={disabled ? theme.textSecondary : theme.primary}
                  />
                </View>
              ) : null}
              <Text
                style={[
                  styles.menuItemText,
                  { color: disabled ? theme.textSecondary : theme.text },
                ]}
              >
                {action.label}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.pinButton} onPress={onTogglePinned}>
              <Icon
                name="star"
                size={pinIconSize}
                color={pinned ? '#FFCC00' : '#C7C7CC'}
              />
            </TouchableOpacity>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconButton: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginLeft: 4,
  },
  menuItemText: {
    marginLeft: 8,
    fontSize: 14,
  },
  pinButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
});
