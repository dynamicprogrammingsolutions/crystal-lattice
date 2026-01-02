import React, { useMemo, useState } from 'react';
import {
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import {
  ALL_SESSION_ACTIONS,
  SESSION_ACTIONS,
  type SessionActionDefinition,
  type SessionActionKey,
} from '../sessionActions';
import { useTheme, type Theme } from '../theme';

export interface SessionActionsBarProps {
  pinned: SessionActionKey[];
  onChangePinned: (pinned: SessionActionKey[]) => void;
  onAction: (action: SessionActionKey) => void;
  isActionDisabled?: (action: SessionActionKey) => boolean;
  extraActions?: SessionActionDefinition[];
}

const SessionActionsBar: React.FC<SessionActionsBarProps> = ({
  pinned,
  onChangePinned,
  onAction,
  isActionDisabled,
  extraActions,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [menuVisible, setMenuVisible] = useState(false);

  const allDefs: SessionActionDefinition[] = useMemo(() => {
    const extras = extraActions ?? [];
    return [...ALL_SESSION_ACTIONS, ...extras];
  }, [extraActions]);

  const defByKey: Record<string, SessionActionDefinition> = useMemo(() => {
    const map: Record<string, SessionActionDefinition> = {};
    allDefs.forEach((def) => {
      if (def && typeof def.key === 'string') {
        map[def.key] = def;
      }
    });
    return map;
  }, [allDefs]);

  const togglePinned = (key: SessionActionKey) => {
    if (pinned.includes(key)) {
      onChangePinned(pinned.filter((k) => k !== key));
    } else {
      onChangePinned([...pinned, key]);
    }
  };

  const renderIconButton = (key: SessionActionKey) => {
    const def = defByKey[key];
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
        <Icon name={def.iconName} size={18} color={theme.primary} />
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
          <Icon name="more-horizontal" size={20} color={theme.primary} />
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
	                    <Text style={styles.menuHeaderText}>Session actions</Text>
	                    <TouchableOpacity
	                      style={styles.closeButton}
	                      onPress={() => setMenuVisible(false)}
	                    >
	                      <Icon name="x" size={18} color="#8E8E93" />
	                    </TouchableOpacity>
	                  </View>
                  {allDefs.map((def) => {
	                    const pinnedHere = pinned.includes(def.key);
	                    return (
	                      <View key={def.key} style={styles.menuItem}>
	                        <TouchableOpacity
	                          style={styles.menuItemLeft}
	                          onPress={() => {
	                            setMenuVisible(false);
	                            onAction(def.key);
	                          }}
	                        >
	                          {renderIconButton(def.key)}
	                          <Text style={styles.menuItemText}>{def.label}</Text>
	                        </TouchableOpacity>
	                        <TouchableOpacity
	                          style={styles.pinButton}
	                          onPress={() => togglePinned(def.key)}
	                        >
	                          <Icon
	                            name="star"
	                            size={16}
	                            color={pinnedHere ? '#FFCC00' : '#C7C7CC'}
	                          />
	                        </TouchableOpacity>
	                      </View>
	                    );
	                  })}
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
    },
    iconButton: {
      paddingHorizontal: 8,
      paddingVertical: 4,
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

export default SessionActionsBar;
