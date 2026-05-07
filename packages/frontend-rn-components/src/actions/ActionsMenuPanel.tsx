import React, { useMemo } from 'react';
import {
  ScrollView,
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
  const themedStyles = useMemo(
    () => ({
      root: {
        backgroundColor: theme.surface,
      },
      headerRow: {
        borderBottomColor: theme.border,
      },
      titleText: {
        color: theme.text,
        fontSize: theme.typography.fontSize.title,
      },
      closeButtonText: {
        color: theme.primary,
        fontSize: theme.typography.fontSize.normal,
      },
    }),
    [
      theme.border,
      theme.primary,
      theme.surface,
      theme.text,
      theme.typography.fontSize.normal,
      theme.typography.fontSize.title,
    ],
  );

  return (
    <View style={[styles.root, themedStyles.root, props.style]}>
      <View style={[styles.headerRow, themedStyles.headerRow]}>
        <Text style={[styles.titleText, themedStyles.titleText]}>{props.title}</Text>
        {props.onRequestClose ? (
          <TouchableOpacity style={styles.closeButton} onPress={props.onRequestClose}>
            {props.renderCloseIcon ? (
              props.renderCloseIcon({
                size: 16,
                color: theme.primary,
                renderIcon: props.renderIcon,
              })
            ) : (
              <Text style={[styles.closeButtonText, themedStyles.closeButtonText]}>Close</Text>
            )}
          </TouchableOpacity>
        ) : null}
      </View>
      <View style={styles.body}>
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
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
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    width: '100%',
    borderRadius: 12,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  titleText: {
    fontWeight: '600',
  },
  body: {
    flexGrow: 0,
    flexShrink: 1,
  },
  scroll: {
    flexGrow: 0,
    flexShrink: 1,
  },
  scrollContent: {
    paddingVertical: 8,
  },
  closeButton: {
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  closeButtonText: {
    fontWeight: '600',
  },
});
