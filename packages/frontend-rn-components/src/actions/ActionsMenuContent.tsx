import React, { useMemo } from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

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
  renderItem?: (params: ActionsMenuRenderItemParams<TDef>) => React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function ActionsMenuContent<TDef extends ActionDefinition>(
  props: ActionsMenuContentProps<TDef>,
): React.JSX.Element {
  const pinnedSet = useMemo(() => new Set(props.pinnedKeys), [props.pinnedKeys]);
  const isActionDisabled = props.isActionDisabled ?? (() => false);

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

        return (
          <View key={action.key} style={styles.row}>
            <TouchableOpacity
              style={styles.rowLeft}
              onPress={onPressAction}
              disabled={disabled}
            >
              <Text style={[styles.label, disabled && styles.labelDisabled]}>{action.label}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.pinButton} onPress={onTogglePinned}>
              <Text style={[styles.pinText, pinned && styles.pinTextPinned]}>
                {pinned ? '★' : '☆'}
              </Text>
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
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  label: {
    fontSize: 14,
    color: '#111111',
  },
  labelDisabled: {
    color: '#8E8E93',
  },
  pinButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  pinText: {
    fontSize: 16,
    color: '#C7C7CC',
  },
  pinTextPinned: {
    color: '#FFCC00',
  },
});
