import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useTheme, type Theme } from '../theme';

export interface AgentSwitchModalProps {
  visible: boolean;
  loading: boolean;
  agents: string[];
  selectedAgentId: string | null;
  currentAgentId?: string | null;
  showCurrentLabel?: boolean;
  onRequestClose: () => void;
  onSelectAgent: (agentId: string) => void;
}

const AgentSwitchModal: React.FC<AgentSwitchModalProps> = ({
  visible,
  loading,
  agents,
  selectedAgentId,
  currentAgentId,
  showCurrentLabel,
  onRequestClose,
  onSelectAgent,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  if (!visible) {
    return null;
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Switch agent</Text>
          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={theme.primary} />
              <Text style={styles.loadingText}>Loading agents...</Text>
            </View>
          )}
          {!loading && agents.length === 0 && (
            <Text style={styles.modalSubtitle}>No agents available.</Text>
          )}
          {!loading && agents.length > 0 && (
            <>
              {showCurrentLabel && currentAgentId && (
                <Text style={styles.modalSubtitle}>Current agent: {currentAgentId}</Text>
              )}
              <ScrollView style={styles.agentList}>
                {agents.map((agentId) => {
                  const selected = selectedAgentId === agentId;
                  return (
                    <TouchableOpacity
                      key={agentId}
                      style={[styles.agentItem, selected && styles.agentItemSelected]}
                      onPress={() => onSelectAgent(agentId)}
                    >
                      <Text style={styles.agentItemText}>{agentId}</Text>
                      {selected && <Icon name="check" size={16} color="#34C759" />}
                    </TouchableOpacity>
                  );
                })}
              </ScrollView>
            </>
          )}
          <View style={styles.modalButtonsRow}>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton, styles.modalButton]}
              onPress={onRequestClose}
            >
              <Text style={styles.buttonTextSecondary}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modalOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    modalContent: {
      width: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      marginBottom: 12,
    },
    loadingContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    loadingText: {
      marginLeft: 8,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
    },
    modalButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      marginTop: 8,
    },
    modalButton: {
      minWidth: 90,
      alignItems: 'center',
      marginLeft: 8,
    },
    button: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    buttonTextSecondary: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    agentList: {
      maxHeight: 220,
      marginTop: 8,
      marginBottom: 8,
    },
    agentItem: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingVertical: 8,
      paddingHorizontal: 10,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      marginBottom: 6,
    },
    agentItemSelected: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    agentItemText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
    },
  });

export default AgentSwitchModal;
