import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  useServerSettingsController,
} from '@crystal-lattice/frontend-sdk-react';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme, type Theme } from '../theme';

export interface ServerSettingsModalProps {
  backend: AgentBackend | null;
  cacheKey?: string;
  visible: boolean;
  onRequestClose: () => void;
}

function normalizeOptions(raw: any): { value: string; label: string }[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((opt) => {
      if (typeof opt === 'string') {
        return { value: opt, label: opt };
      }
      if (opt && typeof opt === 'object') {
        const value = typeof opt.value === 'string' ? opt.value : String(opt.value ?? '');
        const label = typeof opt.label === 'string' ? opt.label : value;
        return { value, label };
      }
      return null;
    })
    .filter((v) => v !== null) as { value: string; label: string }[];
}

const ServerSettingsModal: React.FC<ServerSettingsModalProps> = ({
  backend,
  cacheKey = 'default',
  visible,
  onRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});

  const { controller, state } = useServerSettingsController({
    backend,
    cacheKey,
    enabled: visible,
  });

  const schemaByKey = useMemo(() => buildConfigSchemaByKey([]), []);
  const items = useMemo(
    () =>
      buildSessionSettingItems({
        elements: state?.elements || [],
        overrides: state?.settings || {},
        baseConfig: state?.baseConfig || {},
        schemaByKey,
      }),
    [schemaByKey, state?.baseConfig, state?.elements, state?.settings],
  );
  const savingKeySet = useMemo(() => new Set(state?.savingKeys || []), [state?.savingKeys]);

  useEffect(() => {
    if (!visible) {
      setPendingTextByKey({});
    }
  }, [visible]);

  const handlePatch = async (key: string, value: any) => {
    if (!controller) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    try {
      await controller.patchSetting(key, value);
    } catch {
      // Controller state captures errors.
    }
  };

  const handleDelete = async (key: string) => {
    if (!controller) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    setPendingTextByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    try {
      await controller.deleteSetting(key);
    } catch {
      // Controller state captures errors.
    }
  };

  const handleSaveText = async (key: string, fallback: unknown) => {
    const value =
      pendingTextByKey[key] ??
      (fallback !== undefined && fallback !== null ? String(fallback) : '');
    await handlePatch(key, value);
  };

  if (!visible) {
    return null;
  }

  const renderItem = (item: (typeof items)[number]) => {
    const isSaving = savingKeySet.has(item.key);
    const showDelete = item.hasOverride;
    const description = item.description ? (
      <Text style={styles.description}>{item.description}</Text>
    ) : null;

    if (item.type === 'checkbox') {
      return (
        <View key={item.key} style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <Text style={styles.itemLabel}>{item.label}</Text>
            {description}
          </View>
          {showDelete ? (
            <TouchableOpacity
              accessibilityLabel={`Reset ${item.label}`}
              style={styles.iconButton}
              onPress={() => handleDelete(item.key)}
              disabled={item.disabled}
            >
              <Icon name="trash-2" size={16} color={theme.danger} />
            </TouchableOpacity>
          ) : null}
          <Switch
            value={Boolean(item.effectiveValue ?? false)}
            disabled={item.disabled || isSaving}
            onValueChange={(next) => handlePatch(item.key, next)}
          />
        </View>
      );
    }

    if (item.type === 'select') {
      const options = normalizeOptions((item.element as any).options);
      const selected =
        typeof item.effectiveValue === 'string'
          ? item.effectiveValue
          : String(item.effectiveValue ?? '');
      return (
        <View key={item.key} style={styles.itemBlock}>
          <View style={styles.itemHeaderRow}>
            <Text style={styles.itemLabel}>{item.label}</Text>
            {showDelete ? (
              <TouchableOpacity
                accessibilityLabel={`Reset ${item.label}`}
                style={styles.iconButton}
                onPress={() => handleDelete(item.key)}
                disabled={item.disabled}
              >
                <Icon name="trash-2" size={16} color={theme.danger} />
              </TouchableOpacity>
            ) : null}
          </View>
          {description}
          <View style={styles.chipsRow}>
            {options.map((option) => {
              const active = option.value === selected;
              return (
                <TouchableOpacity
                  key={option.value}
                  style={[styles.chip, active && styles.chipSelected]}
                  onPress={() => handlePatch(item.key, option.value)}
                  disabled={item.disabled || isSaving}
                >
                  <Text style={active ? styles.chipTextSelected : styles.chipText}>
                    {option.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      );
    }

    const hasPending = Object.prototype.hasOwnProperty.call(pendingTextByKey, item.key);
    const textValue =
      (hasPending ? pendingTextByKey[item.key] : undefined) ??
      (item.effectiveValue !== undefined && item.effectiveValue !== null
        ? String(item.effectiveValue)
        : '');

    return (
      <View key={item.key} style={styles.itemBlock}>
        <View style={styles.itemHeaderRow}>
          <Text style={styles.itemLabel}>{item.label}</Text>
          {showDelete ? (
            <TouchableOpacity
              accessibilityLabel={`Reset ${item.label}`}
              style={styles.iconButton}
              onPress={() => handleDelete(item.key)}
              disabled={item.disabled}
            >
              <Icon name="trash-2" size={16} color={theme.danger} />
            </TouchableOpacity>
          ) : null}
        </View>
        {description}
        <View style={styles.textRow}>
          <TextInput
            style={styles.textInput}
            value={textValue}
            editable={!item.disabled && !isSaving}
            onChangeText={(text) =>
              setPendingTextByKey((prev) => ({ ...prev, [item.key]: text }))
            }
            placeholder="Enter value"
            placeholderTextColor={theme.textSecondary}
          />
          <TouchableOpacity
            style={styles.saveButton}
            onPress={() => handleSaveText(item.key, item.effectiveValue)}
            disabled={item.disabled || isSaving}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color={theme.textOnPrimary} />
            ) : (
              <Text style={styles.saveButtonText}>Save</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onRequestClose}
    >
      <View style={styles.overlay}>
        <View style={styles.content}>
          <View style={styles.headerRow}>
            <Text style={styles.title}>Server settings</Text>
            <TouchableOpacity
              accessibilityLabel="Close server settings"
              style={styles.closeButton}
              onPress={onRequestClose}
            >
              <Icon name="x" size={20} color={theme.text} />
            </TouchableOpacity>
          </View>

          {state?.statusMessage ? (
            <Text
              style={[
                styles.statusText,
                state.statusTone === 'error' && styles.statusError,
              ]}
            >
              {state.statusMessage}
            </Text>
          ) : null}

          <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
            {state?.loading ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator size="small" color={theme.primary} />
                <Text style={styles.loadingText}>Loading settings...</Text>
              </View>
            ) : null}
            {!state?.loading && items.length === 0 ? (
              <Text style={styles.emptyText}>No server settings available.</Text>
            ) : (
              items.map(renderItem)
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      flex: 1,
      backgroundColor: 'rgba(0,0,0,0.35)',
      justifyContent: 'flex-end',
    },
    content: {
      maxHeight: '86%',
      backgroundColor: theme.background,
      borderTopLeftRadius: 8,
      borderTopRightRadius: 8,
      padding: 16,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 12,
    },
    title: {
      fontSize: 18,
      fontWeight: '700',
      color: theme.text,
    },
    closeButton: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
    },
    scroll: {
      flexGrow: 0,
    },
    scrollContent: {
      paddingBottom: 16,
    },
    statusText: {
      marginBottom: 10,
      color: theme.textSecondary,
      fontSize: 13,
    },
    statusError: {
      color: theme.danger,
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 12,
    },
    loadingText: {
      marginLeft: 8,
      color: theme.textSecondary,
    },
    emptyText: {
      color: theme.textSecondary,
      fontStyle: 'italic',
      paddingVertical: 12,
    },
    itemBlock: {
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: theme.border,
    },
    itemRow: {
      minHeight: 64,
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: theme.border,
    },
    itemHeaderRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 6,
    },
    itemTextColumn: {
      flex: 1,
      paddingRight: 12,
    },
    itemLabel: {
      fontSize: 15,
      fontWeight: '600',
      color: theme.text,
    },
    description: {
      color: theme.textSecondary,
      fontSize: 13,
      marginTop: 4,
    },
    iconButton: {
      width: 36,
      height: 36,
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: 4,
    },
    chipsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
      marginTop: 4,
    },
    chip: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      backgroundColor: theme.surface,
    },
    chipSelected: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    chipText: {
      color: theme.text,
      fontWeight: '600',
    },
    chipTextSelected: {
      color: theme.primary,
      fontWeight: '700',
    },
    textRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: 4,
    },
    textInput: {
      flex: 1,
      minHeight: 40,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      color: theme.text,
      backgroundColor: theme.surface,
    },
    saveButton: {
      minWidth: 72,
      minHeight: 40,
      alignItems: 'center',
      justifyContent: 'center',
      marginLeft: 8,
      borderRadius: 8,
      backgroundColor: theme.primary,
    },
    saveButtonText: {
      color: theme.textOnPrimary,
      fontWeight: '700',
    },
  });

export default ServerSettingsModal;