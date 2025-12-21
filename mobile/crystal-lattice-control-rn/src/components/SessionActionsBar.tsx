import React, { useState } from 'react';
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
  type SessionActionKey,
} from '../sessionActions';

export interface SessionActionsBarProps {
  pinned: SessionActionKey[];
  onChangePinned: (pinned: SessionActionKey[]) => void;
  onAction: (action: SessionActionKey) => void;
  isActionDisabled?: (action: SessionActionKey) => boolean;
}

const SessionActionsBar: React.FC<SessionActionsBarProps> = ({
  pinned,
  onChangePinned,
  onAction,
  isActionDisabled,
}) => {
  const [menuVisible, setMenuVisible] = useState(false);

  const togglePinned = (key: SessionActionKey) => {
    if (pinned.includes(key)) {
      onChangePinned(pinned.filter((k) => k !== key));
    } else {
      onChangePinned([...pinned, key]);
    }
  };

  const renderIconButton = (key: SessionActionKey) => {
    const def = SESSION_ACTIONS[key];
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
        <Icon name={def.iconName} size={18} color="#007AFF" />
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
          <Icon name="more-horizontal" size={20} color="\#007AFF" />
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
	                  {ALL_SESSION_ACTIONS.map((def) => {
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

const styles = StyleSheet.create({
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
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuContent: {
    width: '80%',
    backgroundColor: '#FFFFFF',
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
    borderBottomColor: '#E5E5EA',
    marginBottom: 4,
  },
  menuHeaderText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000000',
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
    color: '#000000',
  },
  pinButton: {
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
});

export default SessionActionsBar;
