import React, { useEffect, useMemo, useState } from 'react';
import {
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { ActionsMenuContent, useActionsMenuModel } from '@crystal-lattice/frontend-rn-components';
import {
  ALL_MESSAGE_ACTIONS,
  type MessageActionDefinition,
  type MessageActionKey,
} from '../messageActions';
import { useTheme, type Theme } from '../theme';

export interface MessageActionsBarProps {
  pinned: MessageActionKey[];
  onChangePinned: (pinned: MessageActionKey[]) => void;
  onAction: (action: MessageActionKey) => void;
  isActionDisabled?: (action: MessageActionKey) => boolean;
  availableActions?: MessageActionKey[];
  extraActions?: MessageActionDefinition[];
  isActive?: boolean;
}

const MessageActionsBar: React.FC<MessageActionsBarProps> = ({
  pinned,
  onChangePinned,
  onAction,
  isActionDisabled,
  availableActions,
  extraActions,
  isActive,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [menuVisible, setMenuVisible] = useState(false);

  useEffect(() => {
    if (isActive === false) {
      setMenuVisible(false);
    }
  }, [isActive]);

  const { model, togglePinned } = useActionsMenuModel<MessageActionDefinition>({
    baseActions: ALL_MESSAGE_ACTIONS,
    extraActions,
    availableActions,
    pinned,
    onChangePinned,
    isActionDisabled,
  });

  const renderIconButton = (key: MessageActionKey) => {
    const def = model.actionsByKey[key];
    if (!def) {
      return null;
    }
    const disabled = isActionDisabled ? isActionDisabled(key) : false;
    return (
      <TouchableOpacity
        key={def.key}
        style={styles.iconButton}
        onPress={() => onAction(def.key)}
        disabled={disabled}
      >
        <Icon name={def.iconName} size={16} color={theme.primary} />
      </TouchableOpacity>
    );
  };

  return (
    <>
      <View style={styles.actionsRow}>
        {pinned.map((key) => renderIconButton(key))}
        <TouchableOpacity
          style={styles.iconButton}
          onPress={() => setMenuVisible(true)}
        >
          <Icon name="more-horizontal" size={18} color={theme.primary} />
        </TouchableOpacity>
      </View>

	      {menuVisible && (
	        <Modal
	          visible
	          transparent
	          animationType="fade"
	          onRequestClose={() => setMenuVisible(false)}
	        >
	          <TouchableWithoutFeedback onPress={() => setMenuVisible(false)}>
	            <View style={styles.menuOverlay}>
	              <TouchableWithoutFeedback onPress={() => {}}>
	                <View style={styles.menuContent}>
	                  <View style={styles.menuHeader}>
	                    <Text style={styles.menuHeaderText}>Message actions</Text>
	                    <TouchableOpacity
	                      style={styles.closeButton}
	                      onPress={() => setMenuVisible(false)}
	                    >
	                      <Icon name="x" size={16} color="#8E8E93" />
	                    </TouchableOpacity>
	                  </View>
					  <ActionsMenuContent
                    actions={model.orderedActions}
                    pinnedKeys={pinned}
                    isActionDisabled={isActionDisabled}
                    onAction={(key) => {
                      setMenuVisible(false);
                      onAction(key as MessageActionKey);
                    }}
                    onTogglePinned={(key) => {
                      togglePinned(key as MessageActionKey);
                    }}
                    renderItem={({ action: def, pinned: pinnedHere, disabled, onPressAction, onTogglePinned }) => (
                      <View style={styles.menuItem}>
                        <TouchableOpacity
                          style={styles.menuItemLeft}
                          onPress={onPressAction}
                          disabled={disabled}
                        >
                          <View style={styles.iconButton}>
                            <Icon name={def.iconName} size={16} color={theme.primary} />
                          </View>
                          <Text
                            style={[
                              styles.menuItemText,
                              disabled && { color: theme.textSecondary },
                            ]}
                          >
                            {def.label}
                          </Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={styles.pinButton}
                          onPress={onTogglePinned}
                        >
                          <Icon
                            name="star"
                            size={14}
                            color={pinnedHere ? '#FFCC00' : '#C7C7CC'}
                          />
                        </TouchableOpacity>
                      </View>
                    )}
                  />
	                </View>
	              </TouchableWithoutFeedback>
	            </View>
	          </TouchableWithoutFeedback>
	        </Modal>
	      )}
    </>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
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
    menuOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    menuContent: {
      width: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      paddingVertical: 8,
    },
    menuHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
      marginBottom: 4,
    },
    menuHeaderText: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.text,
    },
    closeButton: {
      paddingHorizontal: 4,
      paddingVertical: 4,
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
    },
    menuItemText: {
      marginLeft: 8,
      fontSize: 14,
      color: theme.text,
    },
    pinButton: {
      paddingHorizontal: 4,
      paddingVertical: 4,
    },
  });

export default MessageActionsBar;
