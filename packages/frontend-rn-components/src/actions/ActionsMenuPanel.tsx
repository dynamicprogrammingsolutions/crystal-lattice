import React, { useMemo } from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { useTheme } from '../theme';
import {
  ActionsMenuContent,
  type ActionsMenuContentProps,
  type MenuIconRenderer,
} from './ActionsMenuContent';
import type { ActionDefinition, ActionKey } from './types';

export interface ActionsMenuPanelProps<TDef extends ActionDefinition = ActionDefinition>
  extends Pick<
    ActionsMenuContentProps<TDef>,
    | 'actions'
    | 'pinnedKeys'
    | 'onAction'
    | 'onTogglePinned'
    | 'isActionDisabled'
    | 'getIconName'
    | 'renderIcon'
    | 'renderPinIcon'
    | 'iconSize'
    | 'pinIconSize'
    | 'renderItem'
  > {
  title: string;
  onRequestClose?: () => void;
  renderCloseIcon?: (params: { size: number; color: string; renderIcon?: MenuIconRenderer }) => React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function ActionsMenuPanel<TDef extends ActionDefinition>(
  props: ActionsMenuPanelProps<TDef>,
): React.JSX.Element {
  const theme = useTheme();
  const borderStyle = useMemo(() => ({ borderBottomColor: theme.border }), [theme.border]);

  return (
    <View style={props.style}>
      <View style={[styles.header, borderStyle]}>
        <Text style={[styles.headerText, { color: theme.text }]}>{props.title}</Text>
        {props.onRequestClose ? (
          <TouchableOpacity style={styles.closeButton} onPress={props.onRequestClose}>
            {props.renderCloseIcon ? (
              props.renderCloseIcon({
                size: 16,
                color: theme.textSecondary,
                renderIcon: props.renderIcon,
              })
            ) : (
              <Text style={[styles.closeText, { color: theme.textSecondary }]}>×</Text>
            )}
          </TouchableOpacity>
        ) : null}
      </View>
      <ActionsMenuContent
        actions={props.actions}
        pinnedKeys={props.pinnedKeys}
        onAction={props.onAction}
        onTogglePinned={props.onTogglePinned}
        isActionDisabled={props.isActionDisabled}
        getIconName={props.getIconName}
        renderIcon={props.renderIcon}
        renderPinIcon={props.renderPinIcon}
        iconSize={props.iconSize}
        pinIconSize={props.pinIconSize}
        renderItem={props.renderItem}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
    marginBottom: 4,
  },
  headerText: {
    fontSize: 14,
    fontWeight: '600',
  },
  closeButton: {
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
  closeText: {
    fontSize: 18,
    fontWeight: '800',
    marginTop: -2,
  },
});
