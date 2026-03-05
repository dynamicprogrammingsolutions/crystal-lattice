import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import type { AgentBackend, SessionPluginEntry } from '@crystal-lattice/frontend-sdk';
import { useSessionPluginsController } from '@crystal-lattice/frontend-sdk-react';
import { SessionPluginsList } from '@crystal-lattice/frontend-rn-components';

import { useTheme, type Theme } from '../theme';

export interface SessionPluginsModalProps {
  backend: AgentBackend | null;
  sessionId: string;
  visible: boolean;
  onRequestClose: () => void;
}

function isSessionPluginsSupported(backend: AgentBackend | null): boolean {
  try {
    return Boolean(backend?.getCapabilities()?.sessionPlugins);
  } catch {
    return false;
  }
}

const SessionPluginsModal: React.FC<SessionPluginsModalProps> = ({
  backend,
  sessionId,
  visible,
  onRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const controllerSessionId = visible ? sessionId : null;
  const { state, setEnabled, resetToDefaults } = useSessionPluginsController({
    backend,
    sessionId: controllerSessionId,
    enabled: visible,
  });

  const [optimisticEnabledById, setOptimisticEnabledById] = useState<Record<string, boolean>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [mutationCount, setMutationCount] = useState(0);

  useEffect(() => {
    if (!visible) {
      setOptimisticEnabledById({});
      setSuccessMessage(null);
      setMutationCount(0);
    }
  }, [visible]);

  useEffect(() => {
    setOptimisticEnabledById({});
  }, [state.lastLoadedAt]);

  useEffect(() => {
    if (!successMessage) {
      return;
    }
    const timer = setTimeout(() => setSuccessMessage(null), 1400);
    return () => clearTimeout(timer);
  }, [successMessage]);

  const supported = isSessionPluginsSupported(backend);

  const plugins = useMemo((): SessionPluginEntry[] => {
    const base = Array.isArray(state.plugins) ? state.plugins : [];
    if (!optimisticEnabledById || Object.keys(optimisticEnabledById).length === 0) {
      return base;
    }
    return base.map((plugin) => {
      const next = optimisticEnabledById[plugin.id];
      if (typeof next !== 'boolean') {
        return plugin;
      }
      return { ...plugin, enabled: next };
    });
  }, [optimisticEnabledById, state.plugins]);

  const handleToggle = useCallback(
    async (pluginId: string, nextEnabled: boolean) => {
      if (!backend) {
        Alert.alert('Error', 'No active connection');
        return;
      }
      if (!supported) {
        Alert.alert('Not supported', 'This server does not support session plugins.');
        return;
      }

      setSuccessMessage(null);
      setMutationCount((prev) => prev + 1);
      setOptimisticEnabledById((prev) => ({ ...prev, [pluginId]: nextEnabled }));
      try {
        await setEnabled(pluginId, nextEnabled);
        setSuccessMessage('Saved.');
      } catch {
        // Controller state captures errors.
      } finally {
        setMutationCount((prev) => Math.max(0, prev - 1));
        setOptimisticEnabledById((prev) => {
          const next = { ...prev };
          delete next[pluginId];
          return next;
        });
      }
    },
    [backend, setEnabled, supported],
  );

  const handleReset = useCallback(async () => {
    if (!backend) {
      Alert.alert('Error', 'No active connection');
      return;
    }
    if (!supported) {
      Alert.alert('Not supported', 'This server does not support session plugins.');
      return;
    }

    Alert.alert('Reset plugins', 'Reset session plugins to defaults?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Reset',
        style: 'destructive',
        onPress: () => {
          setSuccessMessage(null);
          setMutationCount((prev) => prev + 1);
          resetToDefaults()
            .then(() => {
              setSuccessMessage('Reset to defaults.');
            })
            .catch(() => {
              // Errors are captured in controller state.
            })
            .finally(() => {
              setMutationCount((prev) => Math.max(0, prev - 1));
            });
        },
      },
    ]);
  }, [backend, resetToDefaults, supported]);

  if (!visible) {
    return null;
  }

  const error = !backend
    ? 'No active connection'
    : !supported
      ? 'Session plugins are not supported by this server.'
      : state.error;

  const showSpinner = (state.loading || mutationCount > 0) && !error;
  const statusText = error || successMessage;
  const statusTone = error ? 'error' : successMessage ? 'success' : showSpinner ? 'busy' : 'idle';

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <View style={styles.modalOverlay}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onRequestClose} />
        <View style={styles.modalContent}>
          <View style={styles.headerRow}>
            <Text style={styles.modalTitle}>Plugins</Text>
            <TouchableOpacity style={styles.closeButton} onPress={onRequestClose}>
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.modalSubtitle}>
            Enable/disable plugins for this session. “Inactive” means it can’t run due to the current config.
          </Text>

          <View style={styles.statusLine}>
            {showSpinner ? <ActivityIndicator size="small" color={theme.primary} /> : null}
            {statusText ? (
              <Text
                style={[
                  styles.statusText,
                  statusTone === 'error'
                    ? styles.statusTextError
                    : statusTone === 'success'
                      ? styles.statusTextSuccess
                      : null,
                ]}
                numberOfLines={1}
              >
                {statusText}
              </Text>
            ) : null}
          </View>

          {!backend || !supported ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>{error}</Text>
            </View>
          ) : (
            <View style={styles.body}>
              <ScrollView
                style={styles.scroll}
                contentContainerStyle={styles.scrollContent}
                keyboardShouldPersistTaps="handled"
              >
                <SessionPluginsList
                  plugins={plugins}
                  onToggle={handleToggle}
                  onReset={handleReset}
                />
              </ScrollView>
            </View>
          )}
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
      width: '90%',
      maxHeight: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: theme.text,
    },
    closeButton: {
      paddingHorizontal: 8,
      paddingVertical: 6,
    },
    closeButtonText: {
      color: theme.primary,
      fontSize: 14,
      fontWeight: '600',
    },
    modalSubtitle: {
      marginTop: 6,
      marginBottom: 10,
      fontSize: 12,
      color: theme.textSecondary,
    },
    statusLine: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      minHeight: 22,
      marginBottom: 10,
    },
    statusText: {
      color: theme.textSecondary,
      fontSize: 13,
      flexShrink: 1,
    },
    statusTextError: {
      color: theme.danger,
      fontWeight: '600',
    },
    statusTextSuccess: {
      color: theme.success,
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
      paddingBottom: 6,
    },
    emptyState: {
      paddingVertical: 8,
    },
    emptyStateText: {
      fontSize: 13,
      color: theme.textSecondary,
    },
  });

export default SessionPluginsModal;
